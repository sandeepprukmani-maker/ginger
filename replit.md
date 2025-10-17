# Browser Automation Framework

## Overview
A comprehensive Python-based browser automation framework powered by Playwright and AI. This framework enables powerful browser automation for **any website** using natural language instructions via Model Context Protocol (MCP). Features intelligent error handling, learning capabilities, and automatic retry with corrections. Completely generic with no site-specific dependencies.

## Project Status
**✅ FULLY OPERATIONAL + MCP INTEGRATED** - Successfully configured in Replit environment
- All dependencies installed and verified
- Playwright browser (Chromium) configured with system dependencies
- **NEW: Playwright MCP Server integration (@playwright/mcp) ✨**
- OpenAI API integration active
- Natural language automation tested and working via MCP

## Recent Changes (October 17, 2025)

**🚀 Playwright MCP Server Integration:**
- Integrated Microsoft's official Playwright MCP server (@playwright/mcp@latest)
- Created PlaywrightMCPClient for standardized browser automation via Model Context Protocol
- Built MCP-powered natural language automation (nl_automation_mcp.py)
- MCP server provides 21 browser automation tools:
  - Navigation: browser_navigate, browser_navigate_back
  - Interaction: browser_click, browser_type, browser_fill_form, browser_select_option
  - Advanced: browser_drag, browser_hover, browser_file_upload
  - Analysis: browser_snapshot, browser_take_screenshot, browser_console_messages
  - Network: browser_network_requests
  - Management: browser_tabs, browser_close, browser_resize
  - Utilities: browser_evaluate, browser_press_key, browser_wait_for, browser_handle_dialog
  - Setup: browser_install
- AI (GPT-4) automatically selects and chains appropriate MCP tools for complex tasks
- Provides more robust and standardized automation than direct Playwright API
- Fixed NixOS environment issues for npx/MCP server compatibility

**Import to Replit Completed + Bug Fixes:**
- Successfully migrated browser automation framework to Replit environment
- Installed Playwright Chromium browser and system dependencies
- Configured OpenAI API key via Replit Secrets
- Installed required system packages: nspr, nss, dbus, atk, cups, mesa, cairo, pango, xorg libraries
- Fixed smart selector bug: Now properly excludes submit buttons when searching for text inputs
- Enhanced search selector: Added Google-specific patterns (input[name="q"]) and prioritization
- Improved strategy order: More specific selectors (aria-label, placeholder) run before generic type matching
- Verified all features are operational
- Workflow configured and tested

**Major Enhancement - Intelligent & Powerful Automation:**
- **Vision-Based Intelligence**: Added GPT-4 Vision for page structure analysis and element detection
- **Advanced Playwright Tools**: Comprehensive toolkit for complex web automation
  - Smart element finding with DOM inspection
  - Dynamic content handling (AJAX, lazy loading)
  - iframe and popup management
  - File upload/download support
  - Table and link extraction
  - Intelligent waiting strategies
- **Enhanced Natural Language Executor**: Upgraded with vision and advanced capabilities
  - Vision-based error diagnosis with screenshot analysis
  - Multi-strategy element finding (text, ARIA, CSS, XPath)
  - Context-aware action generation
  - Intelligent error correction with better selectors
- **Session Memory**: Persistent learning from successful patterns and failures
- **Interactive Enhanced Interface**: nl_automation.py with vision mode option

**Earlier Today:**
- Created NaturalLanguageExecutor for instruction-to-action conversion
- Added SessionMemory for tracking successful patterns
- Enhanced retry logic with AI-powered error analysis

## Previous Changes (October 16, 2025)
- Created modular browser automation framework with Python 3.11
- Implemented core BrowserEngine with multi-browser support (Chromium, Firefox, WebKit)
- Built SmartSelector system with automatic fallback strategies (CSS, XPath, text, ARIA)
- Added TaskExecutor for common automation patterns (scraping, forms, navigation)
- Integrated AI-powered code generation using OpenAI GPT-4 with MCP server
- Implemented robust error handling with retry logic using tenacity
- Added session management with cookie and state persistence
- Created logging system with Rich console output
- Built example scripts for various automation scenarios
- Set up configuration management system

## Architecture

### Core Components

