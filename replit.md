# AI Browser Automation Agent

## Overview

This is a dual-engine browser automation system that allows users to automate web tasks using natural language instructions. The application provides two distinct automation approaches through a modern Flask web interface:

1. **Browser-Use Engine**: AI-powered automation using the browser-use library with LLM reasoning for autonomous, multi-step workflows
2. **Playwright MCP Engine**: Tool-based automation using Playwright's Model Context Protocol for precise, controllable browser actions

Users can switch between engines, choose headless/headful browser modes, and execute complex web automation tasks through simple English instructions via a RESTful API and web UI.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack**: Vanilla JavaScript with server-side Jinja2 templates

**Design Pattern**: Two-column responsive layout
- Left panel: Configuration controls (engine selection, headless mode toggle) and instruction input
- Right panel: Real-time execution feedback and results display
- Footer: Current engine and mode status indicators

**Communication**: RESTful API calls to Flask backend using fetch API

**Key Decision**: Chose vanilla JavaScript over frameworks to minimize dependencies and simplify deployment. The straightforward UI requirements don't justify framework overhead.

### Backend Architecture

**Framework**: Flask (Python web framework)

**Design Pattern**: Service-oriented architecture with clear separation of concerns
- Application Factory Pattern (`app/__init__.py`): Creates configured Flask instances
- Service Layer (`app/services/`): Business logic isolation
- Route Layer (`app/routes/`): API endpoint definitions
- Blueprint Pattern: Modular route organization

**Engine Orchestration**: The `EngineOrchestrator` class manages both automation engines:
- Maintains separate engine instance caches for headless/headful modes
- Delegates execution to appropriate engine based on user selection
- Handles engine lifecycle and resource management

**Thread Safety Considerations**:
- Browser-Use engine creates fresh browser instances per request to avoid asyncio event loop conflicts in Flask's multi-threaded environment
- Each request runs on its own event loop with proper cleanup
- Playwright MCP engine uses subprocess isolation for thread safety

**Key Decision**: Flask chosen for simplicity and Python ecosystem integration. The dual-engine design allows flexible automation strategies - Browser-Use for complex autonomous tasks, Playwright MCP for precise tool-based control.

### Automation Engines

#### Browser-Use Engine
- **Technology**: browser-use library with LangChain integration
- **LLM**: OpenAI GPT-4o-mini for reasoning
- **Execution Model**: Autonomous agent that interprets instructions and takes actions
- **Strengths**: Handles complex multi-step workflows with minimal explicit tool calls
- **Resource Management**: Creates fresh browser instances per request, runs on isolated asyncio event loops

#### Playwright MCP Engine
- **Technology**: Playwright browser automation with Model Context Protocol
- **Architecture**: Client-server model using stdio transport
- **Client**: `MCPStdioClient` launches Node.js MCP server as subprocess, communicates via JSON-RPC
- **Agent**: `BrowserAgent` uses OpenAI to convert natural language to discrete tool calls
- **Execution Model**: LLM selects and sequences specific browser tools (navigate, click, type, screenshot, etc.)
- **Strengths**: Fine-grained control, predictable behavior, discrete auditable actions
- **Process Isolation**: MCP server runs as separate Node.js subprocess for stability

**Key Decision**: Dual-engine approach addresses different use cases - Browser-Use for intelligent autonomous automation, Playwright MCP for precise repeatable tasks with explicit tool control.

### Data Flow

1. User submits instruction via web UI
2. Flask route receives request with instruction, engine type, and headless preference
3. `EngineOrchestrator` retrieves or creates appropriate engine instance
4. Engine executes instruction (Browser-Use via agent loop, Playwright MCP via tool calls)
5. Results streamed back to frontend with step-by-step progress
6. UI displays execution steps and final outcome

## External Dependencies

### AI/LLM Services
- **OpenAI API**: Powers both engines for natural language understanding and action planning
  - API key required via environment variable `OPENAI_API_KEY` or `config.ini`
  - Model: GPT-4o-mini for cost-effective performance
  - Purpose: Instruction interpretation, tool selection, autonomous reasoning

### Browser Automation Libraries
- **Playwright**: Core browser automation for Playwright MCP engine
  - Version: 1.57.0-alpha (specific alpha build)
  - Provides MCP server implementation and browser control
  - Supports Chromium, Firefox, WebKit
  
- **browser-use**: AI-native browser automation library for Browser-Use engine
  - Integrates with LangChain for LLM-powered actions
  - Handles browser lifecycle and action execution

### Python Dependencies
- **Flask**: Web framework for API and UI serving
- **LangChain**: LLM orchestration framework
- **langchain-openai**: OpenAI integration for LangChain

### Node.js Dependencies
- **@modelcontextprotocol/sdk**: MCP protocol implementation
- **playwright-core**: Playwright automation core (used by MCP server)

### Configuration Management
- Environment variables for sensitive data (OpenAI API key)
- `config.ini` for application settings (browser type, headless mode, model selection)
- Configurable per-engine settings (headless mode, browser choice)

### Runtime Requirements
- **Python 3.x**: Backend application runtime
- **Node.js >= 18**: MCP server runtime for Playwright MCP engine
- **Browser binaries**: Chromium/Firefox/WebKit installed by Playwright

## Replit Environment Setup

### Recent Changes

- **2025-10-23**: Security and reliability enhancements
  - Added optional API key authentication for endpoint protection
  - Implemented rate limiting (10 requests/minute per IP)
  - Added comprehensive input validation for all API endpoints
  - Replaced signal.alarm with cross-platform threading timeout
  - Implemented structured error handling with sanitized user messages
  - Added CORS configuration with environment-based origins
  - Created Playwright subprocess monitoring and auto-recovery
  - Added timeout cleanup hooks to prevent resource leaks
  - Created comprehensive security setup documentation

- **2025-10-22**: Configured for Replit environment
  - Removed hardcoded API key from config.ini for security
  - Configured OPENAI_API_KEY as Replit secret (environment variable)
  - Installed Playwright Chromium browser binaries
  - Configured workflow to run Flask server on port 5000
  - Set up VM deployment for production (always-running instance)
  - Updated .gitignore to preserve Replit config files

### Workflow Configuration
- **Server**: Runs `uv run python main.py` on port 5000
  - Uses uv package manager for Python dependency management
  - Serves on 0.0.0.0:5000 (all interfaces) for Replit proxy compatibility
  - Configured for webview output to show UI in Replit preview

### Deployment Configuration
- **Target**: VM (always-running)
  - Required for browser automation to maintain state and subprocess instances
  - Ensures MCP server subprocess persists across requests
  - Prevents browser instance recreation overhead

### Environment Variables
- `OPENAI_API_KEY`: Required - stored in Replit Secrets
- Application reads from environment variable first, falls back to config.ini

### Dependencies Managed By
- **Python**: uv (pyproject.toml) - run `uv sync` to install
- **Node.js**: npm (package.json) - run `npm install`
- **Browsers**: Playwright - run `npx playwright install chromium`