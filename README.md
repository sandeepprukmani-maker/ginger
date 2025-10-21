# Playwright MCP CLI

Convert natural language commands into self-healing Playwright automation scripts.

## Features

- 🗣️ **Natural Language Input**: Describe automation tasks in plain English
- 🧠 **AI-Powered Code Generation**: Automatically generates Playwright Python code with OpenAI
- 🔍 **Multiple Locator Strategies**: Uses role, text, label, placeholder, and CSS selectors
- 🛠️ **Self-Healing**: Automatically fixes broken locators when execution fails
- 📝 **Standalone Scripts**: Generates executable Python files that work without AI/MCP

## Quick Start

### Interactive Mode
```bash
python main.py --interactive
```

Then enter natural language commands like:
- `Go to google.com and search for Playwright`
- `Navigate to example.com and click the login button`
- `Open github.com and search for Replit`

### Direct Command
```bash
python main.py "Go to google.com and search for Playwright"
```

### With Custom Output File
```bash
python main.py "Login to example.com" --output my_automation.py
```

### Show Browser (Non-Headless Mode)
```bash
python main.py "Go to example.com" --show-browser
```

## How It Works

1. **Generate**: OpenAI converts your natural language to Playwright code
2. **Execute**: The code runs in Chromium browser
3. **Heal**: If locators fail, AI regenerates better alternatives
4. **Save**: Outputs a standalone Python script for reuse

## Example

**Input:**
```
Go to example.com and click the More Information link
```

**Generated Code:**
```python
def run_automation(page):
    page.goto("https://example.com")
    page.get_by_role("link", name="More information").click()
```

**Output:**
Standalone script saved to `generated_scripts/automation_*.py`

## Requirements

- Python 3.11+
- OpenAI API key (set as `OPENAI_API_KEY` environment variable)
- Playwright with Chromium browser

## Generated Scripts

All generated scripts are saved to `generated_scripts/` directory and can be run independently:

```bash
python generated_scripts/automation_20251021_120000.py
```

## Locator Strategy Priority

1. `get_by_role()` - Most stable, semantic HTML
2. `get_by_label()` - Form fields
3. `get_by_placeholder()` - Input fields
4. `get_by_text()` - Links and buttons
5. `locator()` with data-testid - If available
6. CSS selectors - Last resort

## Self-Healing Example

If a locator like `page.locator("#submit-btn")` fails, the self-healing engine:
1. Detects the failure
2. Analyzes the error and original command
3. Generates alternative locators (e.g., `page.get_by_role("button", name="Submit")`)
4. Re-executes with the healed code
5. Saves the working version

## Notes

- Browser runs in headless mode by default
- Generated scripts include all necessary imports
- Scripts are executable without OpenAI API after generation
