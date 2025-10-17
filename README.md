# Browser Automation Framework

A powerful Python-based browser automation framework powered by Playwright and AI. Build robust browser automation for **any website** using natural language instructions or code. Features intelligent error handling, learning capabilities, and automatic retry with corrections.

## Features

### 🎯 Enhanced Natural Language Automation (UPGRADED!)
- **Just describe what you want**: "Go to google.com and search for Python"
- **Vision-based intelligence**: Optional GPT-4 Vision analysis for complex pages
- **Smart element detection**: Multiple fallback strategies to find elements
- **Advanced web handling**: Supports iframes, popups, dynamic content, file uploads
- **Intelligent error recovery**: Analyzes failures with vision and retries with corrections
- **Session memory**: Learns from successful patterns to improve over time
- **No coding or selectors needed**: Perfect for non-technical users

### 🚀 Core Browser Automation
- **Multi-browser support**: Chromium, Firefox, WebKit
- **Smart selectors**: Automatic fallback between CSS, XPath, text, and ARIA strategies
- **Robust error handling**: Built-in retry logic with exponential backoff
- **Session management**: Cookie and state persistence across runs
- **Debugging tools**: Screenshots, video recording, and trace files

### 🤖 AI-Powered Features
- Generate Playwright automation code from natural language descriptions
- Intelligent error analysis and automatic corrections
- Context-aware action generation
- Uses OpenAI GPT-4 for intelligent automation

### 📦 Task Execution Library
- Pre-built automation patterns:
  - Form filling (any website)
  - Table scraping
  - Link extraction
  - Screenshot capture
  - Custom JavaScript execution
  - Scroll automation
  - Wait strategies

### ⚙️ Flexible Configuration
- Environment-based configuration
- Customizable timeouts and retries
- Headless and headed browser modes
- Detailed logging with Rich console output

## Quick Start

### Natural Language Automation (Easiest!)

Just tell the automation what you want to do in plain English:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY='your-api-key'

# Run natural language automation
python nl_automation.py
```

Then simply type instructions like:
- "Go to news.ycombinator.com and get the top 5 story titles"
- "Navigate to github.com and click the login button"
- "Visit example.com and extract all headings"
- "Search google for 'browser automation' and get the first 3 results"

The AI will:
1. Convert your instruction into browser actions
2. Use vision to understand page structure (optional)
3. Intelligently find elements with multiple fallback strategies
4. Handle complex scenarios (iframes, dynamic content, popups)
5. Learn from any errors and retry automatically with better selectors
6. Remember successful patterns for future use

**Advanced Features:**
- Vision-based page analysis for difficult-to-automate pages
- Smart element finding (no need to know exact selectors)
- Dynamic content waiting
- Multi-page navigation
- Table and link extraction
- Error diagnosis with screenshots

### Basic Usage (Code)

```python
from src.automation import BrowserEngine, TaskExecutor
from src.automation.config import BrowserConfig, AutomationConfig

async def main():
    # Configure browser
    browser_config = BrowserConfig(headless=True)
    automation_config = AutomationConfig()
    
    # Create browser engine
    browser = BrowserEngine(browser_config, automation_config)
    executor = TaskExecutor(browser)
    
    # Start browser
    await browser.start()
    
    # Navigate to any website
    await browser.navigate("https://example.com")
    
    # Extract data
    headings = await browser.get_all_text("h1, h2")
    links = await browser.get_all_text("a")
    
    # Take screenshot
    await browser.screenshot("page_screenshot")
    
    # Stop browser
    await browser.stop()
```

### Run Interactive Demos

**Natural Language Automation** (Recommended):
```bash
python nl_automation.py
```

**Traditional Demo Menu**:
```bash
python main.py
```

This will launch an interactive menu with demos for:
1. **Web Automation Demo** - Navigate and extract data from any site
2. **Form Automation Demo** - Fill and submit forms on any website
3. **Data Extraction Demo** - Extract specific data from any page
4. **AI Code Generation** - Generate automation code from descriptions

### Run Examples

```bash
# Web scraping any site
python examples/web_scraping_example.py

# Form filling automation
python examples/form_filling_example.py

# AI code generation (requires OPENAI_API_KEY)
python examples/ai_code_generation_example.py

# Advanced automation patterns
python examples/advanced_automation_example.py
```

## Environment Variables

Configuration via environment variables:

```bash
# AI Features (REQUIRED for natural language automation)
OPENAI_API_KEY=your_openai_api_key

# Browser Configuration
BROWSER_TYPE=chromium          # chromium, firefox, or webkit
HEADLESS=true                  # true or false
TIMEOUT=30000                  # Default timeout in milliseconds

