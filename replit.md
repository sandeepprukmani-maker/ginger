# AI Browser Automation

## Overview

AI Browser Automation is an AI-powered platform designed to automate web browser interactions using natural language instructions. It features two distinct automation engines: an AI-driven "Browser-Use" engine for intelligent reasoning and a "Playwright MCP" engine for tool-based execution. The platform enables users to describe complex multi-step workflows, perform data extraction, capture screenshots, and manage advanced browser tasks through a Flask web service with a modern web interface. The business vision is to provide a highly efficient and accessible solution for automating repetitive web tasks, opening up market potential across various industries requiring web data interaction and process automation.

## User Preferences

Preferred communication style: Simple, everyday language.

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

-   **OpenAI API**: Essential for LLM reasoning in both automation engines. Configured via `OPENAI_API_KEY` environment variable, defaulting to `gpt-4o-mini` model.

### Core Python Libraries

-   **browser-use**: AI-powered browser automation.
-   **Playwright**: Cross-browser automation framework.
-   **langchain-openai**: Integration for OpenAI models.
-   **Flask**: Web framework.
-   **Flask-CORS**: Cross-origin resource sharing.
-   **python-dotenv**: Environment variable management.
-   **gunicorn**: Production WSGI server.

### Node.js Components

-   **Playwright MCP Server**: Located in `integrations/playwright_mcp_node/`, this custom MCP server provides tool-based automation via JSON-RPC over STDIO. It uses `@modelcontextprotocol/sdk`, `playwright`, and `playwright-core`.

### Browser Requirements

-   **Playwright Browsers**: Automatically downloads Chromium, Firefox, and WebKit. Default browser is Chromium, with configurable headless mode.

### Configuration Files

-   **config/config.ini**: Central configuration for OpenAI models and browser settings.
-   **.env**: Stores sensitive environment variables like `OPENAI_API_KEY`, `SESSION_SECRET`, and `CORS_ALLOWED_ORIGINS`.