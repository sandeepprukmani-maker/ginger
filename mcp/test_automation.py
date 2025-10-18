import asyncio
from src.automation import BrowserEngine, TaskExecutor
from src.automation.config import BrowserConfig, AutomationConfig
from src.automation.logger import get_logger

logger = get_logger()


async def test_basic_automation():
    logger.info("Testing basic browser automation framework")
    
    browser_config = BrowserConfig(
        headless=True,
        timeout=30000,
        screenshot_on_error=True
    )
    
    automation_config = AutomationConfig(
        max_retries=3,
        log_level="INFO"
    )
    
    browser = BrowserEngine(browser_config, automation_config)
    executor = TaskExecutor(browser)
    
    try:
        logger.info("Starting browser...")
        await browser.start()
        logger.success("Browser started successfully!")
        
        logger.info("Navigating to Python.org...")
        await browser.navigate("https://www.python.org")
        await browser.wait_for_load()
        logger.success("Navigation successful!")
        
        logger.info("Extracting page title...")
        title = await browser.get_text("h1")
        logger.success(f"Page title: {title}")
        
        logger.info("Taking screenshot...")
        screenshot_path = await browser.screenshot("test_python_org")
        logger.success(f"Screenshot saved to: {screenshot_path}")
        
        logger.info("\n" + "="*50)
        logger.success("✅ All tests passed! Framework is working correctly.")
        logger.info("="*50 + "\n")
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False
    finally:
        logger.info("Stopping browser...")
        await browser.stop()
        logger.success("Browser stopped successfully!")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_basic_automation())
    exit(0 if success else 1)
