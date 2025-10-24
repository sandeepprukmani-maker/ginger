# AI Browser Automation

## Overview

AI-powered browser automation platform providing two distinct automation engines: **Browser-Use** (AI-driven reasoning) and **Playwright MCP** (tool-based execution). The system allows users to describe automation tasks in natural language, which are executed by intelligent agents controlling web browsers.

Built as a Flask web service with a modern web interface, supporting both headless and headful browser modes. Designed to handle complex multi-step workflows, data extraction, screenshot capture, and other advanced browser automation tasks.

## User Preferences

Preferred communication style: Simple, everyday language.

## Project Structure

```
ai-browser-automation/
├── app/                          # Flask application
│   ├── engines/                  # Automation engines
│   │   ├── browser_use/          # Browser-Use AI engine
│   │   │   ├── engine.py         # Base engine
│   │   │   ├── engine_optimized.py  # Enhanced with advanced features
│   │   │   ├── advanced_features.py # Screenshots, PDFs, cookies
│   │   │   ├── retry_mechanism.py   # Exponential backoff retry
│   │   │   ├── state_manager.py     # Workflow state persistence
│   │   │   ├── data_extractor.py    # Table/list extraction
│   │   │   ├── performance_monitor.py # Metrics tracking
│   │   │   ├── popup_handler.py     # Popup window handling
│   │   │   └── playwright_code_generator.py # Code export
│   │   └── playwright_mcp/       # Playwright MCP tool engine
│   │       ├── agent/            # Conversation agent
│   │       ├── client/           # STDIO MCP client
│   │       └── mcp_code_generator.py # Code export
│   ├── middleware/               # Security & validation
│   │   └── security.py           # Auth, rate limiting, validation
│   ├── routes/                   # API endpoints
│   │   └── api.py                # REST API routes
│   ├── services/                 # Business logic
│   │   └── engine_orchestrator.py # Engine management
│   ├── static/                   # Frontend assets
│   │   ├── css/style.css
│   │   └── js/app.js
│   ├── templates/                # HTML templates
│   │   └── index.html
│   └── utils/                    # Shared utilities
│       └── timeout.py            # Cross-platform timeout handling
├── integrations/                 # External integrations
│   └── playwright_mcp_node/      # Node.js MCP server
│       ├── cli.js                # Server entry point
│       └── package.json          # Node dependencies
├── config/                       # Configuration
│   └── config.ini                # OpenAI & browser settings
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── conftest.py               # Pytest configuration
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project metadata
└── .env                          # Environment variables (secrets)
```

## System Architecture

### Frontend Architecture

**Web Interface**: Single-page application (SPA) using vanilla JavaScript with a two-column layout:
- Left panel: Configuration controls (engine selection, headless mode toggle, instruction input)
- Right panel: Real-time execution status, results display, and generated code preview
- Styling: Gradient purple theme with responsive design using CSS Grid

**Client-Side Features**:
- Real-time status updates during automation execution
- JSON result formatting and display
- Generated Playwright code preview for reusability
- Engine and mode selection persistence in UI

### Backend Architecture

**Flask Application Factory Pattern**: Modular structure with blueprints, middleware, and services separation.

**Engine Orchestrator** (`app/services/engine_orchestrator.py`): Manages two distinct automation engines with instance caching and lifecycle management.

**Automation Engines**:

1. **Browser-Use Engine** (AI-Powered - Default & Recommended):
   - Location: `app/engines/browser_use/`
   - Uses OpenAI's LLM to reason about browser actions
   - Implements the `browser-use` library with Playwright backend
   - Features: Advanced popup handling, retry mechanisms with exponential backoff, state management for complex workflows, performance monitoring, data extraction (tables, lists, metadata), screenshot/PDF generation, cookie management
   - Thread-safe design: Creates fresh browser instances per request with proper cleanup
   - Two implementations: `engine.py` (base) and `engine_optimized.py` (enhanced)

2. **Playwright MCP Engine** (Tool-Based):
   - Location: `app/engines/playwright_mcp/`
   - Uses Model Context Protocol (MCP) for discrete tool calls
   - OpenAI function calling to map natural language to browser tools
   - Communicates with Node.js MCP server via STDIO transport (subprocess)
   - Available tools: navigate, click, fill, snapshot, select, hover, evaluate, screenshot
   - Node server location: `integrations/playwright_mcp_node/`

**Code Generation**: Both engines include code generators that convert executed automation steps into reusable Playwright Python code.

**Execution Flow**:
1. User submits natural language instruction via REST API (`/api/execute`)
2. Orchestrator selects appropriate engine based on request parameter
3. Engine creates fresh browser instance on new event loop (thread safety)
4. AI agent interprets instruction and executes browser actions
5. Results, history, and generated code returned to client
6. Browser instance cleaned up via finally block

**Security & Middleware** (`app/middleware/security.py`):
- API key authentication (optional, configurable via `API_KEY` env var)
- Rate limiting: In-memory limiter (10 requests per 60 seconds by default)
- Input validation and sanitization
- Error message sanitization to prevent information leakage
- CORS support with configurable allowed origins

