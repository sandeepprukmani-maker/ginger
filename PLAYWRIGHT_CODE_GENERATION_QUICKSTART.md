# Playwright Code Generation - Quick Start Guide

## What Is This?

This feature automatically converts browser-use AI automation into clean, ready-to-run Playwright Python code. Think of it as "AI writes the automation, you get the code."

## Why Use It?

- 🔄 **Turn AI exploration into production code** - Use AI once, run code forever
- 💰 **Save money** - AI automation is expensive, Playwright code is cheap
- 📝 **Get maintainable tests** - Code is reviewable, versionable, and debuggable
- 📚 **Learn Playwright** - See how AI solves problems in standard Playwright syntax
- ⚡ **Faster execution** - Playwright code runs faster than AI decision-making

## How To Use It

### Method 1: API (Automatic - Works with ALL Engines)

```python
import requests

# Works with ANY engine: 'browser_use', 'browser_use_optimized', 'playwright_mcp', or 'hybrid'
response = requests.post('http://localhost:5000/api/automation/execute',
    headers={'X-API-Key': 'your-key'},
    json={
        'instruction': 'Go to Google and search for Playwright',
        'engine': 'browser_use'  # or 'playwright_mcp' or 'hybrid'
    }
)

# Get Playwright code automatically
result = response.json()
playwright_code = result.get('playwright_code')

# Save it
with open('my_script.py', 'w') as f:
    f.write(playwright_code)
```

### Method 2: Run Demo

```bash
python examples/generate_playwright_code_demo.py
```

This will:
1. Run a browser automation task
2. Generate Playwright code
3. Save to `generated_playwright_script.py`
4. Show you the code

### Method 3: Programmatic

```python
from browser_use_codebase.playwright_code_generator import generate_playwright_code_from_history

# After running browser-use automation
history = await agent.run()

# Generate code
code = generate_playwright_code_from_history(
    history,
    output_file="automation.py"
)
```

## Example

**Input (Natural Language):**
```
"Go to Google, search for 'Python tutorials', and click the first result"
```

**Output (Playwright Code):**
```python
import asyncio
from playwright.async_api import async_playwright

# Locators extracted from automation
SEARCH_BOX = r"input[name='q']"
SEARCH_BUTTON = r"button[type='submit']"
FIRST_RESULT = r"div.g:first-child a"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Step 1: Navigate to Google
        await page.goto("https://www.google.com")
        
        # Step 2: Fill search query
        await page.locator(SEARCH_BOX).fill("Python tutorials")
        
        # Step 3: Submit search
        await page.locator(SEARCH_BUTTON).click()
        
        # Step 4: Click first result
        await page.locator(FIRST_RESULT).click()
        
        # Pause to review results
        await page.wait_for_timeout(3000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Running Generated Code

```bash
# Install Playwright
pip install playwright

# Install browsers
playwright install chromium

# Run your script
python automation.py
```

## Use Cases

### 1. Create Test Suite

```python
# Use AI to explore feature
history = await agent.run("Sign up with new user and verify welcome email")

# Get test code
test_code = generate_playwright_code_from_history(
    history,
    output_file="tests/test_signup.py"
)

# Now you have a regression test!
```

### 2. Document Workflows

```python
# Let AI document a complex workflow
history = await agent.run("Complete checkout with PayPal payment")

# Get documented code
docs_code = generate_playwright_code_from_history(
    history,
    output_file="docs/checkout_workflow.py"
)
```

### 3. Learn Playwright

```python
# Watch AI solve a problem
history = await agent.run("Fill out contact form and submit")

# Study how it's done
code = generate_playwright_code_from_history(history)
print(code)
```

## Important Notes

### ✅ What Converts Well
- Navigation (clicking links, typing URLs)
- Form filling
- Button clicks
- Basic waits

### ⚠️ May Need Review
- Complex AI reasoning
- Dynamic content
- Conditional flows
- Data extraction

**Always review generated code before using in production!**

## Full Documentation

See [docs/PLAYWRIGHT_CODE_GENERATION.md](docs/PLAYWRIGHT_CODE_GENERATION.md) for complete documentation.

## Quick Tips

1. **Use specific instructions** - "Click login button" is better than "login somehow"
2. **Review the code** - AI does its best, but you should verify selectors
3. **Commit to git** - Track your automation evolution
4. **Enhance manually** - Generated code is a starting point, add assertions and error handling

## Support

Questions? Check:
- [Full Documentation](docs/PLAYWRIGHT_CODE_GENERATION.md)
- [Example Scripts](examples/)
- [Playwright Docs](https://playwright.dev/python/)
