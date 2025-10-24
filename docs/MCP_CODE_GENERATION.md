# Playwright MCP Code Generation

## Overview

Playwright MCP automation now automatically generates clean, reusable Playwright Python code from its tool-based automation steps. This bridges the gap between AI-driven exploration and deterministic, maintainable test scripts.

## How It Works

### MCP Tool Calls → Playwright Code

Playwright MCP uses tool-based automation where the AI makes explicit tool calls:

```
MCP Tool Calls                 →  Playwright Code
───────────────────────────────────────────────────
browser_navigate_to(url=...)   →  await page.goto(url)
browser_click(ref="e1")        →  await page.locator(selector).click()
browser_fill(ref="e2", text=…) →  await page.locator(selector).fill(text)
browser_snapshot()             →  await page.wait_for_timeout(1000)
browser_press(key="Enter")     →  await page.keyboard.press("Enter")
```

## Quick Start

### Via API (Automatic)

```python
import requests

response = requests.post('http://localhost:5000/api/automation/execute',
    headers={'X-API-Key': 'your-key'},
    json={
        'instruction': 'Search Google for Python tutorials',
        'engine': 'playwright_mcp'
    }
)

result = response.json()
playwright_code = result.get('playwright_code')

# Save and use
with open('google_search.py', 'w') as f:
    f.write(playwright_code)
```

### Programmatic

```python
import playwright_mcp_codebase

# Create engine
mcp_client, browser_agent = playwright_mcp_codebase.create_engine(headless=False)

# Run automation
result = browser_agent.execute_instruction("Search YouTube for tutorials")

# Get generated code
if 'playwright_code' in result:
    code = result['playwright_code']
    print(code)
```

### Demo Script

```bash
python examples/mcp_code_generation_demo.py
```

## Generated Code Structure

### Complete Script

```python
"""
Search Google for Python tutorials

Generated from Playwright MCP automation
To run: python script.py
"""

import asyncio
from playwright.async_api import async_playwright


# Locators extracted from MCP automation
SEARCH_BOX = r"input[name='q']"
SUBMIT_BUTTON = r"button[type='submit']"


async def main():
    """Main automation function"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Automation steps
        # Step 1: Navigate to https://www.google.com
        await page.goto("https://www.google.com")
        
        # Step 2: Fill 'Python tutorials' into input[name='q']
        await page.locator(SEARCH_BOX).fill("Python tutorials")
        
        # Step 3: Press key: Enter
        await page.keyboard.press("Enter")
        
        # Pause to review results
        await page.wait_for_timeout(3000)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
```

## MCP-Specific Features

### Element References

MCP uses element references (like `ref="e1"`) during automation. The code generator handles these:

```python
# MCP Step:
# browser_click(ref="e1")  # From page snapshot

# Generated Code:
# Click element by reference (convert to specific selector)
# Original ref: e1
# NOTE: You should replace this with an actual selector from the page
```

**Action Required**: Replace ref-based actions with actual selectors from your application.

### Tool Call Mapping

| MCP Tool | Generated Playwright |
|----------|---------------------|
| `browser_navigate_to` | `page.goto(url)` |
| `browser_click` | `page.locator(selector).click()` |
| `browser_fill` | `page.locator(selector).fill(text)` |
| `browser_snapshot` | `page.wait_for_timeout(1000)` (inspection pause) |
| `browser_press` | `page.keyboard.press(key)` |
| `browser_scroll` | Comment with implementation hint |

### Selector Extraction

When MCP provides explicit selectors (not just refs), they're extracted:

```python
# Extracted locators
INPUT_EMAIL = r"input[type='email']"
BUTTON_SUBMIT = r"button[type='submit']"

# Used in code
await page.locator(INPUT_EMAIL).fill(email)
await page.locator(BUTTON_SUBMIT).click()
```

## Comparison: Browser-Use vs MCP Code Generation

| Feature | Browser-Use | Playwright MCP |
|---------|-------------|----------------|
| Selector Quality | ✅ Excellent (AI-discovered) | ⚠️ Good (tool-specified) |
| Ref Handling | N/A | Requires manual conversion |
| Code Completeness | ✅ Ready to run | ⚠️ May need selector updates |
| Tool Mapping | N/A | ✅ Direct tool→code mapping |
| Best For | Exploration & discovery | Structured automation |

