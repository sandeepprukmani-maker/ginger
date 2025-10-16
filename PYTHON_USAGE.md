# Browser Automation with Python

This guide shows you how to use the Python script to automate browser interactions using natural language prompts. The script automatically scans the DOM - **no locators needed**!

## Prerequisites

1. **MCP Server Running**: The Playwright MCP server must be running on port 8080 (it's already configured in this Replit)
2. **OpenAI API Key**: You need an OpenAI API key

## Quick Start

### 1. Set Your API Key

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or create a `.env` file:
```bash
OPENAI_API_KEY=your-api-key-here
```

**Where to get an API key:**
- Go to https://platform.openai.com/
- Sign up or log in
- Navigate to API Keys section
- Create a new API key
- Copy it and use it here

### 2. Run with a Prompt

```bash
# Command line usage
python browser_automation.py "Go to google.com and search for Python"

# Interactive mode
python browser_automation.py
```

## How It Works

1. **You provide a natural language prompt** - Describe what you want to do in plain English
2. **GPT-4o-mini interprets the prompt** - Uses OpenAI's AI to understand your intent
3. **MCP server executes actions** - Automatically finds elements using DOM scanning (no locators!)
4. **Returns rerunnable code** - Generates a Python script you can run again

## Examples

### Example 1: Simple Navigation
```bash
python browser_automation.py "Navigate to github.com"
```

### Example 2: Search
```bash
python browser_automation.py "Go to google.com and search for 'Model Context Protocol'"
```

### Example 3: Form Filling
```bash
python browser_automation.py "Go to example.com/login, fill username with 'test@example.com' and password with 'password123', then click submit"
```

### Example 4: Complex Workflow
```bash
python browser_automation.py "Navigate to github.com, click on the search box, type 'playwright', press Enter, and click on the first result"
```

## Generated Output

The script generates two things:

### 1. Console Output
Shows real-time execution of each step:
```
✓ Connected to MCP server: Playwright MCP
✓ Loaded 45 browser automation tools

🤖 Processing prompt: Go to google.com

  → Executing: browser_navigate
  → Executing: browser_snapshot

✓ Successfully navigated to Google

✓ Rerunnable script saved to: automation_script.py
```

### 2. Rerunnable Script (`automation_script.py`)
A standalone Python script that can be executed independently:

```python
#!/usr/bin/env python3
# Auto-generated browser automation script

import asyncio
import httpx

MCP_SERVER_URL = "http://localhost:8080/mcp"

async def run_automation():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Initialize connection
        await client.post(
            MCP_SERVER_URL,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                # ... initialization params
            }
        )
        
        # Step 1: browser_navigate
        response = await client.post(
            MCP_SERVER_URL,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "browser_navigate",
                    "arguments": {"url": "https://google.com"}
                }
            }
        )
        print('Step 1 completed: browser_navigate')

if __name__ == '__main__':
    asyncio.run(run_automation())
```

You can run this generated script directly:
```bash
python automation_script.py
```

## Key Features

### ✅ No Locators Required
The MCP server uses Playwright's accessibility tree to automatically find elements. You don't need to provide CSS selectors, XPath, or any locators.

### ✅ Natural Language Interface
Just describe what you want in plain English:
- "Click the login button"
- "Fill the email field with test@example.com"
- "Navigate to the pricing page"

### ✅ DOM Scanning
The server automatically scans the page's DOM structure and finds the right elements based on your description.

### ✅ Rerunnable Code
Every automation generates a standalone Python script that you can:
- Run again later
- Modify and customize
- Share with others
- Schedule as a cron job

## Available Browser Actions

The MCP server provides these automation capabilities:
- **Navigate**: Go to URLs
- **Click**: Click on elements (buttons, links, etc.)
- **Fill**: Fill form fields
- **Type**: Type text
- **Select**: Select dropdown options
- **Upload**: Upload files
- **Drag**: Drag and drop
- **Evaluate**: Run JavaScript
- **Screenshot**: Take screenshots
- **PDF**: Generate PDFs
- And many more...

## Tips

1. **Be Specific**: The more specific your prompt, the better
   - ❌ "Click button" 
   - ✅ "Click the blue Submit button at the bottom"

2. **Break Complex Tasks**: For complex workflows, break them into steps
   ```bash
   python browser_automation.py "Go to site.com, click login, fill email with x@y.com, fill password with pass123, click submit, wait for dashboard to load"
   ```

3. **Check Generated Code**: Always review the generated `automation_script.py` before running in production

4. **Error Handling**: If an action fails, the script will show the error. Adjust your prompt and try again.

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY='your-key'
```

### "Connection refused to localhost:8080"
Make sure the MCP Server workflow is running in Replit

### Element Not Found
Try being more specific in your description:
- Include button text: "Click the 'Sign Up' button"
- Mention location: "Click the search icon in the top right"
- Add context: "Fill the username field in the login form"

## Advanced Usage

### Programmatic Usage

You can also use the automation agent in your own Python scripts:

```python
import asyncio
from browser_automation import BrowserAutomationAgent

async def my_automation():
    agent = BrowserAutomationAgent(api_key="your-key")
    
    # Execute automation
    code = await agent.execute_prompt(
        "Navigate to example.com and take a screenshot"
    )
    
    print("Generated code:", code)

asyncio.run(my_automation())
```

### Custom MCP Server URL

```python
from browser_automation import PlaywrightMCPClient

client = PlaywrightMCPClient(server_url="http://custom-host:port/mcp")
await client.initialize()
```

## Next Steps

1. Try the examples above
2. Experiment with your own prompts
3. Review and customize the generated scripts
4. Build complex automation workflows

Happy automating! 🚀