**src/automation/**
- `browser_engine.py` - Main browser automation engine with Playwright integration
- `selectors.py` - Smart selector system with automatic strategy fallback
- `task_executor.py` - Task execution framework for common automation patterns
- `mcp_client.py` - **NEW** Playwright MCP server client for standardized automation
- `enhanced_nl_executor.py` - **ENHANCED** Advanced NL executor with vision & intelligence
- `nl_executor.py` - Basic natural language instruction executor
- `advanced_tools.py` - **NEW** Advanced Playwright tools (iframes, dynamic content, smart finding)
- `vision_analyzer.py` - **NEW** GPT-4 Vision-based page analysis and element detection
- `session_memory.py` - **NEW** Persistent memory for learning from executions
- `ai_generator.py` - AI-powered Playwright code generation using OpenAI
- `config.py` - Configuration management (browser, automation settings)
- `logger.py` - Enhanced logging with Rich console output

**Entry Points**
- `nl_automation_mcp.py` - **NEW** MCP-powered natural language automation (recommended)
- `nl_automation.py` - **ENHANCED** Interactive NL automation with vision mode
- `main.py` - Traditional demo menu with code-based automation

### Features

**🎭 MCP-Powered Automation (Primary Approach)**
- Uses Microsoft's official Playwright MCP server for standardized automation
- AI (GPT-4) intelligently selects and chains 21+ browser automation tools
- Model Context Protocol ensures robust, reliable browser control
- Convert plain English to automated browser actions via MCP tools
- No coding or selectors required - AI handles everything
- More stable than direct Playwright API calls

**Enhanced Natural Language Automation**
- Convert plain English instructions to browser actions
- **Vision-based page understanding** for complex sites
- **Smart element detection** with multiple fallback strategies
- **Advanced web features**: iframes, popups, dynamic content, file uploads
- Intelligent error analysis with visual diagnosis
- Automatic corrections with better selectors
- Learn from successful patterns
- Persistent session memory across runs
- Context-aware action generation
- No coding or selectors required - just describe what you want

**Browser Automation**
- Multi-browser support (Chromium, Firefox, WebKit)
- Headless and headed modes
- Smart selector strategies with automatic fallback
- Robust error handling and retry logic
- Screenshot and video recording
- Session and cookie management
- Trace recording for debugging

**Task Execution**
- Pre-built tasks: navigate, click, fill, extract text/links, screenshot, wait, scroll
- Form filling automation (any website)
- Table scraping (any website)
- Data extraction (any website)
- Custom JavaScript execution

**AI-Powered Features**
- Generate Playwright code from natural language descriptions
- Intelligent error correction with retry logic
- Pre-built templates for scraping, form filling, login automation
- Context-aware automation based on execution history

**Configuration**
- Environment-based configuration
- Customizable timeouts and retries
- Session persistence
- Screenshot/video directories
- Logging levels

## Dependencies

**Core**
- Python 3.11
- playwright (browser automation)
- openai (AI code generation)
- mcp (Model Context Protocol client)
- @playwright/mcp (Playwright MCP server - npm package)
- Node.js 20 (for MCP server)

**Utilities**
- python-dotenv (environment management)
- tenacity (retry logic)
- rich (console output)
- pydantic (data validation)

## Usage Examples

### MCP-Powered Natural Language Automation (Recommended)
```bash
# Run the MCP-powered automation:
uv run python nl_automation_mcp.py

# Then type natural language commands:
# "Go to google.com and search for Python tutorials"
# "Navigate to github.com and click the login button"
# "Visit news.ycombinator.com and get the top 5 story titles"

# The AI will:
# 1. Use GPT-4 to understand your command
# 2. Select appropriate MCP browser automation tools
# 3. Chain multiple tools for complex tasks
# 4. Execute via Playwright MCP server
# 5. Provide clear feedback on progress
```

### Enhanced Natural Language Automation (Vision Mode)
```python
# Just run nl_automation.py and type instructions like:
# "Go to news.ycombinator.com and get the top 5 story titles"
# "Navigate to github.com and click the login button"
# "Visit example.com and extract all headings"

# The AI will:
# 1. Convert your instruction to browser actions
# 2. Execute them step by step
# 3. Learn from errors and retry automatically
# 4. Remember successful patterns for future use
```

### Basic Web Automation (Code)
```python
from src.automation import BrowserEngine, TaskExecutor
from src.automation.config import BrowserConfig, AutomationConfig

browser = BrowserEngine(BrowserConfig(), AutomationConfig())
executor = TaskExecutor(browser)

await browser.start()
await browser.navigate("https://any-website.com")
headings = await browser.get_all_text("h1, h2, h3")
links = await browser.get_all_text("a")
await browser.stop()
```

### AI Code Generation
```python
from src.automation import AITaskGenerator

generator = AITaskGenerator()
code = await generator.generate_playwright_code("Navigate to any website and extract all headings")
```

### Custom Automation (Any Website)
```python
browser = BrowserEngine()
await browser.start()
await browser.navigate("https://any-site.com")
await browser.fill("input[name='email']", "user@example.com")
await browser.click("button.submit")
data = await browser.get_all_text(".data-item")
await browser.stop()
```

## Environment Variables

Set environment variables using Replit Secrets:
- `OPENAI_API_KEY` - Optional, required only for AI code generation features
- Other settings can be configured via BrowserConfig and AutomationConfig classes

## Known Limitations in Replit

- Playwright browser automation requires system dependencies that may need manual installation in cloud environments
- The framework code is fully functional, but actual browser execution may require additional setup
- All features work correctly in local development environments with Playwright dependencies installed
- AI code generation works if OPENAI_API_KEY is provided

## Project Structure
```
.
├── src/
│   └── automation/
│       ├── __init__.py
│       ├── browser_engine.py
│       ├── selectors.py
│       ├── task_executor.py
│       ├── ai_generator.py
│       ├── config.py
│       └── logger.py
├── examples/
│   ├── web_scraping_example.py
│   ├── form_filling_example.py
│   ├── ai_code_generation_example.py
│   └── advanced_automation_example.py
├── main.py
├── README.md
└── replit.md
```

## User Preferences
- Prefers comprehensive, production-ready solutions
- Values robust error handling and logging
- Wants flexibility for any automation use case
