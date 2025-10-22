# AI Browser Automation Agent

## Overview
This is an AI-powered browser automation application that uses OpenAI GPT-4o-mini and Playwright to automate web tasks through natural language instructions. The project consists of:

1. **Flask Web Application** (OpenAIWeb/playwright_mcp/) - A web-based interface for browser automation
2. **CLI Tool** (OpenAIWeb/OpenAIWeb/) - A command-line interface for browser automation

The web application is the primary user-facing component, providing an intuitive interface to give instructions to an AI agent that can browse websites, click elements, fill forms, and perform other browser tasks.

## Project Architecture

### Frontend (Flask Web App)
- **Location**: `OpenAIWeb/playwright_mcp/`
- **Framework**: Flask (Python)
- **Port**: 5000
- **Features**:
  - Web UI for entering browser automation instructions
  - **Dual-engine selection**: Choose between browser-use, Playwright MCP, or auto (with fallback)
  - **Headless/Headful mode toggle**: Run browser visibly or invisibly
  - **Automatic fallback**: browser-use → Playwright MCP on failure
  - Real-time execution results with engine metadata
  - Export functionality to generate Playwright code (Python/JavaScript)
  - Health check endpoint

### Backend Components
- **Engine Manager**: Orchestrates engine selection and fallback logic (`server/services/engine_manager.py`)
- **Browser-use Adapter**: Direct integration with browser-use library (`server/services/browser_use_engine.py`)
- **MCP Adapter**: Integration with Playwright MCP server (`server/services/mcp_engine.py`)
- **MCP Server**: Node.js-based Playwright MCP server (`mcp/`)
- **OpenAI Integration**: Uses GPT-4o-mini for natural language understanding

## Recent Changes (October 22, 2025)

### Dual-Engine Architecture Implementation
1. **New UI with Engine Selection**: Added dropdown to choose between:
   - Auto mode (browser-use with MCP fallback)
   - Browser-use only
   - Playwright MCP only
2. **Headless/Headful Toggle**: Users can now run browser in visible mode for debugging
3. **Engine Manager Service**: Orchestrates execution with automatic fallback logic
4. **Modular Adapters**: 
   - BrowserUseAutomationEngine: Wraps browser-use library
   - MCPAutomationEngine: Wraps Playwright MCP server
5. **Priority System**: browser-use runs first, automatically falls back to MCP on failure
6. **Enhanced Results Display**: Shows which engine executed the task and if fallback occurred

### Initial Replit Setup
1. Removed hardcoded OpenAI API key from code (security fix)
2. Installed Python 3.11 and Node.js dependencies
3. Installed Playwright browsers (Chromium) and system dependencies
4. Created .gitignore to prevent committing secrets
5. Configured Flask app to run on port 5000 with 0.0.0.0 host (Replit-compatible)
6. Set up workflow for Flask application
7. Configured VM deployment for production (required for browser automation)
8. Verified application is working correctly

## User Preferences
- None specified yet

## Dependencies

### Python Packages
- flask (web framework)
- openai (AI integration)
- playwright (browser automation)
- requests, sseclient-py (HTTP communication)
- browser-use (AI browser automation library)
- langchain-openai (AI integration)
- python-dotenv (environment variable management)

### Node.js Packages
- @playwright/mcp (Playwright MCP server)
- playwright, playwright-core (browser automation)
- @modelcontextprotocol/sdk (MCP SDK)

### System Dependencies
- Chromium browser with required system libraries
- X11, Mesa, Pango, Cairo, and other graphics libraries

## Environment Variables
- `OPENAI_API_KEY`: Required for AI functionality (stored in Replit Secrets)

## How to Use

### Web Interface
1. The application runs automatically at port 5000
2. Enter a natural language instruction (e.g., "Go to google.com and search for Playwright MCP")
3. Click "Execute" to run the automation
4. View results in the right panel
5. Optionally export the automation as Playwright code

### CLI Tool
Located in `OpenAIWeb/OpenAIWeb/main.py`:
```bash
python OpenAIWeb/OpenAIWeb/main.py "your instruction here"
```

## Deployment
- **Type**: VM deployment (always-on)
- **Reason**: Browser automation requires persistent processes and state management
- **Command**: `python OpenAIWeb/playwright_mcp/main.py`

## Notes
- The application uses Playwright in headless mode for browser automation
- MCP server is initialized lazily on first use to optimize startup time
- Flask development server is used (consider production WSGI server for heavy loads)
