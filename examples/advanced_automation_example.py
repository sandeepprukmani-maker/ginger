import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation import BrowserEngine, TaskExecutor
from src.automation.config import BrowserConfig, AutomationConfig
from src.automation.task_executor import TaskType
from src.automation.logger import get_logger

logger = get_logger()


async def advanced_automation_demo(url: str):
    browser_config = BrowserConfig(
        headless=True,
        timeout=30000,
        screenshot_on_error=True,
        video_recording=False
    )
    
    automation_config = AutomationConfig(
        max_retries=3,
        log_level="INFO",
        save_session=False
    )
    
    browser = BrowserEngine(browser_config, automation_config)
    executor = TaskExecutor(browser)
    
    try:
        await browser.start()
        
        logger.info("Example 1: Basic navigation and data extraction")
        
        result = await executor.execute_task(
            TaskType.NAVIGATE,
            {"url": url}
        )
        logger.info(f"Navigation result: {result.success}")
        
        result = await executor.execute_task(
            TaskType.WAIT,
            {"type": "load"}
        )
        
        result = await executor.execute_task(
            TaskType.EXTRACT_TEXT,
            {"selector": "h1", "all": False}
        )
        logger.info(f"Page heading: {result.data}")
        
        result = await executor.execute_task(
            TaskType.EXTRACT_LINKS,
            {"selector": "a"}
        )
        logger.info(f"Found {len(result.data) if result.data else 0} links")
        
        result = await executor.execute_task(
            TaskType.SCREENSHOT,
            {"name": "example_page"}
        )
        logger.info(f"Screenshot saved: {result.data}")
        
        logger.info("\nExample 2: Scrolling and JavaScript execution")
        
        result = await executor.execute_task(
            TaskType.SCROLL,
            {"direction": "down", "amount": 500}
        )
        logger.info("Scrolled down 500px")
        
        result = await executor.execute_task(
            TaskType.EXECUTE_SCRIPT,
            {"script": "return document.title"}
        )
        logger.info(f"Page title from JS: {result.data}")
        
        result = await executor.execute_task(
            TaskType.EXECUTE_SCRIPT,
            {"script": "return document.querySelectorAll('p').length"}
        )
        logger.info(f"Number of paragraphs: {result.data}")
        
        logger.info("\nExample 3: Table scraping (if table exists)")
        
        try:
            table_data = await executor.scrape_table("table")
            logger.info(f"Scraped table with {len(table_data)} rows")
            for row in table_data[:3]:
                logger.info(f"Row: {row}")
        except Exception as e:
            logger.debug(f"No table found or error scraping: {e}")
        
        logger.success("Advanced automation examples completed successfully")
        
    except Exception as e:
        logger.exception(f"Error during automation: {e}")
    finally:
        await browser.stop()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python advanced_automation_example.py <url>")
        print("Example: python advanced_automation_example.py https://news.ycombinator.com")
        sys.exit(1)
    
    url = sys.argv[1]
    asyncio.run(advanced_automation_demo(url))
