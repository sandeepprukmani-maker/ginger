import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation import BrowserEngine, TaskExecutor
from src.automation.config import BrowserConfig, AutomationConfig
from src.automation.logger import get_logger

logger = get_logger()


async def scrape_website(url: str, selectors: dict):
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
        await browser.start()
        
        logger.info(f"Navigating to {url}")
        await browser.navigate(url)
        await browser.wait_for_load()
        
        extracted_data = {}
        
        for key, selector in selectors.items():
            logger.info(f"Extracting {key} using selector: {selector}")
            texts = await browser.get_all_text(selector)
            extracted_data[key] = texts
            logger.success(f"Found {len(texts)} {key}")
        
        logger.info("\n=== Extracted Data ===")
        print(json.dumps(extracted_data, indent=2))
        
        await browser.screenshot("scraped_page")
        
        return extracted_data
        
    except Exception as e:
        logger.exception(f"Error during scraping: {e}")
        return None
    finally:
        await browser.stop()


async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python web_scraping_example.py <url>")
        print("Example: python web_scraping_example.py https://news.ycombinator.com")
        sys.exit(1)
    
    url = sys.argv[1]
    
    selectors = {
        "headings": "h1, h2",
        "paragraphs": "p",
        "links": "a"
    }
    
    logger.info(f"Scraping {url} with selectors: {selectors}")
    data = await scrape_website(url, selectors)
    
    if data:
        with open("scraped_data.json", "w") as f:
            json.dump(data, f, indent=2)
        logger.success("Data saved to scraped_data.json")


if __name__ == "__main__":
    asyncio.run(main())