# Automation Settings
MAX_RETRIES=3                  # Number of retry attempts
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
```

## Use Cases

### Natural Language Web Scraping
The easiest way - just describe what you want:

```
Instruction: "Go to news.ycombinator.com and extract the top 10 story titles"
→ AI converts to actions and executes automatically
→ Returns: List of story titles
```

### Traditional Web Scraping
Scrape data from any website - e-commerce, news sites, job boards, etc.

```python
await browser.navigate("https://any-website.com")
products = await browser.get_all_text(".product-title")
prices = await browser.get_all_text(".price")
```

### Form Automation
Fill and submit forms on any website automatically.

```python
form_data = {
    "input[name='email']": "user@example.com",
    "input[name='password']": "password123",
    "#country": "USA"
}
await executor.fill_form(form_data)
await browser.click("button[type='submit']")
```

### Testing
Automated testing for any web application.

```python
await browser.navigate("https://your-app.com")
await browser.click("#login-button")
await browser.fill("#username", "testuser")
await browser.fill("#password", "testpass")
await browser.click("#submit")
assert await browser.get_text(".welcome-message")
```

### Data Monitoring
Monitor prices, availability, or any data changes.

```python
await browser.navigate("https://target-site.com")
current_price = await browser.get_text(".price")
# Compare with previous price, send alerts, etc.
```

## Project Structure

```
.
├── src/automation/           # Core automation framework
│   ├── browser_engine.py    # Main browser automation engine
│   ├── selectors.py          # Smart selector system
│   ├── task_executor.py     # Task execution framework
│   ├── ai_generator.py      # AI code generation
│   ├── config.py            # Configuration management
│   └── logger.py            # Enhanced logging
├── examples/                 # Example scripts
│   ├── web_scraping_example.py
│   ├── form_filling_example.py
│   ├── ai_code_generation_example.py
│   └── advanced_automation_example.py
├── main.py                  # Interactive demo
└── README.md               # This file
```

## API Reference

### BrowserEngine

Main browser automation engine with Playwright integration.

```python
browser = BrowserEngine(browser_config, automation_config)

# Core methods
await browser.start()                          # Start browser
await browser.stop()                           # Stop browser
await browser.navigate(url)                    # Navigate to URL
await browser.click(selector)                  # Click element
await browser.fill(selector, value)            # Fill input
await browser.get_text(selector)               # Get element text
await browser.get_all_text(selector)           # Get all matching elements
await browser.screenshot(name)                 # Take screenshot
await browser.wait_for_load()                  # Wait for page load
await browser.execute_script(script)           # Run JavaScript
```

### TaskExecutor

Pre-built automation tasks and patterns.

```python
executor = TaskExecutor(browser)

# Common tasks
await executor.fill_form({"selector": "value", ...})
table_data = await executor.scrape_table("table.data")

# Or use task-based execution
from src.automation.task_executor import TaskType
result = await executor.execute_task(TaskType.EXTRACT_TEXT, {"selector": "h1"})
```

### AITaskGenerator

AI-powered code generation (requires OPENAI_API_KEY).

```python
generator = AITaskGenerator()

code = await generator.generate_playwright_code("Your automation task description")
code = await generator.generate_scraping_code(url, "data to extract")
code = await generator.generate_form_filling_code(url, "form fields description")
```

## Configuration

### BrowserConfig

```python
from src.automation.config import BrowserConfig, BrowserType

config = BrowserConfig(
    browser_type=BrowserType.CHROMIUM,    # Browser type
    headless=True,                         # Headless mode
    timeout=30000,                         # Default timeout (ms)
    viewport_width=1920,                   # Viewport width
    viewport_height=1080,                  # Viewport height
    screenshot_on_error=True,              # Auto screenshot on error
    video_recording=False,                 # Record video
    user_agent="custom UA",                # Custom user agent
)
```

### AutomationConfig

```python
from src.automation.config import AutomationConfig

config = AutomationConfig(
    max_retries=3,                         # Retry attempts
    retry_delay=2,                         # Delay between retries
    screenshot_dir="screenshots",          # Screenshot directory
    save_session=True,                     # Save browser session
    session_name="my_session",             # Session name
    log_level="INFO",                      # Logging level
)
```

## Advanced Features

### Session Persistence

Save and restore browser sessions (cookies, local storage):

```python
config = AutomationConfig(
    save_session=True,
    session_name="my_app_session"
)

# Session is automatically saved on browser.stop()
# and restored on browser.start()
```

### Smart Selectors

Automatic fallback between different selector strategies:

```python
from src.automation.selectors import SmartSelector, SelectorOptions

options = SelectorOptions(strategy=SelectorStrategy.AUTO)
element = await SmartSelector.find_element(page, "button", options)
```

### Error Handling

Built-in retry logic with exponential backoff:

```python
# Automatic retries on navigation failures
await browser.navigate(url)  # Retries up to 3 times

# Custom retry configuration
config = AutomationConfig(max_retries=5, retry_delay=3)
```

## Troubleshooting

### Browser Won't Start
- Ensure Playwright browsers are installed: `python -m playwright install chromium`
- For system dependencies: Run `playwright install-deps` (local) or contact support (cloud)

### AI Code Generation Not Working
- Set OPENAI_API_KEY environment variable
- Verify OpenAI API key is valid
- Check API quota and usage limits

### Selectors Not Working
- Use AUTO strategy for automatic fallback: `SelectorOptions(strategy=SelectorStrategy.AUTO)`
- Enable debug logging: `AutomationConfig(log_level="DEBUG")`
- Take screenshots to inspect page state

## Why This Framework?

✅ **Universal** - Works with any website, no site-specific code  
✅ **Robust** - Smart selectors with automatic fallback  
✅ **Production-ready** - Comprehensive error handling  
✅ **Flexible** - Easy to customize for any use case  
✅ **AI-powered** - Generate code from natural language  

---

**Built with ❤️ using Playwright, OpenAI, and Python**
