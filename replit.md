# AI Browser Automation Agent

## Project Overview

This is a **Python web application** that combines OpenAI GPT-5 with Playwright MCP (Model Context Protocol) to create an intelligent browser automation agent. Users can input natural language instructions, and the AI agent will autonomously perform browser actions to complete the task.

**Project Type:** Flask Web Application + AI Agent
**Created:** October 20, 2025

## Key Features

- Natural language browser automation powered by OpenAI GPT-5
- Intelligent task interpretation and execution using AI function calling
- Real-time browser control via Playwright MCP
- Beautiful, responsive web interface
- Step-by-step execution tracking with detailed results
- Supports navigation, clicking, form filling, and page analysis

## Architecture

### Components

1. **Flask Web App** (`app/web_app.py`)
   - Web server providing REST API and user interface
   - Endpoints for instruction execution, tools listing, and health checks
   - Lazy initialization of MCP client for efficiency

2. **MCP STDIO Client** (`app/mcp_stdio_client.py`)
   - Communicates with Playwright MCP server via subprocess
   - Uses JSON-RPC over STDIO transport for stateful sessions
   - Manages browser lifecycle and tool invocations

3. **Browser Agent** (`app/browser_agent.py`)
   - OpenAI GPT-5 powered intelligent agent
   - Interprets natural language instructions
   - Uses function calling to execute browser automation tools
   - Iterative execution with feedback loops

4. **Playwright MCP Server** (`cli.js`)
   - Node.js-based browser automation server
   - Launched as subprocess by the Python client
   - Provides structured browser interaction tools

### Technology Stack

**Backend:**
- Python 3.11
- Flask (web framework)
- OpenAI Python SDK (GPT-5 API)
- Requests (HTTP client)

**Browser Automation:**
- Playwright MCP Server (Node.js)
- Model Context Protocol (STDIO transport)
- Chromium browser (headless mode)

**Frontend:**
- HTML5 + CSS3
- Vanilla JavaScript (no frameworks)
- Responsive design with gradient UI

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── web_app.py              # Flask application
│   ├── mcp_stdio_client.py     # MCP client (STDIO transport)
│   ├── mcp_client.py           # HTTP client (legacy, not used)
│   ├── browser_agent.py        # OpenAI agent
│   ├── templates/
│   │   └── index.html          # Web interface
│   └── static/
│       ├── css/style.css       # Stylesheet
│       └── js/app.js           # Frontend JavaScript
├── main.py                     # Application entry point
├── cli.js                      # Playwright MCP server
├── package.json                # Node.js dependencies for MCP
├── pyproject.toml              # Python dependencies
└── replit.md                   # This file

```

## How It Works

1. **User Input:** User enters a natural language instruction (e.g., "Go to google.com and search for 'AI'")
2. **AI Processing:** OpenAI GPT-5 interprets the instruction and breaks it into browser automation steps
3. **Tool Execution:** The agent calls Playwright MCP tools (navigate, click, fill, etc.) via function calling
4. **Feedback Loop:** After each action, the agent receives page state and decides next steps
5. **Results Display:** All steps and results are shown in real-time on the web interface

## Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for GPT-5 access (required)

## Usage

### Starting the Application

The application runs automatically on Replit. The Flask server starts on port 5000 and launches the Playwright MCP server as a subprocess.

### Example Instructions

- "Go to example.com"
- "Navigate to github.com and find trending repositories"  
- "Open google.com and search for 'Playwright MCP'"
- "Visit example.com and get the page title"

### API Endpoints

- `GET /` - Web interface
- `POST /api/execute` - Execute an instruction
- `GET /api/tools` - List available browser tools
- `POST /api/reset` - Reset agent conversation
- `GET /health` - Health check endpoint

## Available Browser Tools

The Playwright MCP server provides these tools:

- `browser_navigate` - Navigate to a URL
- `browser_click` - Click an element on the page
- `browser_fill` - Fill form fields with text
- `browser_snapshot` - Get page accessibility tree
- `browser_close` - Close the browser
- And many more...

## Technical Notes

### Transport Protocol

This project uses **STDIO transport** instead of HTTP transport because:
- HTTP transport in Playwright MCP is stateless (each request is independent)
- STDIO maintains session state across multiple tool calls
- Subprocess communication ensures reliable browser context preservation

### AI Agent Design

The browser agent uses OpenAI's function calling feature:
1. System prompt defines the agent's role and capabilities
2. Available tools are formatted as OpenAI function schemas
3. GPT-5 decides which tools to call based on the instruction
4. Agent executes tools and provides results back to GPT-5
5. Process repeats until task is complete (max 10 iterations)

### Error Handling

- Graceful degradation when MCP server is unavailable
- Tool execution errors are captured and reported to the AI
- User-friendly error messages in the web interface
- Health check endpoint for monitoring

## Development Notes

- The MCP client spawns a new Playwright subprocess for each web session
- Browser runs in headless mode for server environments
- Lazy initialization prevents unnecessary resource usage
- CORS and security headers should be added for production use

## Deployment

Configured for Replit Autoscale deployment:
- Deployment target: `autoscale` (stateless web application)
- Run command: `python main.py`
- Port: 5000 (exposed via web interface)

## Known Limitations

1. **Single User:** One browser session per application instance
2. **No Persistence:** Browser state is lost when the app restarts
3. **Resource Intensive:** Running browsers requires significant memory
4. **Rate Limits:** Subject to OpenAI API rate limits and costs

## Future Enhancements

- Multi-user support with session management
- Persistent browser profiles and cookies
- Screenshot and PDF generation capabilities
- Integration with more AI providers
- Advanced debugging and logging features
- Browser extension support for non-headless mode

## Credits

- Built on Replit platform
- Uses Microsoft Playwright MCP Server
- Powered by OpenAI GPT-5
- Created as a demonstration of AI-powered browser automation
