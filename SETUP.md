# Browser Automation Framework - Complete Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Application](#running-the-application)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.11+** (Python 3.11 or higher)
- **Node.js 20+** (for Playwright MCP server)
- **Git** (for cloning the repository)

### Required API Keys
- **OpenAI API Key** - Get from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
  - Needed for AI-powered features (GPT-4o-mini and GPT-4 Vision)
  - Optional for basic automation without AI features

---

## Installation

### Step 1: Clone the Repository
```bash
git clone <your-repository-url>
cd browser-automation-framework
```

### Step 2: Install Python Dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using uv (faster):
```bash
pip install uv
uv pip install -r requirements.txt
```

Required packages:
- `mcp>=1.18.0` - Model Context Protocol
- `openai>=2.4.0` - OpenAI API client
- `playwright>=1.55.0` - Browser automation
- `pydantic>=2.12.2` - Data validation
- `python-dotenv>=1.1.1` - Environment variables
- `rich>=14.2.0` - Terminal formatting
- `tenacity>=9.1.2` - Retry logic

### Step 3: Install Playwright Browsers

Install Chromium browser for Playwright:
```bash
playwright install chromium
```

Optional - install all browsers:
```bash
playwright install
```

### Step 4: Install Node.js Dependencies

For Playwright MCP server:
```bash
npm install
```

This installs:
- `@playwright/mcp` - Playwright MCP server

---

## Configuration

### Option 1: Using Environment Variables (Recommended for Replit)

Set your OpenAI API key as an environment variable:

**On Linux/Mac:**
```bash
export OPENAI_API_KEY="your_api_key_here"
```

**On Windows:**
```cmd
set OPENAI_API_KEY=your_api_key_here
```

**On Replit:**
Use the Secrets tab to add `OPENAI_API_KEY`

### Option 2: Using .env File

1. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API key:
```bash
OPENAI_API_KEY=your_api_key_here
```

### Option 3: Edit config.ini

The framework uses `config.ini` for advanced configuration:

```ini
[OpenAI]
# Your OpenAI API key (can use ${ENV_VARIABLE} syntax)
api_key = ${OPENAI_API_KEY}
model = gpt-4o-mini

[Browser]
browser_type = chromium
headless = true
timeout = 45000
screenshot_on_error = true

[Automation]
max_retries = 5
retry_delay = 1
log_level = INFO
enable_vision = true
vision_on_first_retry = true

[Paths]
screenshots_dir = screenshots
logs_dir = logs
```

---

## Running the Application

The framework provides two main applications:

### 1. Browser Automation CLI (Simple Demos)

Interactive CLI with pre-built automation demos:

```bash
python main.py
```

**Available Demos:**
- Web Automation Demo - Navigate websites and extract content
- Form Automation Demo - Fill web forms automatically
- Data Extraction Demo - Extract structured data from pages
- AI Code Generation - Generate Playwright code from descriptions

**Example Session:**
```
╭───────────────────────────────────────╮
│ Browser Automation Framework          │
│ Universal web automation for any site │
╰───────────────────────────────────────╯

Available Demos:
  1. Web Automation Demo
  2. Form Automation Demo
  3. Data Extraction Demo
  4. AI Code Generation 
  5. Exit

Select an option [1/2/3/4/5] (1): 1
Enter URL to automate: https://example.com
```

### 2. Natural Language Automation (Advanced AI-Powered)

Enhanced automation using natural language commands:

```bash
python nl_automation_mcp.py
```

**Features:**
- Natural language command interface
- GPT-4 Vision for intelligent element detection
- Smart error recovery with 5 retry attempts
- Session memory learns from successful patterns
- Auto-generates Playwright code
- Autonomous multi-step execution

**Example Session:**
```
======================================================================
🚀 ENHANCED Playwright MCP Natural Language Automation
======================================================================

Configuration:
  • AI Model: gpt-4o-mini
  • Browser: chromium (headless: True)
  • Vision: Enabled
  • Max Retries: 5

💬 Command: Go to google.com and search for Python tutorials

[Processing...]
✅ Navigation completed. Search executed. Screenshot saved.

📝 GENERATED PLAYWRIGHT CODE:
[Shows working Playwright code]
```

---

## Usage Examples

### Basic Navigation
```
💬 Command: Go to news.ycombinator.com
💬 Command: Navigate to github.com and click trending repositories
```

### Form Filling
```
💬 Command: Go to example.com/contact and fill name with John Doe
💬 Command: Fill out the form with email test@example.com and message Hello World
```

### Data Extraction
```
💬 Command: Extract all article headlines from this page
💬 Command: Get all product names and prices
💬 Command: Scrape the table data
```

