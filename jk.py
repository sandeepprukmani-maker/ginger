from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # set to True for headless mode
        page = browser.new_page()

        # Step 1: Navigate to Google
        page.goto("https://www.google.com", wait_until="domcontentloaded")

        # Step 2: Accept cookies if prompted (for EU regions)
        try:
            consent_button = page.locator("button:has-text('Accept all')").first
            if consent_button.is_visible():
                consent_button.click()
        except:
            pass  # Ignore if the cookie prompt doesn't exist

        # Step 3: Locate search box and type query
        search_box = page.get_by_role("textbox").first  # works reliably across regions
        search_box.fill("Playwright MCP")

        # Step 4: Press Enter to search
        search_box.press("Enter")

        # Step 5: Wait for results to load
        page.wait_for_selector("h3")

        # Step 6: Print first few result titles
        results = page.locator("h3").all_text_contents()
        print("\nTop search results:\n--------------------")
        for title in results[:5]:
            print("-", title)

        print("\n✅ Search completed successfully!")

        # Optional: Keep browser open for review
        # input("Press Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    run()
