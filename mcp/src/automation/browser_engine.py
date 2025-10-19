import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json
from datetime import datetime

from .config import BrowserConfig, AutomationConfig
from .logger import get_logger
from .selectors import SmartSelector, SelectorOptions

logger = get_logger()


class BrowserEngine:
    
    def __init__(
        self,
        browser_config: Optional[BrowserConfig] = None,
        automation_config: Optional[AutomationConfig] = None
    ):
        self.browser_config = browser_config or BrowserConfig()
        self.automation_config = automation_config or AutomationConfig()
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self._setup_directories()
    
    def _setup_directories(self):
        for dir_path in [
            self.automation_config.screenshot_dir,
            self.automation_config.video_dir,
            self.automation_config.session_dir
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        logger.info(f"Starting browser engine with {self.browser_config.browser_type.value}")
        
        self.playwright = await async_playwright().start()
        
        browser_type = getattr(self.playwright, self.browser_config.browser_type.value)
        
        launch_options = {
            "headless": self.browser_config.headless,
            "slow_mo": self.browser_config.slow_mo,
        }
        
        if self.browser_config.proxy:
            launch_options["proxy"] = self.browser_config.proxy
        
        if self.browser_config.downloads_path:
            Path(self.browser_config.downloads_path).mkdir(parents=True, exist_ok=True)
        
        self.browser = await browser_type.launch(**launch_options)
        
        context_options = {
            "viewport": {
                "width": self.browser_config.viewport_width,
                "height": self.browser_config.viewport_height
            },
            "locale": self.browser_config.locale,
            "timezone_id": self.browser_config.timezone,
            "ignore_https_errors": self.browser_config.ignore_https_errors,
        }
        
        if self.browser_config.user_agent:
            context_options["user_agent"] = self.browser_config.user_agent
        
        if self.browser_config.video_recording:
            context_options["record_video_dir"] = self.automation_config.video_dir
        
        if self.automation_config.save_session:
            session_file = Path(self.automation_config.session_dir) / f"{self.automation_config.session_name}.json"
            if session_file.exists():
                with open(session_file, 'r') as f:
                    storage_state = json.load(f)
                    context_options["storage_state"] = storage_state
                    logger.info(f"Loaded session from {session_file}")
        
        self.context = await self.browser.new_context(**context_options)
        
        if self.browser_config.trace_recording:
            await self.context.tracing.start(screenshots=True, snapshots=True)
        
        self.page = await self.context.new_page()
        
        self.page.set_default_timeout(self.browser_config.timeout)
        
        logger.success("Browser engine started successfully")
    
    async def stop(self):
        logger.info("Stopping browser engine")
        
        if self.automation_config.save_session and self.context:
            session_file = Path(self.automation_config.session_dir) / f"{self.automation_config.session_name}.json"
            storage_state = await self.context.storage_state()
            with open(session_file, 'w') as f:
                json.dump(storage_state, f)
            logger.info(f"Saved session to {session_file}")
        
        if self.browser_config.trace_recording and self.context:
            trace_file = f"traces/trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            Path("traces").mkdir(parents=True, exist_ok=True)
            await self.context.tracing.stop(path=trace_file)
            logger.info(f"Saved trace to {trace_file}")
        
        if self.page:
            await self.page.close()
        
        if self.context:
            await self.context.close()
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        logger.success("Browser engine stopped successfully")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def navigate(self, url: str, wait_until: str = None) -> bool:
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        wait_until = wait_until or self.automation_config.wait_strategy
        
        try:
            logger.info(f"Navigating to {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=self.browser_config.timeout)
            logger.success(f"Successfully navigated to {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            if self.browser_config.screenshot_on_error:
                await self.screenshot(f"error_navigate_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            raise
    
    async def screenshot(self, name: str = None) -> str:
        if not self.page:
            raise RuntimeError("Browser not started")
        
        if name is None:
            name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        screenshot_path = Path(self.automation_config.screenshot_dir) / f"{name}.png"
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"Screenshot saved to {screenshot_path}")
        return str(screenshot_path)
    
    async def wait_for_selector(
        self,
        selector: str,
        timeout: Optional[int] = None,
        state: str = "visible"
    ) -> bool:
        if not self.page:
            raise RuntimeError("Browser not started")
        
        try:
            options = SelectorOptions(timeout=timeout or self.browser_config.timeout, state=state)
            element = await SmartSelector.find_element(self.page, selector, options)
            if element:
                await element.first.wait_for(state=state, timeout=timeout or self.browser_config.timeout)
                return True
        except Exception as e:
            logger.error(f"Wait for selector failed: {str(e)}")
        return False
    
    async def click(self, selector: str, **kwargs) -> bool:
        if not self.page:
            raise RuntimeError("Browser not started")
        
        return await SmartSelector.safe_click(self.page, selector, SelectorOptions(**kwargs))
    
    async def fill(self, selector: str, value: str, **kwargs) -> bool:
        if not self.page:
            raise RuntimeError("Browser not started")
        
        return await SmartSelector.safe_fill(self.page, selector, value, SelectorOptions(**kwargs))
    
    async def get_text(self, selector: str, **kwargs) -> Optional[str]:
        if not self.page:
            raise RuntimeError("Browser not started")
        
        return await SmartSelector.get_text(self.page, selector, SelectorOptions(**kwargs))
    
    async def get_attribute(self, selector: str, attribute: str, **kwargs) -> Optional[str]:
        if not self.page:
            raise RuntimeError("Browser not started")
        
        return await SmartSelector.get_attribute(self.page, selector, attribute, SelectorOptions(**kwargs))
    
    async def get_all_text(self, selector: str, **kwargs) -> List[str]:
        if not self.page:
            raise RuntimeError("Browser not started")
        
        elements = await SmartSelector.find_all(self.page, selector, SelectorOptions(**kwargs))
        texts = []
        for element in elements:
            text = await element.text_content()
            if text:
                texts.append(text.strip())
        return texts
    
    async def execute_script(self, script: str) -> Any:
        if not self.page:
            raise RuntimeError("Browser not started")
        
        return await self.page.evaluate(script)
    
    async def wait_for_load(self, timeout: Optional[int] = None):
        if not self.page:
            raise RuntimeError("Browser not started")
        
        await self.page.wait_for_load_state("networkidle", timeout=timeout or self.browser_config.timeout)
    
    async def new_page(self) -> Page:
        if not self.context:
            raise RuntimeError("Browser not started")
        
        page = await self.context.new_page()
        page.set_default_timeout(self.browser_config.timeout)
        return page
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        if not self.context:
            raise RuntimeError("Browser not started")
        
        return await self.context.cookies()
    
    async def set_cookies(self, cookies: List[Dict[str, Any]]):
        if not self.context:
            raise RuntimeError("Browser not started")
        
        await self.context.add_cookies(cookies)
        logger.info(f"Set {len(cookies)} cookies")
    
    async def clear_cookies(self):
        if not self.context:
            raise RuntimeError("Browser not started")
        
        await self.context.clear_cookies()
        logger.info("Cleared all cookies")
