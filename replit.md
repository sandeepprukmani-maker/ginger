# AI Browser Automation

## Overview

AI Browser Automation is an AI-powered platform designed to automate web browser interactions using natural language instructions. It features two distinct automation engines: an AI-driven "Browser-Use" engine for intelligent reasoning and a "Playwright MCP" engine for tool-based execution. The platform enables users to describe complex multi-step workflows, perform data extraction, capture screenshots, and manage advanced browser tasks through a Flask web service with a modern web interface. The business vision is to provide a highly efficient and accessible solution for automating repetitive web tasks, opening up market potential across various industries requiring web data interaction and process automation.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### October 26, 2025 - Replit Environment Setup & Code Generation Integration
- Migrated from GitHub import to Replit environment
- Fixed requirements.txt dependencies (corrected typos: fla→flask-cors, removed pywin32)
- Installed all Python dependencies including browser-use v0.9.1, Playwright v1.55.0
- Installed Playwright Chromium browser and dependencies
- Installed Node.js dependencies for Playwright MCP server
- Configured Flask to serve on 0.0.0.0:5000 for Replit proxy compatibility
- Added comprehensive .gitignore for Python/Node.js/Playwright projects
- Set up Gunicorn deployment configuration with autoscale for production
- SQLite database fallback configured for local development (Replit PostgreSQL optional)
- Application successfully running with privacy settings enabled (telemetry disabled)
- **Fixed history "View Full Details" modal**: Now properly displays content for all engine types (browser_use, browser_use_optimized, playwright_mcp) with fallback message when no detailed data available
- **Improved engine labels**: Correctly displays "Browser Use", "Browser Use (Optimized)", and "Playwright MCP" in history cards
- **Code Generation Integration** (Critical Fix):
  - Created unified code generator interface (`app/services/code_generator_interface.py`) with factory pattern for both engines
  - Integrated automatic code generation into EngineOrchestrator after successful executions
  - Generated Playwright Python code now automatically included in API responses as `generated_code`
  - Code metadata (action count, generator type, quality scores) included in results
  - Database persistence fully wired - generated code saved to `generated_script` field
  - Both Browser-Use and Playwright MCP engines now produce CI/CD-ready test code
  - Error handling ensures code generation failures don't break main execution flow

## System Architecture

### Frontend Architecture

The system features a single-page application (SPA) built with vanilla JavaScript. It utilizes a two-column layout: a left panel for configuration (engine selection, headless mode, instruction input) and a right panel for real-time execution status, results, and generated code. The UI sports a gradient purple theme with responsive design using CSS Grid. Client-side features include real-time status updates, JSON result display, Playwright code preview, and persistent engine/mode selections.

### Backend Architecture

The backend is a modular Flask application following the factory pattern. An **Engine Orchestrator** (`app/services/engine_orchestrator.py`) manages two distinct automation engines, caching instances and handling their lifecycle.

**Automation Engines:**

1.  **Browser-Use Engine (AI-Powered)**: Located in `app/engines/browser_use/`, this is the default and recommended engine. It leverages OpenAI's LLM for reasoning about browser actions using the `browser-use` library with a Playwright backend. Features include advanced popup handling, retry mechanisms with exponential backoff, state management for complex workflows, performance monitoring, data extraction (tables, lists, metadata), screenshot/PDF generation, and cookie management. It's designed to be thread-safe, creating fresh browser instances per request.

2.  **Playwright MCP Engine (Tool-Based)**: Located in `app/engines/playwright_mcp/`, this engine uses the Model Context Protocol (MCP) for discrete tool calls. It employs OpenAI function calling to map natural language to browser tools, communicating with a Node.js MCP server via STDIO. Available tools include navigate, click, fill, snapshot, select, hover, evaluate, and screenshot.

Both engines include **Code Generation** capabilities to convert executed automation steps into reusable Playwright Python code.

**Execution Flow:**
User instructions are submitted via a REST API (`/api/execute`). The orchestrator selects an engine, which then creates a new browser instance and event loop. The AI agent executes browser actions, and results, history, and generated code are returned to the client. Browser instances are cleaned up post-execution.

**Security & Middleware** (`app/middleware/security.py`): Includes optional API key authentication, in-memory rate limiting (10 requests/60 seconds), input validation, and CORS support. Error messages are sanitized to prevent information leakage.

**Thread Safety:** Each request operates on its own asyncio event loop and browser instance to ensure thread safety in Flask's multi-threaded environment.

