# Overview

This is a comprehensive **AI-powered browser automation platform** that provides intelligent web automation through multiple engines and advanced capabilities. The platform consists of two main applications:

1. **Engines Application** (`engines/`): A Flask-based API server that orchestrates browser automation using two powerful AI engines - Browser-Use (LLM-powered autonomous navigation) and Playwright MCP (tool-based automation).

2. **VisionVault Application** (`full_vision_vault/`): A full-stack web automation platform with visual testing, teaching mode, task learning, and distributed agent architecture. Code must be provided to execute (no AI code generation in this component).

The system enables users to automate web tasks using natural language instructions, with intelligent error recovery, visual analysis, and continuous learning from successful executions.

# Recent Changes

**October 24, 2025 - Integrated Engines Automation into VisionVault UI**
- **Unified Application**: Created integrated web interface combining VisionVault UI with Engines automation
- **Architecture**: VisionVault UI (port 5000) proxies automation requests to Engines API (internal port 5001)
- **New Endpoint**: Added `/api/automation/execute` in VisionVault that forwards instructions to engines
- **Updated UI**: Modified dashboard to call engines automation and display logs in real-time
- **Unified Startup**: Created `start_server.py` that launches both servers automatically
- **User Experience**: Users enter natural language instructions → Engines executes automation → Logs display in UI
- **Non-blocking Design**: Fixed subprocess stdout handling to prevent pipe blocking during verbose automation logs

**October 24, 2025 - Complete Cleanup of VisionVault Code Generation & Browser Automation**
- **Removed entire `mcp/` directory**: Deleted AI code generation (ai_generator.py), browser automation execution (browser_engine.py, task_executor.py), and MCP client integration
- **Removed healing services**: Deleted healing_executor.py, multi_strategy_healer.py, advanced_locator_validator.py (AI-powered code healing features)
- **Removed planning and inspection services**: Deleted intelligent_planner.py (AI pre-execution analysis) and dom_inspector.py (DOM analysis for automation)
- **Replaced executor**: Created minimal executor.py that only executes user-provided code without AI healing
- **Cleaned up app.py**: Removed all imports and references to deleted services
- **Preserved core features**: Teaching Mode (action recording), Task Library (learned tasks storage), and Recall Mode (semantic task search) remain fully functional
- VisionVault now focuses exclusively on: recording user actions, storing/searching tasks, and executing user-provided code
- Note: The engines/ application still has full AI code generation and automation capabilities

**October 24, 2025 - Removed Code Generation & Healing from VisionVault**
- Removed all code generation functionality from full_vision_vault/api/execute endpoint
- Removed self-healing automation features (HealingExecutor, healing socket handlers)
- Removed "Generated Script" and "Healed Script SMART" UI panels from HTML template
- Modified /api/execute to require code to be provided in request payload instead of generating it
- VisionVault now focuses on execution, recording, and task management without AI code generation
- Note: The engines/ application still has full AI code generation capabilities

**October 24, 2025 - Initial Replit Setup**
- Installed Python 3.11 and all required dependencies
- Installed Playwright Chromium browser for automation
- Created `.env` file in `engines/` directory for environment variables
- Configured Flask app for Replit environment (already using 0.0.0.0:5000 and CORS wildcards)
- Set up workflow to run the Engines Flask server on port 5000
- Created `.gitignore` for Python project
- Configured deployment settings using Gunicorn for production
- Application successfully tested and verified working

# Setup Instructions

## Environment Variables

The application requires the following API keys to be set in Replit Secrets:

1. **OPENAI_API_KEY** (Required for AI features)
   - Needed for Browser-Use engine and AI-powered code generation
   - Get your key from: https://platform.openai.com/api-keys

2. **GEMINI_API_KEY** (Optional)
   - Needed for semantic search and embeddings in VisionVault
   - Get your key from: https://aistudio.google.com/app/apikey

3. **API_KEY** (Optional)
   - For API authentication (disabled in development mode if not set)

## Running the Application

The application runs as a **unified system** via `start_server.py`:

**VisionVault UI** (User-Facing):
- Entry point: `full_vision_vault/run_server.py`
- Port: 5000 (public)
- Web interface for automation, teaching mode, task library, and recall mode
- Endpoints: `/`, `/api/automation/execute`, `/api/teaching/*`, `/api/tasks/*`

**Engines API** (Internal):
- Entry point: `engines/main.py`
- Port: 5001 (localhost only)
- AI automation engine with Browser-Use and Playwright MCP
- Endpoints: `/api/execute`, `/api/health`, `/api/reset`, `/api/tools`

**How it works:**
1. User enters automation instructions in VisionVault UI
2. UI sends request to `/api/automation/execute`
3. VisionVault proxies request to Engines API on port 5001
4. Engines executes automation using AI
5. Results and logs are returned to UI and displayed

Both servers start automatically via the unified `start_server.py` script.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## 1. Multi-Engine Architecture (Engines App)

### Engine Orchestrator Pattern
- **EngineOrchestrator** coordinates two distinct automation engines:
  - **Browser-Use Engine**: AI-powered autonomous navigation using GPT-4o-mini with up to 50 reasoning steps
  - **Playwright MCP Engine**: Tool-based automation using Model Context Protocol with conversational AI
- Engines are cached per headless mode for performance optimization
- Thread-safe execution with per-request event loops to prevent asyncio affinity issues
- Each request creates fresh browser instances with automatic cleanup

