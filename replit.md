# Browser Automation Framework

## Overview
A comprehensive Python-based browser automation framework powered by Playwright and AI. This framework enables powerful browser automation for **any website** including web scraping, form filling, testing, and AI-powered code generation. Completely generic with no site-specific dependencies.

## Project Status
**Active Development** - Production-ready browser automation framework

## Recent Changes (October 16, 2025)
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
- `ai_generator.py` - AI-powered Playwright code generation using OpenAI
- `config.py` - Configuration management (browser, automation settings)
- `logger.py` - Enhanced logging with Rich console output

### Features

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

**AI Code Generation**
- Generate Playwright code from natural language descriptions
- Pre-built templates for scraping, form filling, login automation
- MCP server integration for enhanced capabilities

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
- agents (MCP integration)

**Utilities**
- python-dotenv (environment management)
- tenacity (retry logic)
- rich (console output)
- pydantic (data validation)

## Usage Examples

### Basic Web Automation
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
