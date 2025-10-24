# Playwright Code Generation from Browser-Use

## Overview

This feature automatically converts browser-use AI automation into clean, maintainable Playwright Python code. This is incredibly useful for:

- **Creating Test Scripts**: Convert one-off automation into regression tests
- **Documentation**: See exactly what the AI did in standard Playwright code
- **Code Review**: Make AI automation reviewable and maintainable
- **Hybrid Approach**: Use AI to explore, then convert to deterministic code
- **Learning**: Understand how to write Playwright code by seeing examples

## How It Works

```
┌─────────────────┐
│  Browser-Use    │  AI performs automation
│  Automation     │  using natural language
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent History   │  Records all actions:
│  (Steps Taken)  │  - Navigate to URL
└────────┬────────┘  - Click button
         │           - Fill form
         ▼           - etc.
┌─────────────────┐
│  Playwright     │  Converts to clean
│ Code Generator  │  Playwright code
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Python Script  │  Ready-to-run
│  (.py file)     │  Playwright automation
└─────────────────┘
```

## Quick Start

### Option 1: Automatic Generation (Via API)

When you run browser-use automation through the API, Playwright code is automatically generated:

```python
import requests

response = requests.post('http://localhost:5000/api/automation/execute', 
    headers={'X-API-Key': 'your-key'},
    json={
        'instruction': 'Go to Google and search for Playwright',
        'engine': 'browser_use'
    }
)

result = response.json()

# Access the generated Playwright code
playwright_code = result.get('playwright_code')

if playwright_code:
    # Save to file
    with open('generated_script.py', 'w') as f:
        f.write(playwright_code)
    print("✅ Playwright script saved!")
```

### Option 2: Programmatic Generation

```python
import asyncio
from browser_use import Agent
from browser_use.llm import ChatOpenAI
from browser_use_codebase.playwright_code_generator import generate_playwright_code_from_history

async def main():
    # Run browser automation
    agent = Agent(
        task="Search for Python tutorials on YouTube",
        llm=ChatOpenAI(model="gpt-4o-mini")
    )
    
    history = await agent.run()
    
    # Generate Playwright code
    playwright_code = generate_playwright_code_from_history(
        history,
        task_description="YouTube Python tutorial search",
        output_file="youtube_search.py"
    )
    
    print(playwright_code)

asyncio.run(main())
```

### Option 3: Using the Demo Script

```bash
python examples/generate_playwright_code_demo.py
```

## Generated Code Structure

The generated Playwright code includes:

### 1. **Complete Setup**
```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        # ... automation steps
        await browser.close()
```

### 2. **Extracted Locators** (Optional)
```python
# Locators extracted from automation
SEARCH_BOX = r"input[name='q']"  # fill('Playwright')
SEARCH_BUTTON = r"button[type='submit']"  # click()
```

### 3. **Clean Action Steps**
```python
# Step 1: Navigate to Google
await page.goto("https://www.google.com")

# Step 2: Fill search query
await page.locator(SEARCH_BOX).fill("Playwright")

# Step 3: Submit search
await page.locator(SEARCH_BUTTON).click()
```

### 4. **Proper Cleanup**
```python
# Pause to review results
await page.wait_for_timeout(3000)

await browser.close()
```

## API Reference

### PlaywrightCodeGenerator Class

```python
from browser_use_codebase.playwright_code_generator import PlaywrightCodeGenerator

generator = PlaywrightCodeGenerator(
    history=agent_history,
    task_description="What the automation does"
)

# Generate code
code = generator.generate_python_code(
    use_locators=True,        # Extract selectors as constants
    include_comments=True,     # Add explanatory comments
    async_style=True          # Use async/await (recommended)
)

# Save to file
generator.save_to_file("my_script.py")
```

### Convenience Function

```python
from browser_use_codebase.playwright_code_generator import generate_playwright_code_from_history

code = generate_playwright_code_from_history(
    history,
    task_description="My automation task",
    output_file="output.py"  # Optional: auto-save
)
```

## Supported Actions

The generator converts these browser-use actions to Playwright:

| Browser-Use Action | Playwright Code |
|-------------------|-----------------|
| Navigate to URL | `await page.goto(url)` |
| Click element | `await page.locator(selector).click()` |
| Fill text input | `await page.locator(selector).fill(text)` |
| Wait | `await page.wait_for_timeout(ms)` |
| Generic actions | Converted to comments for manual review |

## Configuration Options

### use_locators (bool)
Extract repeated selectors into named constants:

```python
# use_locators=True
SEARCH_BOX = r"input[name='q']"
await page.locator(SEARCH_BOX).fill("query")

# use_locators=False
await page.locator("input[name='q']").fill("query")
```