### Flask REST API Design
- Blueprint-based route organization (`app/routes/api.py`)
- Security middleware: API key authentication, rate limiting, input validation
- Cross-platform timeout handling for long-running automation tasks
- Structured error responses with sanitized messages for security

### Browser-Use Engine Optimizations
- **Advanced Features**: Screenshot capture, PDF generation, cookie/session management via `AdvancedBrowserFeatures`
- **Smart Retry Mechanism**: Exponential backoff with configurable retry policies (3 attempts default)
- **Popup Handling**: Automatic detection and switching to OAuth popups, payment gateways
- **State Management**: Workflow state persistence for complex multi-step automations via `WorkflowState`
- **Data Extraction**: Table scraping, structured data parsing via `DataExtractor`
- **Performance Monitoring**: Operation timing and success rate tracking via `PerformanceMonitor`

### Playwright MCP Integration
- **STDIO Transport**: Launches Node.js MCP server as subprocess with JSON-RPC communication
- **Conversational Agent**: OpenAI-powered agent interprets natural language and calls MCP tools
- **Tool Discovery**: Dynamic discovery of available Playwright MCP tools at runtime
- Multi-threaded message queue for async request/response handling

## 2. VisionVault Full-Stack Architecture

### Distributed Agent System
- **Server-Agent Architecture**: WebSocket-based communication for distributed test execution
- **Browser Manager**: Centralized browser instance lifecycle management with cleanup
- **Agent Registration**: Auto-discovery of available browsers on agent machines
- **Execution Modes**: Server-side execution vs agent-side execution with mode selection

### Execution & Test Management
- **Code Execution**: Executes user-provided Playwright automation code (no generation)
- **DOM Inspector**: Pre-analyzes pages to extract element information for debugging
- **Screenshot Capture**: Captures screenshots during test execution for visual verification
- **Execution History**: Tracks all test executions with logs and status tracking

### Intelligent Learning System
- **Self-Learning Engine**: Learns from successful/failed executions to improve over time
- **Task Knowledge Base**: Stores successful automation patterns with metadata
- **Semantic Search**: Vector-based task search using Gemini embeddings and FAISS indexing
- **Intelligent Planner**: Pre-execution analysis to predict failures and optimize strategies
- **Execution Feedback Loop**: Tracks task success rates and continuously adapts

### Teaching Mode & Recording
- **Action Recorder**: Browser event listeners capture user interactions (click, input, navigation)
- **Codegen Integration**: Playwright codegen for generating automation scripts from recordings
- **Session Management**: Manages multiple concurrent recording sessions with subprocess monitoring
- **Auto-stop Detection**: Monitors browser closure to automatically stop recording

### Database Layer
- **SQLite**: Primary database for test history, learned tasks, and execution logs
- **LearnedTask Model**: Stores task definitions with versioning and parent-child relationships
- **TaskExecution Model**: Tracks execution history for feedback and analytics
- **Vector Store**: FAISS-based vector index for semantic task similarity search

## 3. External Dependencies

### AI & Language Models
- **OpenAI GPT-4o-mini**: Primary LLM for Browser-Use engine and task generation
- **OpenAI GPT-4o**: Advanced healing and multi-strategy generation (optional upgrade)
- **Google Gemini**: Embedding generation for semantic task search (768-dim vectors)

### Browser Automation
- **Playwright**: Core browser automation library (Python async API)
- **Playwright MCP Server**: Node.js server providing Model Context Protocol tools
- **Browser-Use Library**: Python library for LLM-powered autonomous browsing

### Web Framework & Communication
- **Flask**: Primary web framework for REST API and web UI
- **Flask-SocketIO**: Real-time bidirectional communication for agent coordination
- **Gunicorn + Gevent**: Production WSGI server with async worker support
- **CORS**: Cross-origin resource sharing for API access

### Data & Storage
- **SQLite**: Embedded database (via Flask-SQLAlchemy)
- **FAISS**: Facebook's similarity search library for vector operations
- **NumPy**: Numerical operations for vector normalization and manipulation

### ML & Processing
- **scikit-learn**: Machine learning utilities for learning engine
- **Pillow**: Image processing for screenshots

### Configuration & Environment
- **python-dotenv**: Environment variable management with .env file support
- **configparser**: INI-based configuration files for engine settings

### Utilities
- **tenacity**: Retry logic with exponential backoff decorators
- **psutil**: Process management for port termination scripts
- **Rich**: Terminal output formatting for CLI tools

### Node.js Dependencies
- **@playwright/mcp**: Official Playwright MCP server package
- **playwright & playwright-core**: Browser automation (Node.js version)
- **@modelcontextprotocol/sdk**: MCP protocol implementation

## 4. Key Design Patterns

### Security Architecture
- API keys stored in environment variables (never in source code)
- Code validation sandbox with restricted imports and dangerous pattern detection
- Input sanitization for all user-provided instructions
- Rate limiting per client with in-memory tracking

### Error Handling Strategy
- Multi-level retry with exponential backoff for transient failures
- AI-powered error analysis and code healing for locator failures
- Graceful degradation when AI services unavailable
- Comprehensive logging at INFO level for debugging

### Performance Optimizations
- Engine instance caching to avoid repeated browser launches
- Locator caching for frequently accessed elements
- Parallel strategy testing for healing attempts
- Debounced input recording to reduce noise

### Configuration Management
- Environment-based configuration with .env files
- INI files for engine-specific settings (max_steps, timeouts, model selection)
- Runtime configuration overrides via API parameters
- Separate configs for browser, automation, retry, and performance settings