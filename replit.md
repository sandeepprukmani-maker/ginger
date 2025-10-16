# VisionVault - AI-Powered Browser Automation

## Overview
VisionVault is an intelligent browser automation platform that uses AI to create, execute, and heal web automation tests. The system leverages Playwright for browser automation and integrates with OpenAI and Google Gemini for intelligent code generation and semantic search capabilities.

## Project Architecture

### Core Components
- **Web Application** (`visionvault/web/`): Flask-based web server with Socket.IO for real-time communication
- **Agents** (`visionvault/agents/`): Browser automation agents that connect to the server and execute tests
- **Services** (`visionvault/services/`): Core automation services including:
  - Intelligent Planner: Pre-execution analysis and risk assessment
  - Self-Learning Engine: Learns from past executions to improve success rates
  - Healing Engine: Automatically fixes failing tests using AI
  - DOM Inspector: Analyzes web pages for optimal locator selection
  - Vector Store: Semantic search for similar learned tasks
- **Core Models** (`visionvault/core/`): Database models and data structures

### Technology Stack
- **Backend**: Python 3.11, Flask, Flask-SocketIO, Gunicorn
- **Browser Automation**: Playwright
- **AI/ML**: OpenAI GPT-4, Google Gemini, scikit-learn, FAISS
- **Database**: SQLite (development), PostgreSQL ready
- **Frontend**: Bootstrap 5, vanilla JavaScript

## Setup and Running

### Entry Points
1. **Web Server**: `python run_server.py` - Starts the Flask web application on port 5000
2. **Agent**: `python run_agent.py` - Starts the automation agent that connects to the server
3. **Both**: `python scripts/run_both.py` - Runs both server and agent together

### Required Environment Variables
- `OPENAI_API_KEY` (optional): For AI code generation and intelligent planning
- `GEMINI_API_KEY` (optional): For semantic search and embeddings
- `SESSION_SECRET` (optional): Flask session secret (auto-generated if not set)

### Database
- Uses SQLite by default (`data/automation.db`)
- Tables:
  - `test_history`: Execution history and test results
  - `learned_tasks`: Persistent learning knowledge base
  - `task_executions`: Execution feedback loop

## Key Features
1. **Natural Language to Code**: Convert commands to executable Playwright code
2. **Self-Healing Tests**: Automatically repair failing tests using multiple strategies
3. **Intelligent Planning**: Pre-execution analysis to predict and prevent failures
4. **Learning System**: Continuously improves from past executions
5. **Recording Sessions**: Capture user interactions to generate automation scripts
6. **DOM Intelligence**: Real-time page analysis for optimal element selection

## Recent Changes
- **2025-10-16**: MCP Integration for Production-Ready Reusable Scripts
  - **MCP Server Infrastructure** (`visionvault/mcp/server.py`): Created VisionVaultMCPServer with four intelligent tools:
    - `search_learned_tasks`: Search learning database for similar automation patterns
    - `analyze_dom`: Analyze DOM structure and suggest optimal selectors
    - `get_healing_strategies`: Get AI-powered healing strategies for failed selectors
    - `format_reusable_script`: Format healed scripts with documentation for production use
  - **MCP-Enhanced Code Generation** (`visionvault/mcp/client.py`): Built MCPEnhancedCodeGenerator and MCPEnhancedHealer
    - Leverages MCP tools to enhance code generation with learned tasks and DOM analysis
    - Produces clean, production-ready healed scripts with proper documentation
    - Includes improvement tracking and explanation of applied fixes
  - **Graceful Fallback Mechanism** (`visionvault/web/app.py`): 
    - System works with or without OpenAI API key
    - Falls back to basic code generation when AI is not available
    - MCP enhancements only activate when OpenAI client is configured
  - **Frontend Enhancement** (`visionvault/web/templates/index.html`):
    - Added "Reusable Production Script" panel with MCP-ENHANCED badge
    - Copy-to-clipboard functionality for easy script reuse
    - Displays improvements list showing all fixes applied during healing
    - Socket event handling for real-time reusable script delivery
  - **Production-Ready Output**: Healed scripts now include:
    - Full documentation with usage instructions
    - Comprehensive error handling
    - Step-by-step execution flow
    - All improvements and fixes clearly documented

- **2025-10-15**: Critical bug fixes and enhancements
  - **Data Contract Fix**: Fixed schema mismatch between DOMInspector and AdvancedLocatorValidator
    - DOMInspector now outputs camelCase keys (testId, ariaLabel, tag) matching validator expectations
    - Added missing 'tag' field to prevent KeyError crashes
  - **Safe Access Implementation**: AdvancedLocatorValidator now uses .get() for all field access
    - Prevents crashes when optional fields are missing
    - Added sensible defaults for all locator strategies
  - **Multi-Strategy Healing**: Implemented actual parallel strategy execution
    - Multi-strategy healing now executes on attempt 3 (previously just declared)
    - Tests multiple healing strategies in parallel and selects the best one
    - Comprehensive error handling for strategy failures
  - **Concurrency Fix**: Resolved gevent/asyncio mixing issues
    - Pure asyncio implementation with proper Event handling
    - Added result buffering for early agent responses
    - Thread-safe event signaling with event loop stored at initialization
  - **Error Handling**: Added comprehensive exception handling
    - MultiStrategyHealer gracefully handles strategy failures
    - Safe unpacking of results with fallback mechanisms

- **2025-10-15**: Initial import to Replit environment
  - Configured Python 3.11 environment
  - Installed all dependencies via pip
  - Installed Playwright with Chromium browser
  - Installed system dependencies for browser automation
  - Created data directories structure
  - Set up .gitignore for Python project

## User Preferences
(No user preferences recorded yet)

## Development Notes
- The application serves on port 5000 (required for Replit environment)
- Gunicorn is configured with gevent worker for Socket.IO compatibility
- The frontend communicates via WebSocket for real-time updates
- Screenshots and logs are stored in `data/uploads/`
