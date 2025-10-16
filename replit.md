# Playwright MCP Server

## Project Overview
This project now contains **two integrated systems**:

1. **Playwright MCP Server** (Node.js) - Browser automation backend
2. **Python Automation System** - Natural language browser automation

The Python system uses the MCP server to provide natural language browser automation - just describe what you want, and it automatically executes the actions and generates reusable code!

## Project Type
- **Primary**: Python Browser Automation System
- **Backend**: Playwright MCP Server (Node.js)
- **Languages**: Python 3.11, Node.js, TypeScript
- **Main Components**:
  - Python Automation Engine with LLM orchestration
  - Playwright MCP Server (port 3000)
  - Browser Extension (Chrome/Edge)
  - Code generation system

## Recent Changes
- **2024-10-16**: Complete system setup
  - Installed all npm and Python dependencies
  - Built browser extension successfully
  - Configured standalone MCP server workflow on port 3000
  - Created Python automation system with natural language support
  - Integrated OpenAI GPT-5 for intelligent orchestration
  - Implemented code generation for reusable automation scripts
  - Added comprehensive error handling and user guidance

## Project Structure

### Python Automation System (Main)
- `main.py` - Command-line and interactive interface
- `automation/` - Core automation engine
  - `automation_engine.py` - Main orchestration
  - `mcp_client.py` - MCP server communication
  - `llm_orchestrator.py` - Natural language processing
- `examples.py` - Pre-built automation examples
- `test_automation.py` - System verification
- `output/` - Automation execution results
- `generated_code/` - Reusable Python scripts

### Playwright MCP Server (Backend)
- `/` - MCP server package
  - `cli.js` - CLI entry point
  - `index.js` - Programmatic API
- `/extension` - Browser extension
  - Built output in `/extension/dist`
- `/tests` - Test suite

## How to Use

### 🎯 Python Automation System (Primary Usage)

**Interactive Mode:**
```bash
python main.py
```
Then enter natural language commands like:
- `navigate to google.com and search for Playwright`
- `go to github.com and click sign in`
- `open reddit.com and extract top posts`

**Command Line:**
```bash
python main.py "go to example.com and take a snapshot"
```

**Run Examples:**
```bash
python examples.py          # All examples
python examples.py 1        # Example 1 only
```

### 🔧 MCP Server (Backend - Already Running)
The server runs on port 3000:
```bash
node cli.js --port 3000 --headless --browser chromium --no-sandbox --host 0.0.0.0
```

### 📚 Documentation
- `SETUP_COMPLETE.md` - Complete setup guide
- `README_AUTOMATION.md` - Detailed usage instructions
- `README.md` - Original MCP documentation

## Replit Setup

### Current Workflow
- **MCP Server**: Running on port 3000
  - Command: `node cli.js --port 3000 --headless --browser chromium --no-sandbox --host 0.0.0.0`
  - Access: This is a backend MCP server, not a web UI
  - Purpose: Provides browser automation capabilities via MCP protocol

### Limitations in Replit
- Full Playwright browser testing requires system dependencies not available via Nix
- The server runs in headless mode with `--no-sandbox` flag
- This is a CLI tool/library package, not a deployable web application

## Development Notes
- Node.js 18+ required
- Playwright browsers need to be installed (not available in Replit environment currently)
- Tests require Playwright system dependencies
- The server is designed to be consumed by MCP clients, not run directly as a web app

## Architecture
This is a **library/CLI package**, not a traditional web application. It provides:
- MCP server functionality for browser automation
- Tools for LLMs to interact with web pages
- Browser extension for connecting to existing tabs
- Programmatic API via `createConnection()`
