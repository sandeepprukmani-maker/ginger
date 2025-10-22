from playwright.sync_api import sync_playwright, expect
import re


def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 1. Open the login page
        page.goto("https://practicetestautomation.com/practice-test-login/")

        # 2. Type username and password
        page.fill("input#username", "student")
        page.fill("input#password", "Password123")

        # 3. Click Submit button
        page.click("button#submit")

        # 4. Verify URL contains expected path
        expect(page).to_have_url(re.compile(r"practicetestautomation\.com/logged-in-successfully/"))

        # 5. Verify the page contains expected text
        expect(page.locator("body")).to_contain_text("Congratulations")
        # or alternatively
        # expect(page.locator("body")).to_contain_text("successfully logged in")

        # 6. Verify Log out button is displayed
        expect(page.locator("a[href='/practice-test-login/']")).to_be_visible()

        browser.close()


if __name__ == "__main__":
    test_login()
