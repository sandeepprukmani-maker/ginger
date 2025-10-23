# AI Browser Automation

## Overview

AI Browser Automation is a Flask-based web application that provides intelligent browser automation through natural language instructions. The system implements a hybrid approach that combines AI-powered autonomous automation with reliable tool-based control, offering automatic fallback mechanisms for maximum reliability.

The application exposes a RESTful API and web interface that allows users to execute browser automation tasks using three distinct engines:
- **Hybrid Engine** (recommended): Attempts AI-powered Browser-Use first, automatically falls back to Playwright MCP if needed
- **Browser-Use Engine**: Fully autonomous AI agent using LLM reasoning for complex workflows
- **Playwright MCP Engine**: Deterministic tool-based automation using Microsoft's Model Context Protocol

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Framework
- **Web Framework**: Flask with factory pattern (`create_app()`)
- **Frontend**: Server-side rendered HTML with vanilla JavaScript
- **API Design**: RESTful endpoints with JSON request/response format
- **Multi-threading**: Flask's default threaded mode with per-request resource isolation

### Core Components

#### Engine Orchestration Layer
The `EngineOrchestrator` serves as the central coordinator:
- Manages three distinct automation engines (Hybrid, Browser-Use, Playwright MCP)
- Implements per-headless-mode caching for engine instances
- Delegates execution based on engine selection
- Rationale: Centralized management ensures consistent engine lifecycle and prevents resource leaks

#### Automation Engines

**1. Hybrid Engine** (`hybrid_engine/`)
- Strategy: Primary-fallback pattern
- Uses Browser-Use as primary, Playwright MCP as automatic fallback
- Returns metadata indicating which engine succeeded
- Design rationale: Combines AI intelligence with tool-based reliability for production use

**2. Browser-Use Engine** (`browser_use_codebase/`)
- AI-powered automation using the `browser-use` library
- Leverages OpenAI LLMs for autonomous reasoning
- Thread safety: Creates fresh browser instance per request with isolated event loops
- No instance caching to prevent asyncio loop affinity issues
- Design rationale: Maximizes autonomy for complex multi-step workflows

**3. Playwright MCP Engine** (`playwright_mcp_codebase/`)
- Tool-based automation using Microsoft's Playwright MCP server
- Client-server architecture over STDIO transport
- OpenAI agent converts natural language to discrete tool calls
- Design rationale: Provides deterministic control for reliability

#### Security & Middleware Layer
- **Authentication**: API key validation via headers
- **Rate Limiting**: In-memory rate limiter (10 requests/60 seconds per client)
- **Input Validation**: Instruction sanitization and engine type validation
- **Error Handling**: Sanitized error messages to prevent information leakage
- Design rationale: Multi-layer security without external dependencies

#### Timeout Management
- Cross-platform timeout utility using ThreadPoolExecutor
- Graceful timeout handling that returns promptly to HTTP clients
- Note: Background threads may continue but don't block responses
- Design rationale: Prevents hung requests across Windows/Linux/macOS

### Request Flow

1. Client submits instruction via web UI or API endpoint
2. Security middleware validates API key and applies rate limiting
3. Request validation checks instruction and engine type
4. EngineOrchestrator retrieves/creates appropriate engine instance
5. Engine executes instruction with timeout protection
6. Results formatted and returned as JSON response
7. Frontend updates UI with execution results and metadata

### Thread Safety Model

**Browser-Use Engine**: 
- Creates new event loop per request
- No shared state between requests
- Browser instances disposed after execution
- Trade-off: Slower startup but complete isolation

**Playwright MCP Engine**:
- Subprocess-based MCP server
- STDIO communication via JSON-RPC
- Thread-safe client with request ID tracking
- Trade-off: Subprocess overhead but predictable lifecycle

**Hybrid Engine**:
- Lazy initialization of both engines
- Falls back automatically on Browser-Use failure
- Tracks which engine succeeded for transparency

### Configuration Management
- Environment variables for secrets (OPENAI_API_KEY, SESSION_SECRET)
- INI files for non-sensitive settings (config/config.ini)
- Runtime overrides via API parameters (headless mode, browser choice)
- Design rationale: Separates secrets from configuration, supports flexibility

### Error Handling Strategy
- Graceful degradation: Hybrid engine falls back automatically
- Timeout protection: All engine executions wrapped in timeout utility
- Error sanitization: Production errors don't leak internal details
- Logging: Comprehensive logging at INFO level for debugging

## External Dependencies

### AI & Language Models
- **OpenAI API**: LLM for natural language understanding and reasoning
  - Used by both Browser-Use and Playwright MCP agents
  - Configured via OPENAI_API_KEY environment variable
  - Default model: gpt-4o-mini (configurable)

### Browser Automation Libraries
- **browser-use** (>=0.5.9): AI-powered autonomous browser automation
- **Playwright**: Browser automation framework (via @playwright/mcp Node package)
- **playwright-core**: Core Playwright functionality

### Web Framework & HTTP
- **Flask** (>=3.1.2): Python web framework
- **flask-cors** (>=6.0.1): Cross-origin resource sharing
- **flask-sqlalchemy** (>=3.1.1): Database ORM (prepared for future persistence)
- **gunicorn** (>=23.0.0): WSGI HTTP server for production

### Node.js Integration
- **@playwright/mcp** (v0.0.43): Playwright Model Context Protocol server
- **@modelcontextprotocol/sdk**: MCP SDK for tool-based automation
- Communication: Subprocess with STDIO transport using JSON-RPC

### Supporting Libraries
- **langchain-openai** (>=1.0.1): LangChain OpenAI integration
- **python-dotenv** (>=1.1.1): Environment variable management
- **psycopg2-binary** (>=2.9.11): PostgreSQL adapter (for future database features)
- **requests** (>=2.32.5): HTTP library
- **sseclient-py** (>=1.8.0): Server-sent events client

### Testing
- **pytest** (>=8.4.2): Testing framework
- **pytest-cov** (>=7.0.0): Code coverage reporting

### Security Considerations
- API keys stored exclusively in environment variables
- No secrets in configuration files or code
- Input sanitization on all user-provided data
- Rate limiting to prevent abuse
- CORS configured with explicit allowed origins