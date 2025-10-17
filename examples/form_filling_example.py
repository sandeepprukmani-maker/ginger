import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.automation import BrowserEngine, TaskExecutor
from src.automation.config import BrowserConfig, AutomationConfig
from src.automation.logger import get_logger

logger = get_logger()


async def fill_and_submit_form(url: str, form_config_file: str = None):
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
        
        if form_config_file:
            with open(form_config_file, 'r') as f:
                config = json.load(f)
                form_data = config.get('form_data', {})
                submit_selector = config.get('submit_selector')
        else:
            logger.info("Interactive mode: Define form fields")
            form_data = {}
            
            print("\nEnter form fields (CSS selector = value)")
            print("Examples:")
            print("  input[name='email'] = user@example.com")
            print("  #username = myusername")
            print("  textarea[name='message'] = Hello World")
            print("\nPress Enter with empty selector to finish\n")
            
            while True:
                selector = input("CSS Selector (or press Enter to finish): ").strip()
                if not selector:
                    break
                
                value = input(f"Value for '{selector}': ").strip()
                form_data[selector] = value
            
            submit_selector = input("\nSubmit button CSS selector (or press Enter to skip): ").strip()
            if not submit_selector:
                submit_selector = None
        
        if not form_data:
            logger.warning("No form data provided")
            return
        
        logger.info("Filling form fields...")
        success = await executor.fill_form(form_data)
        
        if not success:
            logger.error("Failed to fill form")
            return
        
        await browser.screenshot("form_before_submit")
        logger.success("Form filled successfully")
        
        if submit_selector:
            logger.info(f"Clicking submit button: {submit_selector}")
            await browser.click(submit_selector)
            await browser.wait_for_load()
            await browser.screenshot("form_after_submit")
            logger.success("Form submitted successfully!")
        else:
            logger.info("No submit button specified - form filled but not submitted")
        
    except Exception as e:
        logger.exception(f"Error during form automation: {e}")
    finally:
        await browser.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Interactive mode: python form_filling_example.py <url>")
        print("  Config file mode: python form_filling_example.py <url> <config.json>")
        print("\nExample config.json:")
        print(json.dumps({
            "form_data": {
                "input[name='email']": "test@example.com",
                "input[name='password']": "password123"
            },
            "submit_selector": "button[type='submit']"
        }, indent=2))
        sys.exit(1)
    
    url = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    asyncio.run(fill_and_submit_form(url, config_file))
