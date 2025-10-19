from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("🌐 Navigating to GitHub...")
        page.goto("https://github.com/", wait_until="networkidle")

        # Wait until any "Try GitHub Copilot" link is visible
        page.wait_for_selector("a:has-text('Try GitHub Copilot')")

        # There are multiple "Try GitHub Copilot" links — click the first visible one
        print("⚡ Clicking 'Try GitHub Copilot' ...")
        copilot_links = page.locator("a:has-text('Try GitHub Copilot')")
        copilot_links.first.click()

        page.wait_for_load_state("networkidle")

        # Click "Try now"
        print("⚡ Clicking 'Try now' ...")
        try_now = page.locator("text=Try now")
        try_now.first.click()
        page.wait_for_load_state("networkidle")

        # Click "Continue with Google"
        print("⚡ Clicking 'Continue with Google' ...")
        continue_google = page.locator("text=Continue with Google")
        continue_google.first.click()

        # Optional: take screenshot
        page.screenshot(path="final_page.png")
        print("✅ Successfully reached the Google sign-in step.")


if __name__ == "__main__":
    run()
