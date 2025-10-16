# Overview

This is a Playwright MCP (Model Context Protocol) server implementation that enables AI agents to control and automate web browsers through the MCP protocol. The project serves as a bridge between AI models (particularly OpenAI) and Playwright browser automation, allowing natural language commands to be translated into browser actions. It can be run as a command-line tool or through a web interface.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Components

**MCP Server (Node.js/TypeScript)**
- Full Model Context Protocol implementation using `@modelcontextprotocol/sdk`
- Stdio-based JSON-RPC transport for communication with MCP clients
- Session manager for Playwright browser lifecycle (Chromium headless)
- 8 MCP tools: health_check, navigate, click, fill, get_text, get_all_text, screenshot, plan_and_execute
- Located in `/mcp-server` directory with TypeScript source and compiled build
- Can be used with Claude Desktop, Python clients, or any MCP-compatible client

**Automation Tools**
- `playwright_navigate`: Navigate to URLs with networkidle wait
- `playwright_click`: Click elements using CSS, text (text=Button), or role selectors
- `playwright_fill`: Fill text into input fields
- `playwright_get_text`: Extract text from single element
- `playwright_get_all_text`: Extract text from multiple matching elements
- `playwright_screenshot`: Capture page screenshots (supports fullPage option)
- `playwright_plan_and_execute`: AI-powered automation planning and execution

**AI Planning Engine**
- OpenAI GPT-4 integration for natural language to automation translation
- Fallback heuristic-based planning when OpenAI API key not available
- Analyzes user prompts and generates executable Playwright action sequences
- Supports complex multi-step automations from simple descriptions

**Web Interface Layer**
- Flask-based web UI (`web_ui_mcp.py`) with MCP client integration
- Python MCP client (`mcp_client.py`) communicates with Node MCP server via subprocess stdio
- Persistent event loop in separate thread for async MCP communication
- JSON-RPC request/response handling for tool invocation
- Real-time automation execution with results streaming

## Technology Stack

**MCP Server (Node.js)**
- Node.js 18+ runtime
- TypeScript for type-safe development
- `@modelcontextprotocol/sdk` for MCP protocol
- Playwright 1.57.0-alpha for browser automation
- OpenAI SDK for AI planning
- Zod for parameter validation

**Web UI (Python)**
- Python 3.11 with asyncio
- Flask web framework
- Custom MCP client for stdio communication
- Subprocess management for MCP server lifecycle

**Browser Automation**
- Playwright Chromium (headless mode)
- Supports CSS selectors, text selectors (text=), and role-based selectors
- Screenshot capture with base64 encoding
- Network idle detection for page loads

# External Dependencies

**Node.js Dependencies**
- `@modelcontextprotocol/sdk` (1.0.4+): MCP protocol implementation
- `playwright` (1.57.0-alpha): Browser automation framework
- `openai` (4.80.0+): AI-powered automation planning
- `zod` (3.24.2+): Runtime type validation
- `typescript` (5.7.3+): TypeScript compiler

**Python Dependencies**
- `flask` (3.1.2+): Web server for UI
- `openai` (2.3.0+): Python OpenAI client (legacy engine)
- `playwright` (1.55.0+): Python Playwright for legacy engine
- `requests` (2.32.5+): HTTP client

**System Dependencies**
- Chromium browser binaries (via Playwright)
- System libraries: alsa-lib, at-spi2-atk, cups, libdrm, mesa, nspr, nss, pango, xorg libraries

**Configuration Files**
- `/mcp-server/package.json`: Node.js MCP server dependencies
- `/mcp-server/tsconfig.json`: TypeScript compiler configuration
- `/pyproject.toml`: Python project dependencies
- `/mcp-config-example.json`: Example Claude Desktop MCP configuration