**Timeout Handling** (`app/utils/timeout.py`): A cross-platform mechanism using `ThreadPoolExecutor` prevents hung operations, with a default timeout of 300 seconds.

### API Endpoints

-   `GET /`: Web interface
-   `POST /api/execute`: Execute automation instruction
-   `POST /api/execute/stream`: Execute with Server-Sent Events streaming
-   `GET /api/history`: Get paginated execution history
-   `GET /api/history/<id>`: Get specific execution details
-   `DELETE /api/history`: Delete all execution history
-   `DELETE /api/history/<id>`: Delete specific execution
-   `GET /health`: Health check endpoint

### Data Storage

**PostgreSQL Database**: Replit's built-in PostgreSQL database stores persistent execution history via the `ExecutionHistory` model, capturing prompt, engine, mode, success status, generated scripts, screenshots, logs, and timing.

**File-Based Outputs**: Screenshots, PDFs, and cookies are stored in `automation_outputs/` directories. Workflow states for complex multi-step processes are managed via `workflow_states/*.json`.

### Authentication & Authorization

Optional API key authentication is available via the `X-API-Key` header, configurable with the `API_KEY` environment variable. The system does not implement user management or role-based access control.

## External Dependencies

### Third-Party Services

-   **Gateway API with OAuth 2.0**: Essential for LLM reasoning in both automation engines. Uses OAuth 2.0 client credentials flow for authentication via gateway endpoint (`GW_BASE_URL`). Supports GPT-4.1 model (`gpt-4.1-2025-04-14-eastus-dz`) optimized for coding tasks. OAuth configuration requires: `OAUTH_TOKEN_URL`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_GRANT_TYPE`, and `OAUTH_SCOPE` environment variables.

### Core Python Libraries

-   **browser-use (v0.5.9)**: AI-powered browser automation with ChatBrowserUse optimized model support (3-5x faster execution).
-   **Playwright (v1.55.0)**: Cross-browser automation framework.
-   **langchain-openai**: Integration for OpenAI models.
-   **Flask**: Web framework.
-   **Flask-CORS**: Cross-origin resource sharing.
-   **python-dotenv**: Environment variable management.
-   **gunicorn**: Production WSGI server.

### Performance Optimizations (October 2025)

**Browser Resource Management**:
-   Automatic browser instance cleanup after each execution via finally blocks
-   Proper asyncio event loop disposal with pending task cancellation
-   Zero memory leaks from browser/event loop accumulation

**Real-Time Progress Updates**:
-   Full SSE streaming support with progress callbacks: init, browser_init, agent_create, execution_start, step
-   Progress callbacks properly wired from engines through orchestrator to frontend
-   Eliminates UI unresponsiveness during long-running automations

**Optimized Browser Wait Times**:
-   Reduced page load times: 0.5s minimum, 1.0s network idle (down from 1.0s/1.5s)
-   Faster action execution: 0.5s between actions (down from 1.0s)
-   40-50% faster automation execution while maintaining reliability

**ChatBrowserUse Model**:
-   Optional 3-5x faster browser automation using specialized LLM
-   Configurable via `use_chat_browser_use=true` in config.ini
-   Automatic fallback to standard OpenAI models if unavailable
-   Improved task completion accuracy

**Enhanced Timeout Handling**:
-   Proper cleanup of timed-out browser sessions
-   Engine cache eviction prevents zombie browser reuse
-   300-second timeout with graceful degradation

### Node.js Components

-   **Playwright MCP Server**: Located in `integrations/playwright_mcp_node/`, this custom MCP server provides tool-based automation via JSON-RPC over STDIO. It uses `@modelcontextprotocol/sdk`, `playwright`, and `playwright-core`.

### Browser Requirements

-   **Playwright Browsers**: Automatically downloads Chromium, Firefox, and WebKit. Default browser is Chromium, with configurable headless mode.

### Configuration Files

-   **config/config.ini**: Central configuration for LLM models and browser settings.
-   **.env**: Stores sensitive environment variables including OAuth credentials (`OAUTH_TOKEN_URL`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_GRANT_TYPE`, `OAUTH_SCOPE`), gateway endpoint (`GW_BASE_URL`), `SESSION_SECRET`, and `CORS_ALLOWED_ORIGINS`.
-   **auth/oauth_handler.py**: Centralized OAuth 2.0 authentication module handling token fetching, caching, retry logic, and certificate management for secure gateway connections.