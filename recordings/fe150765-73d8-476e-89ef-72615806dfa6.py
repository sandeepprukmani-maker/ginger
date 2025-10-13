import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.amazon.in/")
    page.get_by_text("Up to 80% off | Home, kitchen & moreKitchen essentialsHome decorFurnitureHome").click()
    page.get_by_text("Kitchen essentialsHome decorFurnitureHome improvement").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