### Screenshots
```
💬 Command: Take a screenshot of the current page
💬 Command: Navigate to example.com and capture a screenshot
```

### Complex Multi-Step Tasks
```
💬 Command: Go to google.com, search for Python, and click the first result
💬 Command: Navigate through pagination and collect all items
```

---

## Project Structure

```
browser-automation-framework/
├── src/
│   └── automation/
│       ├── __init__.py
│       ├── browser_engine.py      # Browser control
│       ├── task_executor.py       # Task execution
│       ├── ai_generator.py        # AI code generation
│       ├── vision_analyzer.py     # GPT-4 Vision analysis
│       ├── mcp_client.py          # MCP protocol client
│       ├── session_memory.py      # Learning & memory
│       ├── recorder.py            # Interaction recording
│       ├── config.py              # Configuration models
│       ├── config_loader.py       # Config loading
│       └── logger.py              # Logging utilities
├── main.py                        # CLI demo application
├── nl_automation_mcp.py           # Natural language automation
├── nrw.py                         # No Repeat Work automation
├── test_automation.py             # Test suite
├── config.ini                     # Main configuration
├── requirements.txt               # Python dependencies
├── package.json                   # Node.js dependencies
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
└── replit.md                      # Project documentation
```

---

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Solution:**
1. Verify your API key is set as an environment variable or in `.env`
2. Check that `.env` file is in the project root
3. Ensure the key starts with `sk-`
4. Restart the application after setting the key

```bash
# Verify the key is set
echo $OPENAI_API_KEY  # Linux/Mac
echo %OPENAI_API_KEY% # Windows
```

### Issue: "Playwright browser not found"

**Solution:**
Install Playwright browsers:
```bash
playwright install chromium
```

### Issue: "Module not found" errors

**Solution:**
Reinstall dependencies:
```bash
pip install -r requirements.txt
npm install
```

### Issue: "Permission denied" on Linux

**Solution:**
Playwright may need additional system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
  libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
```

### Issue: Screenshots not saving

**Solution:**
Ensure the screenshots directory exists and has write permissions:
```bash
mkdir -p screenshots
chmod 755 screenshots
```

### Issue: "AI did not return tool calls"

**Solution:**
1. Check your OpenAI API key is valid
2. Verify you have API credits available
3. Try a simpler command first
4. Check the logs for detailed error messages

### Issue: Browser hangs or times out

**Solution:**
Increase timeout in `config.ini`:
```ini
[Browser]
timeout = 60000  # 60 seconds
```

### Issue: Elements not found on page

The framework has built-in retry logic:
1. First retry: Uses GPT-4 Vision to locate elements
2. Subsequent retries: Uses element catalog with fuzzy matching
3. Final fallback: Page refresh and retry

If still failing:
- Try more specific selectors
- Wait for page to fully load
- Check if element is in an iframe

---

## Advanced Configuration

### Custom Browser Settings

Edit `config.ini`:
```ini
[Browser]
browser_type = chromium     # or firefox, webkit
headless = true            # false for visible browser
viewport_width = 1920
viewport_height = 1080
```

### Vision Settings

```ini
[Automation]
enable_vision = true              # Enable GPT-4 Vision
vision_on_first_retry = true      # Use vision on first failure
max_retries = 5                   # Maximum retry attempts
```

### Logging

```ini
[Automation]
log_level = INFO    # DEBUG, INFO, WARNING, ERROR
```

Logs are saved to `logs/` directory.

---

## Running in Production

### Headless Mode (Default)
```bash
python nl_automation_mcp.py
```

### With Visible Browser
Edit `config.ini`:
```ini
[Browser]
headless = false
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .
CMD ["python", "nl_automation_mcp.py"]
```

---

## Next Steps

1. **Try the demos** - Run `python main.py` and explore
2. **Test natural language** - Run `python nl_automation_mcp.py`
3. **Read the examples** - See common automation patterns
4. **Customize config.ini** - Adjust settings for your needs
5. **Build your automation** - Create custom scripts

---

## Support & Resources

- **OpenAI Documentation**: https://platform.openai.com/docs
- **Playwright Documentation**: https://playwright.dev/python/
- **MCP Protocol**: https://github.com/modelcontextprotocol

---

## Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed
- [ ] Cloned repository
- [ ] Installed Python dependencies (`pip install -r requirements.txt`)
- [ ] Installed Playwright browsers (`playwright install chromium`)
- [ ] Installed Node.js dependencies (`npm install`)
- [ ] Set OPENAI_API_KEY (environment variable or .env file)
- [ ] Run `python main.py` or `python nl_automation_mcp.py`
- [ ] Success! 🎉

---

**Happy Automating! 🚀**
