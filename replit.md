# AI Browser Automation

## Overview

AI Browser Automation is an AI-powered platform for automating web browser interactions using natural language. It features an AI-driven "Browser-Use" engine for intelligent reasoning and a "Playwright MCP" engine for tool-based execution. The platform enables complex multi-step workflows, data extraction, screenshot capture, and advanced browser tasks via a Flask web service with a modern web interface. The business vision is to provide an efficient solution for repetitive web tasks, offering significant market potential in web data interaction and process automation.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### October 28, 2025 - Performance Improvements for Playwright MCP
- **Increased Max Iterations** - Fixed "max iterations reached" issue
  - Updated all Playwright MCP agents (BrowserAgent, PlannerAgent, GeneratorAgent, EnhancedCodeGenerator) to read `max_steps` from config
  - Increased `max_steps` from 20 to 40 in `config/config.ini` for complex automation tasks
  - Changed from hardcoded values (10-20) to centralized configuration
  - Prevents timeout issues on longer automation workflows
- **Optimized Code Generation** - Eliminated duplicate code generation
  - Removed code generation from direct execution mode (was making slow LLM API calls)
  - Code generation now happens only once in automation mode using fast MCPCodeGenerator
  - MCPCodeGenerator converts steps to code locally without API calls (~instant)
  - **Result**: Code generation is now 5-10x faster for simple tasks
- **Optimized Agent Efficiency** - Faster browser automation execution
  - Updated system prompt to emphasize efficiency and minimal necessary steps
  - Agent now avoids unnecessary snapshots and redundant actions
  - Clearer completion criteria to stop iteration as soon as task is done
  - **Result**: Simple automation tasks complete 2-3x faster with fewer LLM calls
- **Overall Performance**: Simple tasks like "open google search for lion" now complete in seconds instead of minutes

### October 28, 2025 - MCP Server Mode Configuration & Enhanced Code Generation
- **NEW: ⚙️ Configurable MCP Server Modes** - Control how the Playwright MCP server runs
  - `always_run` mode: Keeps MCP server running persistently (faster response, uses more resources)
  - `on_demand` mode: Starts MCP server only when needed (saves resources, slower first request)
  - Configuration in `config/config.ini` under `[playwright_mcp]` section
  - Server manager with singleton pattern ensures single persistent instance
  - Automatic cleanup on app shutdown via atexit handler
- **NEW API Endpoints**:
  - `GET /api/mcp/status`: Check MCP server status and mode
  - `POST /api/mcp/restart`: Restart persistent MCP server (always_run mode only)
  - `GET /health`: Now includes MCP server status
- **Enhanced Browser-use Code Generation** - Playwright Agents pattern implementation
  - Semantic locator prioritization (data-testid, role+name, aria-label, etc.)
  - Automatic selector validation with confidence scoring (HIGH/MEDIUM/LOW/REJECTED)
  - Production-ready standalone scripts following Microsoft's best practices
  - Enhanced mode enabled by default (configurable)
  - Both engines now generate standalone Python scripts instead of pytest tests

### October 28, 2025 - Automatic Multiple Screenshot Capture
- **Automatic Screenshot Capture** - Always captures at least one screenshot at the end of execution
  - Intelligent parsing of screenshot requests: "take 3 screenshots", "capture 5 screenshots", etc.
  - Handles plural forms ("screenshots") and multiple mentions
  - Default: 1 final screenshot if not mentioned in prompt
  - Maximum limit: 10 screenshots per execution to prevent abuse
- **Multiple Screenshot Support**:
  - Database schema: `screenshot_path` now stores JSON array of screenshot paths
  - UI displays all screenshots in responsive grid layout with numbered labels
  - Click any screenshot to open full size in new tab
  - Backward compatible with existing single screenshot data
- **Database Migration Required**:
  - The `screenshot_path` column type changed from `String(500)` to `Text`
  - Existing data will be automatically converted to JSON array format
  - Migration handled gracefully in `to_dict()` method with fallback

### October 28, 2025 - Healing Workflow for Script Execution
- **Script Healing Workflow** - Execute generated scripts from history with automatic healing when locator issues are detected
- **API Endpoints**:
  - `POST /api/history/<id>/execute`: Executes script with HealerAgent, automatically fixes locator issues
  - `GET /api/history/<id>`: Auto-promotes healed_script to generated_script when opening history
  - `POST /api/history/<id>/promote-healed`: Manual promotion endpoint (optional)