**Thread Safety Design**: Designed for Flask's multi-threaded WSGI environment. Each request creates its own asyncio event loop and browser instance, avoiding event loop affinity issues. Resources are properly cleaned up after each request.

**Timeout Handling** (`app/utils/timeout.py`): Cross-platform timeout mechanism using ThreadPoolExecutor to prevent hung operations (default: 300 seconds).

### API Endpoints

- `GET /` - Web interface
- `POST /api/execute` - Execute automation instruction
- `GET /api/tools` - List available tools for an engine
- `POST /api/reset` - Reset agent conversation history
- `GET /health` - Health check endpoint

### Data Storage

**No Database**: The current implementation does not use a persistent database. All state is in-memory or written to local files (screenshots, PDFs, workflow states, cookies).

**File-Based Outputs**:
- Screenshots: `automation_outputs/screenshots/`
- PDFs: `automation_outputs/pdfs/`
- Cookies: `automation_outputs/cookies/`
- Workflow states: `workflow_states/*.json` (for complex multi-step workflows)

**Environment Configuration**: Uses `python-dotenv` to load configuration from `.env` file with explicit override to prevent system environment variable conflicts.

### Authentication & Authorization

**API Key Authentication**: Optional middleware-based API key validation via `X-API-Key` header. Disabled by default (no auth required), can be enabled by setting `API_KEY` environment variable.

**No User Management**: The system does not implement user accounts, sessions, or role-based access control. It's designed as a single-user or team-shared automation service.

## External Dependencies

### Third-Party Services

**OpenAI API** (Required):
- Purpose: LLM reasoning for natural language instruction interpretation
- Configuration: `OPENAI_API_KEY` environment variable (never hardcoded)
- Models used: `gpt-4o-mini` (default, configurable in `config/config.ini`)
- Usage: Both engines use OpenAI for instruction understanding and action planning

### Core Python Libraries

- **browser-use**: AI-powered browser automation library with LLM reasoning
- **Playwright**: Cross-browser automation framework (Chromium, Firefox, WebKit)
- **langchain-openai**: LangChain integration for OpenAI models
- **Flask**: Web framework for REST API and UI serving
- **Flask-CORS**: Cross-origin resource sharing support
- **python-dotenv**: Environment variable management from `.env` files
- **pytest**, **pytest-cov**: Testing framework and coverage
- **gunicorn**: Production WSGI server

### Node.js Components

**Playwright MCP Server** (`integrations/playwright_mcp_node/`):
- Purpose: Provides tool-based browser automation via Model Context Protocol
- Package: `@playwright/mcp` (custom MCP server implementation)
- Communication: JSON-RPC over STDIO with Python subprocess
- Dependencies: `@modelcontextprotocol/sdk`, `playwright`, `playwright-core`

### Browser Requirements

**Playwright Browsers**: Automatically downloads Chromium, Firefox, and WebKit on first run. Configurable via `config/config.ini`:
- Default browser: Chromium
- Headless mode: Configurable per request
- Browser validation: Skipped via `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1`

### Configuration Files

**config/config.ini**: Central configuration for OpenAI models and browser settings
**.env**: Sensitive environment variables (API keys, secrets)
- `OPENAI_API_KEY`: Required for AI features
- `SESSION_SECRET`: Flask session secret
- `CORS_ALLOWED_ORIGINS`: Comma-separated allowed origins for CORS

## Testing

**Test Structure** (`tests/`):
- `unit/`: Unit tests for individual components (security, validation, utilities)
- `integration/`: Integration tests for API endpoints and engine orchestration
- `conftest.py`: Pytest configuration and shared fixtures

Run tests: `pytest tests/`

## Performance Optimization

**Conservative "Reliability-First" Optimizations** (2025-10-24):
- **System Prompt Optimization**: Refined instructions from ~1400 to ~700 characters (50% reduction) while preserving all safety guardrails including verification steps, security checks, error recovery, and popup handling
- **Reduced Logging Overhead**: Disabled detailed metrics tracking (kept summary logging); disabled verbose popup logging
- **Configuration**: All reliability settings preserved at safe defaults:
  - max_steps: 25 (handles complex workflows)
  - Browser waits: 1.0s/1.5s/1.0s (reliable page loading)
  - LLM timeout: 180s (handles long-running tasks)
  - Retry: 3 attempts with exponential backoff
  - Features: Screenshots, PDFs, cookies, state persistence all enabled
- **Expected Impact**: ~20% reduction in LLM processing time, ~5% reduction in logging overhead, zero compromise on reliability or functionality

## Recent Changes

**2025-10-24**: Major project restructure
- Removed hybrid engine implementation (simplified to 2 engines: browser_use, playwright_mcp)
- Reorganized project structure professionally:
  - Moved `browser_use_codebase/` → `app/engines/browser_use/`
  - Moved `playwright_mcp_codebase/` → `app/engines/playwright_mcp/`
  - Moved `node/` → `integrations/playwright_mcp_node/`
- Updated all imports to reflect new package structure
- Deleted unnecessary files (requirements.txt.bak, config.ini duplicate, check_env.py, run_windows.bat, uv.lock)
- Created professional test suite structure
- Browser-Use is now the default and recommended engine
- Applied conservative performance optimizations (prompt refinement, reduced logging overhead)
