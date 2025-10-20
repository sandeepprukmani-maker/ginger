# Export Feature Guide

## Overview
The export feature allows you to convert AI-powered browser automation into reusable Playwright code and JSON data.

## How to Use

### 1. Execute an Instruction
Type any instruction in the web UI, for example:
- "Go to example.com"
- "Navigate to github.com and search for playwright"
- "Open google.com and search for 'AI automation'"

### 2. Click Export
After successful execution, the green "Export as Playwright" button appears. Click it to see two export formats:

---

## Export Format 1: Playwright Test Code

Generated `.spec.ts` file ready for Playwright test suites.

### Example Output:

```typescript
import { test, expect } from '@playwright/test';

test('Go to example.com', async ({ page }) => {
  await page.goto('https://example.com');
  // Browser will close automatically after test
});
```

### With Interactions:

```typescript
import { test, expect } from '@playwright/test';

test('Search on Google', async ({ page }) => {
  await page.goto('https://google.com');
  await page.locator('[role="textbox"][name="q"]').fill('AI automation');
  await page.locator('[role="button"][name="Google Search"]').click();
});
```

### Selector Extraction

The code generator attempts to extract selectors in this priority:

1. **Role + Name attributes**: `[role="button"][name="Submit"]`
2. **Text content**: `text='Click Here'`
3. **Fallback**: Comment with `[ref=...]` for manual replacement

---

## Export Format 2: JSON Data

Complete execution data including all steps, arguments, and results.

### Example JSON Structure:

```json
{
  "instruction": "Go to example.com",
  "timestamp": "2025-10-20T22:30:00.000000",
  "steps": [
    {
      "tool": "browser_navigate",
      "arguments": {
        "url": "https://example.com"
      },
      "success": true,
      "result": {
        "content": [
          {
            "type": "text",
            "text": "Navigated to https://example.com"
          }
        ],
        "snapshot": "page: Example Domain\nlink: 'More information...' [ref=e1]"
      }
    }
  ],
  "usage_notes": {
    "description": "Steps executed by AI with full context",
    "replay": "Can be used to replay automation programmatically",
    "selectors": "Check result.snapshot fields for element information"
  }
}
```

### JSON Fields Explained:

- **instruction**: Original natural language instruction
- **timestamp**: When the automation was executed
- **steps**: Array of all actions taken
  - **tool**: MCP tool used (browser_navigate, browser_click, browser_fill, etc.)
  - **arguments**: Parameters passed to the tool
  - **success**: Whether the step succeeded
  - **result**: Response from MCP including:
    - **content**: Action result message
    - **snapshot**: Page state in YAML format with element refs

---

## Using Exported Data

### Option 1: Direct Playwright Usage

1. Download the `.spec.ts` file
2. Add to your Playwright test suite
3. Run with: `npx playwright test`

```bash
# Save exported code as test.spec.ts
npx playwright test test.spec.ts
```

### Option 2: Programmatic Replay

Use the JSON export to replay steps programmatically:

```python
import json
from app.mcp_stdio_client import MCPStdioClient

# Load exported JSON
with open('automation-steps.json') as f:
    data = json.load(f)

# Replay steps
client = MCPStdioClient()
client.initialize()

for step in data['steps']:
    tool = step['tool']
    args = step['arguments']
    result = client.call_tool(tool, args)
    print(f"Executed {tool}: {result}")
```

### Option 3: Convert to Other Frameworks

The JSON data can be converted to other automation frameworks:

- **Selenium**: Convert locators to By.CSS_SELECTOR or By.XPATH
- **Puppeteer**: Use `page.goto()`, `page.click()`, `page.type()`
- **Cypress**: Convert to `cy.visit()`, `cy.get()`, `cy.click()`

---

## Understanding Locators

### What MCP Returns

MCP uses temporary references in snapshots like `[ref=e1]`, `[ref=e2]`. These work during AI session but need conversion for standalone scripts.

### What Gets Exported

The export feature analyzes the snapshot data and extracts:

1. **ARIA roles and names**: Most reliable for accessibility
   ```typescript
   page.locator('[role="button"][name="Submit"]')
   ```

2. **Text content**: Good for unique text elements
   ```typescript
   page.locator('text="Click Here"')
   ```

3. **Comments with refs**: When selector can't be determined
   ```typescript
   // Click element [ref=e1] - TODO: Add proper selector
   ```

### Improving Selectors

If you get TODO comments, you can:

1. **Inspect the snapshot in JSON** - Look at `result.snapshot` field
2. **Use browser DevTools** - Find stable selectors manually
3. **Add data-testid attributes** - In your own app for reliable testing

```typescript
// Instead of:
// Click element [ref=e1] - TODO: Add proper selector

// Replace with:
await page.locator('data-testid=submit-button').click();
// or
await page.locator('#submit-btn').click();
// or
await page.locator('button:has-text("Submit")').click();
```

---

## Performance Comparison

### AI Execution (Slow but Smart)
- Figures out what to do: 5-10 seconds
- Each action: 2-3 seconds (AI decides + execute)
- **Total for 5 actions: 15-25 seconds**

### Exported Code Execution (Fast but Fixed)
- No AI reasoning needed
- Direct Playwright commands
- **Total for 5 actions: < 1 second**

---

## Best Practices

### 1. Use AI for Discovery
- Explore new websites
- Figure out complex workflows
- Handle dynamic content

### 2. Export for Repetition
- Regression testing
- Scheduled automation
- CI/CD pipelines

### 3. Refine Manually
- Review exported code
- Add assertions (`expect()` statements)
- Handle edge cases
- Add proper waits

### Example Workflow:

```
1. AI Discovery (Once)
   "Go to my-app.com, login as test@example.com with password 'test123', 
    and verify the dashboard shows user profile"

2. Export Code
   - Click "Export as Playwright"
   - Download .spec.ts file

3. Manual Refinement
   - Add assertions for verification
   - Add data-testid to your app
   - Replace dynamic selectors

4. Run in CI/CD (Many times, fast)
   - npx playwright test login.spec.ts
   - Runs in < 1 second
   - No API costs
```

---

## Troubleshooting

### "No steps to export"
- Execute an instruction first
- Wait for completion
- Only successful executions can be exported

### "TODO: Add proper selector" comments
- Check the JSON export for snapshot data
- Use browser DevTools to find stable selectors
- Update the generated code manually

### Selectors not working
- Page structure may have changed
- Use more specific selectors
- Add waits: `await page.waitForSelector()`
- Use data-testid attributes in your app

---

## Advanced: Custom Export Processing

You can process the JSON export programmatically:

```javascript
// Load JSON export
const data = require('./automation-steps.json');

// Extract all URLs visited
const urls = data.steps
  .filter(s => s.tool === 'browser_navigate')
  .map(s => s.arguments.url);

console.log('URLs visited:', urls);

// Extract all clicks and their targets
const clicks = data.steps
  .filter(s => s.tool === 'browser_click')
  .map(s => ({
    ref: s.arguments.ref,
    snapshot: s.result.snapshot
  }));

// Generate custom framework code
// ... your custom code generator ...
```

---

## Summary

✅ **Record once with AI** - Let AI figure out the steps  
✅ **Export for reuse** - Get Playwright code + JSON data  
✅ **Replay instantly** - No AI overhead, sub-second execution  
✅ **Customize as needed** - Refine selectors and add logic  

The export feature bridges the gap between AI-powered exploration and production automation!