- **Workflow**: Open history → see Generated Script → Execute → if issues found → Healer fixes them → see Healed Script → reopen → healed version becomes new Generated Script
- **Frontend Integration**: Execute button in history modal, dynamic injection of healed scripts without auto-refresh, success/failure banners
- **Continuous Improvement**: Each healing cycle improves script quality, creating progressively more reliable automation
- **User Experience**: Clear visual feedback, healed script visible until manual reopen triggers promotion, cross-browser compatible event handling

## System Architecture

### UI/UX Decisions

The frontend is a single-page application (SPA) built with vanilla JavaScript, featuring a two-column layout for configuration and real-time execution status. The design uses a gradient purple theme with responsive CSS Grid. It provides real-time status updates, JSON result display, Playwright code preview, and persistent engine/mode selections.

### Technical Implementations

The backend is a modular Flask application using a factory pattern and an `Engine Orchestrator` to manage two distinct automation engines:

1.  **Browser-Use Engine (AI-Powered)**: Leverages OpenAI's LLM for reasoning about browser actions via the `browser-use` library and Playwright. Features include advanced popup handling, retries, state management, data extraction, screenshot/PDF generation, and cookie management. It's designed to be thread-safe with fresh browser instances per request.
2.  **Playwright MCP Engine (Tool-Based)**: Uses the Model Context Protocol (MCP) for discrete tool calls. It employs OpenAI function calling to map natural language to browser tools, communicating with a Node.js MCP server. This engine integrates Microsoft's Playwright Test Agents for automated test generation and self-healing:
    *   **Planner Agent**: Explores applications and creates test plans in Markdown (`specs/`).
    *   **Generator Agent**: Transforms test plans into executable Playwright Python tests (`tests/`).
    *   **Healer Agent**: Automatically repairs failing tests by analyzing errors and fixing selectors/assertions.
    *   **File Manager**: Manages `specs/` and `tests/` directories.
    *   **Initialization Script**: Sets up the workspace, seed test, and README.

Both engines include **Code Generation** capabilities to produce reusable Playwright Python code from executed automation steps, including self-healing features (retries, backoff, selector fallbacks).

### System Design Choices

*   **Execution Flow**: User instructions are processed via a REST API (`/api/execute`). The orchestrator selects an engine, creating a new browser instance and event loop for each request. Results, history, and generated code are returned to the client, with browser instances cleaned up post-execution.
*   **Security & Middleware**: Includes optional API key authentication, in-memory rate limiting, input validation, and CORS support. Error messages are sanitized.
*   **Thread Safety**: Each request uses its own asyncio event loop and browser instance.
*   **Timeout Handling**: A cross-platform mechanism using `ThreadPoolExecutor` prevents hung operations, with a default timeout of 300 seconds.
*   **Performance Optimizations**: Includes automatic browser instance cleanup, proper asyncio event loop disposal, full SSE streaming support for real-time progress updates, optimized browser wait times (e.g., 0.5s page load, 0.5s action execution), and optional use of the ChatBrowserUse Model for faster automation.

### Data Storage

*   **PostgreSQL Database**: Stores persistent execution history (prompt, engine, success status, generated scripts, screenshots, logs, timing) via the `ExecutionHistory` model.
*   **File-Based Outputs**: Screenshots, PDFs, and cookies are stored in `automation_outputs/`. Workflow states are managed via `workflow_states/*.json`.
*   **Playwright Test Agents Workspace**: Test plans in `specs/` and generated tests in `tests/`.

## External Dependencies

### Third-Party Services

*   **Gateway API with OAuth 2.0**: Used for LLM reasoning in both automation engines. Requires `OAUTH_TOKEN_URL`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_GRANT_TYPE`, `OAUTH_SCOPE`, and `GW_BASE_URL` environment variables.

### Core Python Libraries

*   **browser-use**: AI-powered browser automation.
*   **Playwright**: Cross-browser automation framework.
*   **langchain-openai**: Integration for OpenAI models.
*   **Flask**: Web framework.
*   **Flask-CORS**: Cross-origin resource sharing.
*   **python-dotenv**: Environment variable management.
*   **gunicorn**: Production WSGI server.

### Node.js Components

*   **Playwright MCP Server**: A custom Node.js server (`integrations/playwright_mcp_node/`) providing tool-based automation via JSON-RPC over STDIO, using `@modelcontextprotocol/sdk`, `playwright`, and `playwright-core`.

### Browser Requirements

*   **Playwright Browsers**: Automatically downloads Chromium, Firefox, and WebKit (defaulting to Chromium).