**Recommendation**: Use `True` for maintainability

### include_comments (bool)
Add explanatory comments:

```python
# include_comments=True
# Step 1: Navigate to homepage
await page.goto("https://example.com")

# include_comments=False
await page.goto("https://example.com")
```

**Recommendation**: Use `True` for clarity

### async_style (bool)
Use async/await or sync API:

```python
# async_style=True (recommended)
async def main():
    async with async_playwright() as p:
        await page.goto(url)

# async_style=False
def main():
    with sync_playwright() as p:
        page.goto(url)
```

**Recommendation**: Use `True` (async is more powerful)

## Example Use Cases

### 1. Create Regression Tests

```python
# Run AI automation once
history = await agent.run("Login to dashboard and verify user count")

# Generate test
code = generate_playwright_code_from_history(
    history,
    task_description="Dashboard login test",
    output_file="tests/test_dashboard_login.py"
)

# Now you have a repeatable test!
```

### 2. Document Complex Workflows

```python
# AI explores a complex workflow
history = await agent.run("Complete checkout process with test payment")

# Generate documentation
code = generate_playwright_code_from_history(
    history,
    task_description="Checkout process - detailed steps",
    output_file="docs/checkout_workflow.py"
)
```

### 3. Learn Playwright

```python
# Watch AI solve a problem
history = await agent.run("Fill out the contact form and submit")

# See how it's done in Playwright
code = generate_playwright_code_from_history(history)
print(code)  # Study the generated code
```

### 4. Hybrid AI + Deterministic Approach

```python
# Phase 1: Use AI to discover the workflow
ai_history = await agent.run("Find and download the monthly report")

# Phase 2: Convert to deterministic Playwright code
reliable_code = generate_playwright_code_from_history(
    ai_history,
    output_file="monthly_report_download.py"
)

# Phase 3: Use Playwright code in production (faster, cheaper, predictable)
```

## Running Generated Scripts

### Prerequisites

```bash
# Install Playwright
pip install playwright

# Install browser binaries
playwright install chromium
```

### Execute

```bash
python generated_script.py
```

## Limitations

### What Gets Converted Well
- ✅ Navigation (goto)
- ✅ Clicks
- ✅ Text input (fill)
- ✅ Basic waits
- ✅ Simple selectors

### What Needs Manual Review
- ⚠️ Complex AI reasoning steps
- ⚠️ Dynamic selectors
- ⚠️ Conditional logic
- ⚠️ Data extraction
- ⚠️ File uploads/downloads

**Tip**: Check generated code for `# Action:` comments - these may need manual conversion.

## Best Practices

### 1. Review Generated Code

Always review before running in production:
- Check selectors are specific enough
- Verify waits are appropriate
- Add error handling if needed

### 2. Use Descriptive Task Descriptions

```python
# ✅ Good
generate_playwright_code_from_history(
    history,
    task_description="Login to admin panel and verify dashboard loads"
)

# ❌ Poor
generate_playwright_code_from_history(
    history,
    task_description="Do stuff"
)
```

### 3. Combine with Manual Playwright Code

Generated code is a starting point:

```python
# Generated code provides the structure
await page.goto("https://example.com")
await page.locator(LOGIN_BUTTON).click()

# Add your enhancements
await page.wait_for_load_state('networkidle')
screenshot = await page.screenshot()
assert page.url == expected_url
```

### 4. Version Control

Commit generated scripts to track automation evolution:
```bash
git add automation_scripts/
git commit -m "Add Playwright script for user signup flow"
```

## Troubleshooting

### "No actions found in history"

The AI may have failed to complete the task. Check:
```python
if history.is_done():
    code = generate_playwright_code_from_history(history)
else:
    print("Task incomplete, review history manually")
```

### "Selectors not working"

Browser-use may use dynamic selectors. Options:
1. Use more specific selectors manually
2. Use Playwright codegen to find better selectors
3. Add `data-testid` attributes to your app

### "Generated code has comments instead of actions"

Some AI actions don't map cleanly to Playwright. Review the comments and implement manually.

## Integration with CI/CD

```yaml
# .github/workflows/test.yml
name: Test
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install playwright
      - run: playwright install chromium
      - run: python generated_test.py
```

## Future Enhancements

Planned features:
- [ ] TypeScript code generation
- [ ] Support for assertions
- [ ] Data-driven test generation
- [ ] Mobile/tablet viewport support
- [ ] Network request mocking
- [ ] Screenshot comparison

## References

- [Playwright Python Documentation](https://playwright.dev/python/)
- [Browser-Use Library](https://github.com/browser-use/browser-use)
- [Playwright Best Practices](https://playwright.dev/python/docs/best-practices)
