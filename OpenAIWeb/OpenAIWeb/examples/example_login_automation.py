"""
Example: Login Automation Script

This example demonstrates how to use the AI Browser Automation CLI
to automate a login process on a website.

Usage:
    # Generate code for this automation:
    python main.py "go to example.com, click login, fill email with test@example.com, click submit" \
        --generate-code --output examples/generated_login.py

    # Execute with self-healing:
    python main.py --execute-code examples/generated_login.py --verbose
"""

async def automated_task(page, safe_locator):
    """
    This is an example of what generated code looks like.
    In practice, you would use --generate-code to create this automatically.
    """
    await page.goto("https://example.com")
    
    login_button = await safe_locator(
        page,
        [
            lambda: page.get_by_text("Login"),
            lambda: page.get_by_role("button", name="Login"),
            lambda: page.get_by_label("Login"),
        ],
        action_description="click login button"
    )
    await login_button.click()
    
    email_input = await safe_locator(
        page,
        [
            lambda: page.get_by_label("Email"),
            lambda: page.get_by_placeholder("Email"),
            lambda: page.locator("input[type='email']"),
        ],
        action_description="fill email field"
    )
    await email_input.fill("test@example.com")
    
    submit_button = await safe_locator(
        page,
        [
            lambda: page.get_by_text("Submit"),
            lambda: page.get_by_role("button", name="Submit"),
            lambda: page.locator("button[type='submit']"),
        ],
        action_description="click submit button"
    )
    await submit_button.click()
    
    await page.wait_for_timeout(2000)
    
    print("✅ Login automation completed!")
