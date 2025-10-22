# AI Browser Automation Agent

## Overview
This is a dual-engine AI browser automation system that provides two powerful automation approaches:
1. **Browser-Use Engine**: Advanced AI-powered automation using the browser-use library with LLM reasoning
2. **Playwright MCP Engine**: Tool-based automation using Playwright's Model Context Protocol

Users can switch between engines and choose headless (invisible) or headful (visible) browser modes through an intuitive web interface.

## Architecture
- **Frontend**: Modern Flask web application with dual-engine configuration
- **Backend**: 
  - Python Flask server on port 5000
  - OpenAI API integration (GPT-4o-mini)
  - Dual engine system:
    - **Browser-Use Engine**: Native browser-use integration with async execution
    - **Playwright MCP Engine**: MCP STDIO Client communicating with Playwright subprocess
- **Browser Modes**: Both headless and headful modes supported on both engines

## Project Structure
```
.
├── app/
│   ├── __init__.py
│   ├── app.py               # Flask routes and application
│   ├── browser_agent.py     # OpenAI agent logic
│   ├── mcp_stdio_client.py  # MCP client for Playwright
│   ├── templates/
│   │   └── index.html       # Web UI
│   └── static/
│       ├── css/style.css    # Styling
│       └── js/app.js        # Frontend JavaScript
├── main.py                  # Application entry point
├── cli.js                   # Playwright MCP server entry point
├── config.ini               # Configuration file (server, browser, OpenAI settings)
├── package.json             # Node.js dependencies
├── pyproject.toml           # Python dependencies (uv package manager)
└── SETUP.md                 # Setup guide for local Windows installation
```

## Configuration
- **OpenAI API Key**: Set in `config.ini` file under `[openai]` section's `api_key` field (fallback to `OPENAI_API_KEY` environment variable)
- **Model**: gpt-4o-mini (configurable in config.ini)
- **Browser**: Chromium in headless mode
- **Server**: Runs on 0.0.0.0:5000

## Recent Changes
- 2025-10-22: **Major Update - Dual Engine System with Modern UI**
  - **Dual Engine Architecture**: Added browser-use engine alongside Playwright MCP
    - Browser-Use: AI-powered automation with advanced reasoning capabilities
    - Playwright MCP: Tool-based automation with discrete browser actions
  - **Headless/Headful Modes**: Added toggle for both engines (headful is default)
  - **Redesigned UI**: Modern two-column layout with configuration panel
    - Engine selector dropdown
    - Headless mode toggle switch
    - Quick example buttons
    - Real-time status badges
    - Improved step visualization
  - **Backend Enhancements**:
    - Created browser_use_engine.py for browser-use integration
    - Updated engine caching system for both engines
    - Added mode configuration support
    - Improved health check endpoint
  - **Dependencies**: Installed browser-use, langchain-openai, and supporting libraries
  
- 2025-10-22: Removed code generation/export feature - focused on pure browser automation
  - Removed `/api/export-playwright` endpoint and all export functionality
  - Removed Playwright code generation and selector extraction functions
  - Removed export button and modal from frontend
  
- 2025-10-20: GitHub Import Setup for Replit Environment + Critical Bug Fixes
  
  **Initial Setup:**
  - Created config.ini with sections for server, browser, and OpenAI settings
  - Installed Python dependencies via uv (flask, openai, requests, sseclient-py)
  - Installed Node.js dependencies via npm (playwright, @modelcontextprotocol/sdk)
  - Installed Playwright Chromium browser with headless mode support
  - Configured Flask workflow using `python main.py` on port 5000
  - Configured VM deployment (stateful, always-running for MCP subprocess)
  - Changed port from 5002 to 5000 in main.py
  - Updated .gitignore to not exclude config.ini
  
  **Critical Bug Fixes (Post-Architect Review):**
  - **Security**: Removed hardcoded API key from browser_agent.py
  - **API Key Handling**: Updated to prioritize environment variables over config.ini for security
  - **OpenAI API Fix**: Changed `max_completion_tokens` to `max_tokens` (was causing API errors)
  - **MCP Client Fix**: Added stderr reader thread to prevent process deadlock
  - **CLI Args Fix**: Improved command-line argument handling for MCP server subprocess
  - **Error Messages**: Enhanced error messages to guide users toward secure practices
  
  **Verified**: Web interface, MCP subprocess communication, browser automation

