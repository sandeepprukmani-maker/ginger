# Playwright MCP Server - Replit Setup

## Overview

This is **Playwright MCP** - a Model Context Protocol (MCP) server that provides browser automation capabilities using [Playwright](https://playwright.dev). This server enables Large Language Models (LLMs) to interact with web pages through structured accessibility snapshots, bypassing the need for screenshots or visually-tuned models.

### Key Features
- **Fast and lightweight**: Uses Playwright's accessibility tree, not pixel-based input
- **LLM-friendly**: No vision models needed, operates purely on structured data
- **Deterministic tool application**: Avoids ambiguity common with screenshot-based approaches

## Project Type

This is a **CLI tool/library** that runs as an MCP server. It's not a traditional web application but rather a protocol server that enables browser automation for AI assistants.

## Project Structure

```
├── cli.js                    # Main CLI entry point for MCP server
├── index.js                  # Library entry point (exports createConnection)
├── package.json              # Node.js dependencies
├── browser_automation.py     # Python client for browser automation
├── PYTHON_USAGE.md           # Python usage documentation
├── extension/                # Browser extension (Chrome/Edge)
│   ├── src/                 # Extension source code
│   ├── package.json         # Extension dependencies
│   └── vite.config.mts      # Extension build configuration
├── tests/                   # Test files
└── src/                     # Source files
```

## Current Setup in Replit

### Workflow Configuration
- **MCP Server**: Runs on port 8080 as a standalone HTTP server
  - Command: `node cli.js --port 8080 --headless --browser chromium --no-sandbox`
  - The server listens for MCP connections via HTTP
  - Access endpoint: `http://localhost:8080/mcp`

### Dependencies Installed
- Main project: All npm dependencies installed
- Extension: All npm dependencies installed (includes React, Vite, TypeScript)

## How to Use

### Running the MCP Server

The server is configured to run automatically via the workflow. You can connect to it using any MCP client with this configuration:

```json
{
  "mcpServers": {
    "playwright": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### CLI Options

The server supports numerous options (run `node cli.js --help` for full list):
- `--port <port>`: Port to listen on for HTTP transport
- `--headless`: Run browser in headless mode
- `--browser <browser>`: Browser to use (chromium, firefox, webkit)
- `--no-sandbox`: Disable sandbox (required in containerized environments like Replit)
- `--isolated`: Keep browser profile in memory
- `--user-data-dir <path>`: Custom user data directory

### Browser Extension

The project includes a Chrome/Edge browser extension in the `extension/` directory. To build it:

```bash
cd extension
npm run build
```

The built extension will be in `extension/dist/`.

### Python Browser Automation (NEW! ✨)

A Python client is now available that lets you automate browser interactions using **natural language prompts**. No need to provide locators - the DOM is automatically scanned!

#### Quick Start

1. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```
   
   Get your API key from: https://platform.openai.com/

2. **Run automation with a prompt**:
   ```bash
   # Command line usage
   python browser_automation.py "Go to google.com and search for Python"
   
   # Interactive mode
   python browser_automation.py
   ```

#### What It Does

- **Accepts natural language prompts**: Just describe what you want in plain English
- **Automatic DOM scanning**: No need to provide CSS selectors or XPath
- **Uses GPT-4o-mini**: OpenAI's AI converts your prompt into browser actions
- **Returns rerunnable code**: Generates a standalone Python script (`automation_script.py`)

#### Example Prompts

```bash
# Simple navigation
python browser_automation.py "Navigate to github.com"

# Search workflow
python browser_automation.py "Go to google.com and search for 'Playwright MCP'"

# Form filling
python browser_automation.py "Go to example.com/login and fill username with test@example.com"

# Complex automation
python browser_automation.py "Navigate to github.com, search for 'playwright', and click the first result"
```

#### Key Features

- ✅ **No locators required** - Automatic element detection
- ✅ **Natural language interface** - Describe actions in plain English
- ✅ **DOM scanning** - Uses Playwright's accessibility tree
- ✅ **Rerunnable scripts** - Every automation generates a standalone Python script
- ✅ **Real-time execution** - See each step as it happens

#### Output

The script generates:
1. **Console output** - Shows real-time execution
2. **Rerunnable script** (`automation_script.py`) - Standalone Python file you can run again

See [PYTHON_USAGE.md](PYTHON_USAGE.md) for complete documentation and examples.

## Development

### Running Tests
```bash
npm test                 # Run all tests
npm run ctest           # Chrome tests
npm run ftest           # Firefox tests
npm run wtest           # WebKit tests
```

### Building the Extension
```bash
cd extension
npm run build           # Production build
npm run watch           # Development mode with auto-rebuild
```

## Technical Notes

### Replit-Specific Configuration
- The server runs with `--no-sandbox` flag (required for Chromium in containerized environments)
- Uses headless mode for browser automation
- HTTP transport enabled via `--port` option for easier client connections

### MCP Protocol
This server implements the Model Context Protocol (MCP), which provides:
- Browser automation tools (click, fill, navigate, etc.)
- Accessibility tree snapshots
- JavaScript evaluation
- Console message access
- File upload handling
- And many more browser interaction capabilities

## Recent Changes

### Python Automation Client Added (October 16, 2025)
- Created `browser_automation.py` - Python client for natural language browser automation
- Installed Python 3.11 and required packages (mcp, httpx, openai)
- Uses GPT-4o-mini for AI-powered prompt interpretation
- Added automatic DOM scanning capability - no locators needed
- Implemented code generation for rerunnable automation scripts
- Created comprehensive documentation in `PYTHON_USAGE.md`

### Initial Setup (October 16, 2025)
- Installed all project dependencies (Node.js and Python)
- Configured MCP server workflow on port 8080
- Set up for headless browser automation
- Verified server runs successfully in Replit environment

## Resources

- [Playwright Documentation](https://playwright.dev)
- [MCP Protocol](https://modelcontextprotocol.io)
- [GitHub Repository](https://github.com/microsoft/playwright-mcp)

## User Preferences

None configured yet.