## Best Practices

### 1. Update Element References

MCP often uses element references that need conversion:

```python
# Generated (needs work):
# Click element by reference (convert to specific selector)
# Original ref: e1

# Updated (production-ready):
await page.locator("button[data-testid='submit']").click()
```

### 2. Add Stable Selectors to Your App

Help MCP generate better code by using stable attributes:

```html
<!-- Good: Stable selector -->
<button data-testid="login-submit">Login</button>

<!-- Better than: Dynamic selector -->
<button class="btn-abc123-xyz">Login</button>
```

### 3. Combine with Browser-Use

Use both engines strategically:

```python
# Phase 1: Exploration with Browser-Use
browser_use_result = execute_automation(
    instruction="Explore checkout flow",
    engine="browser_use"
)
# Get: Discovered selectors, workflow understanding

# Phase 2: Structured automation with MCP
mcp_result = execute_automation(
    instruction="Complete checkout with known selectors",
    engine="playwright_mcp"
)
# Get: Clean tool-based code
```

### 4. Review and Enhance

Always review generated code:

```python
# Generated code is your foundation
await page.goto(url)
await page.locator(selector).click()

# Enhance for production
await page.goto(url)
await page.wait_for_load_state('networkidle')
await page.locator(selector).wait_for(state='visible')
await page.locator(selector).click()
assert await page.locator(success_message).is_visible()
```

## Configuration Options

```python
from playwright_mcp_codebase.mcp_code_generator import MCPCodeGenerator

generator = MCPCodeGenerator(
    steps=result['steps'],
    task_description="My automation"
)

code = generator.generate_python_code(
    use_locators=True,        # Extract selectors as constants
    include_comments=True,     # Add step comments
    async_style=True          # Use async/await
)
```

## Limitations

### Current Limitations

1. **Element References**: MCP refs need manual conversion to selectors
2. **Complex Logic**: Conditional flows may need manual implementation
3. **Data Extraction**: Result parsing not automatically converted

### What Works Great

✅ Navigation  
✅ Form filling  
✅ Button clicks  
✅ Keyboard input  
✅ Basic page interactions  

### What Needs Manual Work

⚠️ Ref-based element targeting  
⚠️ Complex page state verification  
⚠️ Data extraction and assertions  
⚠️ Conditional logic  

## Future Enhancements

Planned improvements:

- [ ] Automatic ref-to-selector conversion using page snapshots
- [ ] Support for assertions and verifications
- [ ] Better handling of complex workflows
- [ ] Integration with test frameworks (pytest, etc.)
- [ ] TypeScript code generation

## Use Cases

### 1. Convert Exploratory Automation to Tests

```python
# Use MCP to explore
result = mcp_agent.execute_instruction("Test the signup flow")

# Get test code
test_code = result['playwright_code']

# Save as regression test
with open('tests/test_signup.py', 'w') as f:
    f.write(test_code)
```

### 2. Document Workflows

```python
# Automate complex workflow
result = mcp_agent.execute_instruction(
    "Complete multi-step checkout process"
)

# Get documented code
docs = result['playwright_code']
# Now you have executable documentation!
```

### 3. Learn Playwright

```python
# Watch how MCP solves problems
result = mcp_agent.execute_instruction("Fill out contact form")

# Study the generated Playwright code
print(result['playwright_code'])
```

## Troubleshooting

### "Element reference not found"

MCP uses refs like `e1`, `e2` from page snapshots. Update to actual selectors:

```python
# Before:
# Original ref: e1

# After:
await page.locator("button#submit").click()
```

### "Locators not working"

If generated selectors don't work:

1. Use Playwright Inspector: `playwright codegen`
2. Add `data-testid` attributes to your app
3. Use more robust selectors (roles, labels)

### "Code incomplete"

Some MCP tool calls don't map directly to Playwright:

```python
# Generated comment:
# Tool: browser_scroll - {"direction": "down"}

# Implement manually:
await page.evaluate("window.scrollBy(0, 500)")
```

## See Also

- [Main Code Generation Docs](PLAYWRIGHT_CODE_GENERATION.md)
- [Browser-Use Code Generation](PLAYWRIGHT_CODE_GENERATION.md#browser-use-vs-mcp)
- [Playwright Best Practices](https://playwright.dev/python/docs/best-practices)
