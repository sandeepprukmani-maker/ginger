# Playwright MCP Server

## Overview
This is the **Playwright MCP (Model Context Protocol)** server - a tool that provides browser automation capabilities for LLMs and AI assistants. It enables AI to interact with web pages through structured accessibility snapshots, without requiring screenshots or vision models.

**Last Updated**: October 15, 2025

## Project Type
- **Primary**: CLI tool and Node.js library
- **Secondary**: Chrome/Edge browser extension (optional)

## Key Features
- Fast and lightweight browser automation using Playwright's accessibility tree
- LLM-friendly structured data (no vision models needed)
- Deterministic tool application
- Can run as MCP server via stdio or HTTP transport
- Optional browser extension for connecting to existing browser tabs

## Project Structure
```
.
├── cli.js                  # Main CLI entry point
├── index.js                # Library entry point (exports createConnection)
├── package.json            # Main project dependencies
├── extension/              # Browser extension (React + Vite)
│   ├── src/
│   │   ├── ui/            # React UI components
│   │   └── background.ts  # Extension background script
│   ├── dist/              # Built extension (generated)
│   └── package.json       # Extension dependencies
└── tests/                 # Playwright tests

```

## Dependencies
- **Runtime**: Node.js 18+
- **Main**: playwright, playwright-core
- **Dev**: @playwright/test, @modelcontextprotocol/sdk
- **Extension**: React, Vite, TypeScript

## Setup on Replit
The project has been set up with all dependencies installed:
- Main project dependencies installed via `npm install`
- Extension dependencies installed via `npm install` in extension/
- Extension built and ready in `extension/dist/`

## Running the Project

### As MCP Server (HTTP Mode) - Active Workflow
The MCP server is currently running in HTTP mode on port 8080:
```bash
node cli.js --headless --browser chromium --port 8080 --host 0.0.0.0
```

The server is accessible at:
- **MCP Endpoint**: `http://localhost:8080/mcp`
- **SSE Endpoint**: `http://localhost:8080/sse` (legacy)

This allows MCP clients to connect via HTTP transport instead of stdio.

### As CLI Tool
The primary use case is as a CLI tool invoked by MCP clients:
```bash
npx @playwright/mcp@latest [options]
```

### Available Commands
- `npm test` - Run Playwright tests
- `npm run ctest` - Run Chrome tests only
- `npm run lint` - Update README

### Extension Build
- `cd extension && npm run build` - Build browser extension
- `cd extension && npm run watch` - Watch mode for development

## Configuration
The server supports extensive configuration via CLI arguments or config file:
- `--browser`: Browser type (chrome, firefox, webkit, msedge)
- `--headless`: Run in headless mode
- `--port`: Enable HTTP transport on specified port
- `--host`: Bind server to host (default: localhost)
- `--config`: Path to JSON configuration file
- See `node cli.js --help` for full options

## Usage in MCP Clients
Configure in MCP clients (VS Code, Claude Desktop, etc.):
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

## Browser Extension
The Chrome/Edge extension is located in `extension/dist/` after building. It allows connecting the MCP server to existing browser tabs with your logged-in sessions.

Installation:
1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select `extension/dist/` directory

## Development Notes
- This is primarily a **CLI tool**, not a web application
- The HTTP server mode (with --port) is mainly for standalone deployments
- Tests use Playwright Test framework
- Extension uses Vite for building React components

## Testing the Server
You can test the MCP server is running:
```bash
curl http://localhost:8080/mcp
# Should return "Invalid request" (expected for simple GET)
```

For MCP clients to connect, they need to use the JSON-RPC protocol over HTTP.

## Browser Automation Web App

A new web application has been built on top of Playwright MCP that allows you to control browsers using natural language!

### What It Does
- Type commands in plain English (no coding, no locators needed)
- AI (GPT-4) interprets your commands
- Browser automatically executes the tasks
- See step-by-step results in real-time

### Architecture
```
User (Browser) 
    ↓ (natural language command)
Frontend (port 5000) 
    ↓ (HTTP API)
Backend Server (app/server.js)
    ↓ (OpenAI API - interprets command)
    ↓ (MCP protocol)
MCP Server (port 8080)
    ↓ (Playwright automation)
Chromium Browser (headless)
```

### Files Added
- `app/server.js` - Express backend that connects OpenAI + MCP
- `app/public/index.html` - Beautiful UI for entering commands
- `start.sh` - Startup script that runs both servers

### Example Commands
- "Go to Google and search for artificial intelligence"
- "Navigate to GitHub and search for playwright"
- "Open news.ycombinator.com and show me the top story"
- "Go to Wikipedia and search for quantum computing"

### How to Use
1. Open the Replit preview (port 5000)
2. Type a command in plain English
3. Click "Execute Automation"
4. Watch the AI control the browser for you!

## Recent Changes
- October 15, 2025: Initial Replit setup
  - Installed all dependencies for main project and browser extension
  - Built browser extension (available in `extension/dist/`)
  - Created Browser Automation Web App with OpenAI integration
  - Configured workflow running both MCP server (8080) and web app (5000)
  - App accessible at the Replit preview URL
