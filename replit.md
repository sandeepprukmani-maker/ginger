# AI Browser Automation Agent

## Overview
This is an AI-powered browser automation agent that combines OpenAI's GPT-4o-mini with Playwright's Model Context Protocol (MCP) server to enable natural language browser automation. Users can give instructions in plain English, and the AI will execute complex browser actions like navigation, clicking, form filling, and data extraction.

## Architecture
- **Frontend**: Flask web application (Python) serving a clean, modern UI
- **Backend**: 
  - Python Flask server on port 5000
  - OpenAI API integration for natural language understanding
  - MCP STDIO Client for communication with Playwright
- **Browser Automation**: Playwright MCP Server (Node.js) running as a subprocess
  - Uses Chromium browser in headless mode
  - Communicates via JSON-RPC over stdio

## Project Structure
```
.
├── app/
│   ├── __init__.py
│   ├── web_app.py           # Flask routes and application
│   ├── browser_agent.py     # OpenAI agent logic
│   ├── mcp_stdio_client.py  # MCP client for Playwright
│   ├── templates/
│   │   └── index.html       # Web UI
│   └── static/
│       ├── css/style.css    # Styling
│       └── js/app.js        # Frontend JavaScript
├── main.py                  # Application entry point
├── cli.js                   # Playwright MCP server entry point
├── config.ini               # Configuration file
├── package.json             # Node.js dependencies
└── pyproject.toml          # Python dependencies
```

## Configuration
- **OpenAI API Key**: Set via `OPENAI_API_KEY` environment secret
- **Model**: gpt-4o-mini (configurable in config.ini)
- **Browser**: Chromium in headless mode
- **Server**: Runs on 0.0.0.0:5000

## Recent Changes
- 2025-10-20: Initial Replit setup & Export Feature
  - Installed Python dependencies via uv
  - Installed Node.js dependencies via npm
  - Installed Playwright Chromium browser
  - Configured environment to use OPENAI_API_KEY secret
  - Set up Flask workflow on port 5000
  - Configured deployment for VM (stateful, always-running)
  - Created .gitignore for Python/Node projects
  - Added Playwright export feature:
    - Export executed actions as Playwright test code (.spec.ts)
    - Export as JSON for programmatic replay
    - Faster execution without AI/MCP overhead

## Dependencies
**Python** (via uv):
- flask
- openai
- requests
- sseclient-py

**Node.js** (via npm):
- playwright
- playwright-core
- @modelcontextprotocol/sdk
- @playwright/test

## API Endpoints
- `GET /` - Web interface
- `POST /api/execute` - Execute browser automation instruction
- `GET /api/tools` - List available browser tools
- `POST /api/reset` - Reset agent conversation history
- `POST /api/export-playwright` - Export last execution as Playwright code
- `GET /health` - Health check endpoint

## How It Works
1. User enters a natural language instruction in the web UI
2. Flask server receives the instruction
3. BrowserAgent uses OpenAI to interpret the instruction
4. OpenAI decides which browser tools to call (navigate, click, fill, etc.)
5. MCPStdioClient spawns a Node.js subprocess running Playwright MCP
6. Playwright executes the browser actions
7. Results are streamed back to the UI in real-time

## Environment Variables
- `OPENAI_API_KEY` (required): Your OpenAI API key
- `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS`: Set to '1' to skip browser dependency checks

## Deployment Notes
- Deployed as a **VM** (always-running, stateful) because:
  - The MCP subprocess needs to maintain state
  - Browser sessions are persistent
  - Immediate response time is important
- The application runs on port 5000 (only non-firewalled port in Replit)
- Uses development Flask server (suitable for Replit environment)

## Export Feature

📖 **See EXPORT_GUIDE.md for complete documentation**

After successfully executing an instruction, an "Export as Playwright" button appears. This allows you to:

1. **Export as Playwright Test Code**: 
   - Generates a `.spec.ts` file with Playwright test code
   - Ready to use in your own Playwright test suite
   - Includes all successful actions (navigate, click, fill, etc.)
   - Download or copy to clipboard

2. **Export as JSON**:
   - Contains all steps with their arguments and results
   - Can be used for programmatic replay
   - Includes timestamp and original instruction

### Workflow: Record Once, Replay Fast

1. **Record (Slow)**: Use AI to figure out the automation steps
   - Example: "Go to example.com and click the login button"
   - AI navigates, finds elements, performs actions
   - Takes 10-20 seconds due to AI reasoning

2. **Export**: Click "Export as Playwright" button
   - Download the generated Playwright code
   - Or copy the JSON for programmatic use

3. **Replay (Fast)**: Run the exported code directly
   - No AI overhead
   - No MCP communication delays
   - Runs in < 1 second

This is perfect for:
- Creating test suites from manual exploration
- Automating repetitive tasks
- Learning Playwright syntax from AI-generated examples

## Known Limitations
- MCP subprocess communication requires process persistence (hence VM deployment)
- Browser runs in headless mode (no GUI visible to user)
- Maximum 10 iterations per instruction to prevent infinite loops
- Exported Playwright code may need selector refinement for dynamic content