## Dependencies
**Python** (via uv):
- flask - Web framework
- openai - OpenAI API client
- requests - HTTP library
- sseclient-py - Server-sent events
- browser-use - AI browser automation library
- langchain-openai - LangChain OpenAI integration
- python-dotenv - Environment variable management
- playwright - Browser automation (via browser-use)

**Node.js** (via npm):
- playwright - Browser automation library
- playwright-core - Core Playwright functionality
- @modelcontextprotocol/sdk - MCP protocol implementation
- @playwright/test - Playwright testing framework

## API Endpoints
- `GET /` - Web interface
- `POST /api/execute` - Execute browser automation instruction
- `GET /api/tools` - List available browser tools
- `POST /api/reset` - Reset agent conversation history
- `GET /health` - Health check endpoint

## How It Works

### Browser-Use Engine (Default)
1. User enters instruction and selects Browser-Use engine
2. Flask server creates/retrieves browser-use engine instance
3. Browser-Use Agent uses GPT-4o-mini for AI reasoning
4. Agent autonomously navigates, interacts, and completes tasks
5. Results with action history are returned to the UI

### Playwright MCP Engine
1. User enters instruction and selects Playwright MCP engine
2. Flask server creates/retrieves MCP client and browser agent
3. BrowserAgent uses OpenAI to determine browser tool calls
4. MCPStdioClient communicates with Playwright subprocess via JSON-RPC
5. Playwright executes discrete browser actions (navigate, click, fill, etc.)
6. Results are returned step-by-step to the UI

## Environment Variables
- `OPENAI_API_KEY` (optional): OpenAI API key as environment variable (fallback if not in config.ini)
- `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS`: Automatically set to '1' by MCP client to skip browser dependency checks in Replit

## How to Set Your OpenAI API Key
You have two options:

**Option 1: Using config.ini (Recommended)**
1. Open the `config.ini` file
2. Replace `YOUR_OPENAI_API_KEY_HERE` with your actual API key in the `[openai]` section:
   ```ini
   [openai]
   api_key = sk-your-actual-openai-api-key-here
   model = gpt-4o-mini
   ```

**Option 2: Using Environment Variable**
1. Add `OPENAI_API_KEY` as a Replit secret
2. The application will use it if config.ini doesn't contain a valid key

## Deployment Notes
- Deployed as a **VM** (always-running, stateful) because:
  - The MCP subprocess needs to maintain state
  - Browser sessions are persistent
  - Immediate response time is important
- The application runs on port 5000 (only non-firewalled port in Replit)
- Uses development Flask server (suitable for Replit environment)

## Features
- **Dual Engine System**: Choose between AI-powered (Browser-Use) or tool-based (Playwright MCP) automation
- **Headless/Headful Modes**: Run browser invisibly for speed or visibly for debugging
- **Natural Language Instructions**: Describe tasks in plain English
- **Real-time Feedback**: See step-by-step execution progress
- **Modern UI**: Clean two-column interface with configuration panel
- **Quick Examples**: Pre-loaded examples for common automation tasks
- **Engine Switching**: Seamlessly switch between automation engines
- **Status Badges**: Visual indicators for execution state
- **Detailed Step Logs**: View arguments and results for each automation step

## Known Limitations
- MCP subprocess communication requires process persistence (hence VM deployment)
- Browser runs in headless mode (no GUI visible to user)
- Maximum 10 iterations per instruction to prevent infinite loops
