from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio
from dataclasses import dataclass

from .browser_engine import BrowserEngine
from .logger import get_logger

logger = get_logger()


class TaskType(Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_LINKS = "extract_links"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    SCROLL = "scroll"
    EXECUTE_SCRIPT = "execute_script"


@dataclass
class TaskResult:
    success: bool
    data: Any = None
    error: Optional[str] = None


class TaskExecutor:
    
    def __init__(self, browser_engine: BrowserEngine):
        self.browser = browser_engine
    
    async def execute_task(self, task_type: TaskType, params: Dict[str, Any]) -> TaskResult:
        try:
            if task_type == TaskType.NAVIGATE:
                return await self._navigate(params)
            elif task_type == TaskType.CLICK:
                return await self._click(params)
            elif task_type == TaskType.FILL:
                return await self._fill(params)
            elif task_type == TaskType.EXTRACT_TEXT:
                return await self._extract_text(params)
            elif task_type == TaskType.EXTRACT_LINKS:
                return await self._extract_links(params)
            elif task_type == TaskType.SCREENSHOT:
                return await self._screenshot(params)
            elif task_type == TaskType.WAIT:
                return await self._wait(params)
            elif task_type == TaskType.SCROLL:
                return await self._scroll(params)
            elif task_type == TaskType.EXECUTE_SCRIPT:
                return await self._execute_script(params)
            else:
                return TaskResult(success=False, error=f"Unknown task type: {task_type}")
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return TaskResult(success=False, error=str(e))
    
    async def _navigate(self, params: Dict[str, Any]) -> TaskResult:
        url = params.get("url")
        if not url:
            return TaskResult(success=False, error="URL is required")
        
        success = await self.browser.navigate(url, params.get("wait_until"))
        return TaskResult(success=success)
    
    async def _click(self, params: Dict[str, Any]) -> TaskResult:
        selector = params.get("selector")
        if not selector:
            return TaskResult(success=False, error="Selector is required")
        
        success = await self.browser.click(selector)
        return TaskResult(success=success)
    
    async def _fill(self, params: Dict[str, Any]) -> TaskResult:
        selector = params.get("selector")
        value = params.get("value")
        
        if not selector or value is None:
            return TaskResult(success=False, error="Selector and value are required")
        
        success = await self.browser.fill(selector, str(value))
        return TaskResult(success=success)
    
    async def _extract_text(self, params: Dict[str, Any]) -> TaskResult:
        selector = params.get("selector")
        if not selector:
            return TaskResult(success=False, error="Selector is required")
        
        all_elements = params.get("all", False)
        
        if all_elements:
            texts = await self.browser.get_all_text(selector)
            return TaskResult(success=True, data=texts)
        else:
            text = await self.browser.get_text(selector)
            return TaskResult(success=text is not None, data=text)
    
    async def _extract_links(self, params: Dict[str, Any]) -> TaskResult:
        selector = params.get("selector", "a")
        
        links = []
        elements = await self.browser.get_all_text(selector)
        
        for i, _ in enumerate(elements):
            href = await self.browser.get_attribute(f"{selector}:nth-of-type({i+1})", "href")
            text = await self.browser.get_text(f"{selector}:nth-of-type({i+1})")
            if href:
                links.append({"url": href, "text": text or ""})
        
        return TaskResult(success=True, data=links)
    
    async def _screenshot(self, params: Dict[str, Any]) -> TaskResult:
        name = params.get("name")
        path = await self.browser.screenshot(name)
        return TaskResult(success=True, data=path)
    
    async def _wait(self, params: Dict[str, Any]) -> TaskResult:
        wait_type = params.get("type", "time")
        
        if wait_type == "time":
            duration = params.get("duration", 1000)
            await asyncio.sleep(duration / 1000)
            return TaskResult(success=True)
        elif wait_type == "selector":
            selector = params.get("selector")
            if not selector:
                return TaskResult(success=False, error="Selector is required for selector wait")
            success = await self.browser.wait_for_selector(selector, params.get("timeout"))
            return TaskResult(success=success)
        elif wait_type == "load":
            await self.browser.wait_for_load(params.get("timeout"))
            return TaskResult(success=True)
        else:
            return TaskResult(success=False, error=f"Unknown wait type: {wait_type}")
    
    async def _scroll(self, params: Dict[str, Any]) -> TaskResult:
        direction = params.get("direction", "down")
        amount = params.get("amount", 500)
        
        script = f"window.scrollBy(0, {amount if direction == 'down' else -amount})"
        await self.browser.execute_script(script)
        
        return TaskResult(success=True)
    
    async def _execute_script(self, params: Dict[str, Any]) -> TaskResult:
        script = params.get("script")
        if not script:
            return TaskResult(success=False, error="Script is required")
        
        result = await self.browser.execute_script(script)
        return TaskResult(success=True, data=result)
    
    async def fill_form(self, form_data: Dict[str, str]) -> bool:
        logger.info("Filling form with provided data")
        
        for selector, value in form_data.items():
            success = await self.browser.fill(selector, value)
            if not success:
                logger.error(f"Failed to fill field: {selector}")
                return False
        
        logger.success("Form filled successfully")
        return True
    
    async def scrape_table(self, table_selector: str) -> List[Dict[str, Any]]:
        logger.info(f"Scraping table: {table_selector}")
        
        headers_script = f"""
        Array.from(document.querySelector('{table_selector}').querySelectorAll('th'))
            .map(th => th.textContent.trim())
        """
        headers = await self.browser.execute_script(headers_script)
        
        rows_script = f"""
        Array.from(document.querySelector('{table_selector}').querySelectorAll('tbody tr'))
            .map(tr => Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim()))
        """
        rows = await self.browser.execute_script(rows_script)
        
        table_data = []
        for row in rows:
            row_dict = dict(zip(headers, row))
            table_data.append(row_dict)
        
        logger.success(f"Scraped {len(table_data)} rows from table")
        return table_data
