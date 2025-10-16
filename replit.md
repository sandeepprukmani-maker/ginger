# Playwright Automation Generator

## Overview

This project combines the **Playwright MCP** (Model Context Protocol) server with a Python web application that converts natural language descriptions into executable Playwright automation code. Users can describe UI automation tasks in plain English, and the application generates ready-to-run Playwright Python code.

**Project Type:** Web Application with MCP Integration  
**Primary Languages:** Python (Flask), Node.js / TypeScript  
**Main Components:**
- Python Flask Web Application (frontend UI for natural language input)
- MCP Server (browser automation backend)
- OpenAI GPT-5 Integration (natural language processing)
- Chrome Browser Extension (optional, for connecting to existing browser sessions)

## Current State

The project is fully set up and running:
- ✅ Python Flask web application running on port 5000
- ✅ OpenAI GPT-5 integration configured
- ✅ All npm and Python dependencies installed
- ✅ Playwright browsers installed (Chromium, Firefox, WebKit)
- ✅ Chrome extension built and ready
- ✅ MCP Server managed by Python application

## Recent Changes

**2025-10-16:** Complete application development
- Created Python Flask web application with modern UI
- Integrated OpenAI GPT-5 for natural language interpretation
- Implemented MCP server management from Python
- Built natural language to Playwright code conversion
- Configured workflow to run web app on port 5000
- Added server start/stop controls in the UI

## Project Architecture

### Main Components

1. **Python Flask Web Application** (`app.py`, `templates/index.html`)
   - Main web interface for the automation generator
   - Accepts natural language input from users
   - Converts input to Playwright code using OpenAI GPT-5
   - Manages the MCP server lifecycle (start/stop)
   - Provides REST API endpoints for code generation
   - Running on port 5000

2. **MCP Server** (`cli.js`, `index.js`)
   - Playwright MCP server for browser automation
   - Supports both stdio (default) and HTTP/SSE transport modes
   - Managed by the Python application
   - Runs on port 8080 when started

3. **Chrome Extension** (`extension/`)
   - Optional browser extension for connecting to existing browser tabs
   - Built with React and TypeScript
   - Compiled output in `extension/dist/`
   - Allows using logged-in browser sessions

4. **Tests** (`tests/`)
   - Playwright-based test suite
   - Test server located in `tests/testserver/`

### Key Files

- `app.py` - Main Flask application with OpenAI integration
- `templates/index.html` - Web UI for natural language input
- `cli.js` - CLI entry point for the MCP server
- `index.js` - Programmatic API entry point
- `package.json` - Node.js project dependencies
- `pyproject.toml` - Python project dependencies
- `extension/` - Browser extension source and build files

## Running the Project

### Web Application

The web application is the primary interface and runs automatically:

**Workflow Name:** Web App  
**Command:** `python app.py`  
**Port:** 5000  
**URL:** Open the webview in Replit to access the application

### How to Use

1. **Open the Web Application** - The app runs automatically on port 5000
2. **Describe Your Task** - Enter a natural language description of your automation task:
   - Example: "Go to example.com, click the login button, fill in username and password, then submit"
3. **Generate Code** - Click "Generate Playwright Code" to convert your description to executable Python code
4. **Start MCP Server** (Optional) - Click "Start MCP Server" if you need the MCP server running
5. **Copy and Use** - Copy the generated code and run it in your own environment

### API Endpoints

The Flask application provides the following REST API endpoints:

- `GET /` - Main web interface
- `POST /api/interpret` - Convert natural language to Playwright code
  - Request: `{"input": "your automation description"}`
  - Response: `{"playwright_code": "...", "explanation": "...", "actions": [...]}`
- `POST /api/server/start` - Start the MCP server
- `POST /api/server/stop` - Stop the MCP server
- `GET /api/server/status` - Check MCP server status

### Available Commands

```bash
# Run the web application (main entry point)
python app.py

# Run MCP server manually (usually managed by Python app)
node cli.js --headless --port 8080 --host localhost

# Run tests
npm test

# Build Chrome extension
cd extension && npm run build
```

### Chrome Extension

The extension is built and ready in `extension/dist/`. To use it:

1. Open Chrome/Edge browser
2. Navigate to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked" and select the `extension/dist/` directory
5. Configure MCP server with `--extension` flag

## Development Notes

- Node.js version: 18+ required
- The server uses Playwright's accessibility tree for page interaction
- Extension UI is built with React and bundled with Vite
- All Playwright browsers (Chromium, Firefox, WebKit) are installed and ready

## Features

- 🎯 **Natural Language Input** - Describe automation tasks in plain English
- 🤖 **AI-Powered Code Generation** - Uses OpenAI GPT-5 to generate Playwright code
- 🎭 **Playwright Integration** - Generates executable Playwright Python code
- 🔄 **MCP Server Management** - Start/stop the Playwright MCP server from the UI
- 📋 **Copy to Clipboard** - Easy code copying for immediate use
- 🎨 **Modern UI** - Beautiful, responsive interface with gradient design
- ⚡ **Real-time Status** - Live server status monitoring

## Dependencies

**Python:**
- flask - Web framework
- openai - OpenAI API integration (GPT-5)
- requests - HTTP library

**Node.js:**
- playwright: ^1.57.0
- playwright-core: ^1.57.0
- @modelcontextprotocol/sdk: ^1.17.5
- @playwright/test: ^1.57.0

**Extension:**
- react: ^18.2.0
- react-dom: ^18.2.0
- vite: ^5.4.20
- typescript: ^5.8.2

## Environment Variables

- `OPENAI_API_KEY` - Required for natural language processing

## Resources

- **Original GitHub Repository:** https://github.com/microsoft/playwright-mcp
- **Playwright Documentation:** https://playwright.dev
- **MCP Protocol:** https://modelcontextprotocol.io
- **OpenAI API:** https://platform.openai.com
