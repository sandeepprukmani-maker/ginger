from playwright.async_api import async_playwright, Page, Browser, Locator
from typing import Optional, List
import asyncio


async def automated_task():
    """Generated Playwright automation code with self-healing support"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Step 1: goto
            await page.goto("https://google.com")
            await page.wait_for_load_state('networkidle')

            # Step 2: fill
            # Text: doge
            element = await self_healing_locator(
                page,
                primary=page.get_by_text("doge"),
                fallbacks=[
                    'page.locator("text=\\"doge\\"")',
                    'page.locator("//*[contains(text(), \\"doge\\")]")'
                ]

            )
            await element.fill("doge")

            # Step 3: click
            # Unable to determine locator for click action

            print("✅ Task completed successfully!")

        except Exception as e:
            print(f"❌ Error during automation: {e}")
            raise
        finally:
            await browser.close()


async def self_healing_locator(
    page: Page,
    primary: str,
    fallbacks: Optional[List[str]] = None
) -> Locator:
    """Try primary locator, fall back to alternatives if it fails"""
    fallbacks = fallbacks or []
    
    # Try primary locator
    try:
        locator = eval(primary)
        await locator.wait_for(timeout=5000)
        return locator
    except Exception as e:
        print(f"⚠️  Primary locator failed: {primary}")
    
    # Try fallback locators
    for fallback in fallbacks:
        try:
            locator = eval(fallback)
            await locator.wait_for(timeout=5000)
            print(f"✓ Fallback locator succeeded: {fallback}")
            return locator
        except Exception:
            continue
    
    raise Exception(f"All locators failed for: {primary}")


if __name__ == "__main__":
    asyncio.run(automated_task())