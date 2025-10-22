# Natural Language to Playwright Converter

Convert natural language commands into Playwright-specific locators and actions using browser-use AI agent.

## Features

- 🤖 Natural language input (e.g., "go to google.com, search for dogs, click first link")
- 🎯 Generates Playwright-specific locators and actions
- 🔄 Supports multi-page navigation
- 📑 Handles multi-tab scenarios
- ⚠️ Alert handling
- 📝 Exports ready-to-use Playwright scripts

## Setup

1. Install dependencies:
```bash
uv pip install -e .
uvx playwright install chromium --with-deps
```

2. Set up environment variables:
```bash
# Copy .env.example to .env and add your API keys
cp .env.example .env
```

3. Add your LLM API key to `.env`:
```
# Choose one:
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
GEMINI_API_KEY=your-key-here
```

## Usage

Run the converter:
```bash
python main.py
```

Enter your natural language command:
```
> go to google.com, search for "cute dogs", and click on the first image result
```

The tool will:
1. Execute the task using browser-use AI agent
2. Capture all actions taken
3. Generate a Playwright script with proper locators
4. Save it to `generated_scripts/`

## Example Output

```python
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to google.com
        page.goto("https://google.com")
        
        # Search for "cute dogs"
        page.locator('textarea[name="q"]').fill("cute dogs")
        page.keyboard.press("Enter")
        
        # Click first image result
        page.locator('a[data-ri="0"]').click()
        
        browser.close()

if __name__ == "__main__":
    run()
```
