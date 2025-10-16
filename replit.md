# Overview

This is an AI-powered UI testing system with **local agent execution** that combines Playwright MCP (Model Context Protocol) with LLM-based orchestration. The system consists of:

1. **Playwright MCP Server** - A Node.js/TypeScript wrapper around Microsoft's Playwright MCP tools, providing browser automation capabilities through the MCP protocol
2. **Python Web Application** - A Flask-based web interface that uses OpenAI's LLM to convert natural language commands into executable Playwright automation sequences
3. **Local Agent Executor** - Securely runs generated code in headful (visible browser) or headless mode

**What you can do:**
- Enter natural language test prompts (e.g., "navigate to google.com and search for Playwright")
- Get working Python Playwright code automatically
- Run the generated code locally with visible browser (headful mode)
- Toggle between headful/headless execution modes

# Recent Updates (October 16, 2024)

✅ **New: Local Agent with Headful Mode**
- Added secure local code execution with hash validation
- Headful/headless browser mode toggle
- Run generated Playwright code with visible browser
- Security: Only system-generated code can be executed (prevents arbitrary code execution)

✅ **Complete Web Application**
- Flask web interface on port 5000
- Playwright MCP server on port 3000
- AI-powered automation with OpenAI integration
- Full error handling and user-friendly UI

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

**Web Interface (Flask + HTML/CSS/JS)**
- Simple single-page application served by Flask
- Users enter natural language automation commands through a textarea
- Real-time status updates and results display
- Code generation output shown to users
- Example prompts provided for common automation tasks

**Chrome Extension (Optional)**
- React-based UI for browser tab selection
- WebSocket relay connection to MCP server
- Allows AI to interact with existing browser sessions and user profiles
- Tab management and connection status monitoring

## Backend Architecture

**Python Automation Engine** (`automation/`)
- `AutomationEngine`: Main orchestrator coordinating the workflow
- `LLMOrchestrator`: Converts natural language to automation steps using OpenAI GPT-5
- `PlaywrightMCPClient`: MCP client for communicating with Playwright server via stdio
- Generates executable Python Playwright code from automation steps
- Saves results and generated code to `output/` and `generated_code/` directories

**Node.js MCP Server Wrapper**
- Thin wrapper around Microsoft's Playwright MCP implementation
- Core MCP logic lives in `playwright/lib/mcp` (Microsoft's Playwright monorepo)
- Exposes browser automation tools through MCP protocol
- Supports multiple browsers (Chromium, Firefox, WebKit)
- Can run in headless or headed mode
- Supports Docker containerization for isolated testing

**Tool Capabilities System**
- Core automation: navigate, click, fill forms, take screenshots
- Tab management: multi-tab support
- Browser installation: automated browser setup
- Vision (opt-in): coordinate-based interactions
- PDF generation (opt-in): document creation
- Tracing (opt-in): execution recording and debugging

## Communication Flow

1. User enters natural language command in web UI
2. Flask app sends command to LLMOrchestrator
3. LLM analyzes available MCP tools and generates automation plan
4. PlaywrightMCPClient executes plan by calling MCP tools via stdio
5. Results and generated code are saved and displayed to user

## Testing Infrastructure

**Playwright Test Suite**
- Comprehensive test coverage using @playwright/test
- Tests for core tools (navigate, click, type, etc.)
- Extension-specific tests for browser tab connection
- Docker mode testing for containerized environments
- Custom fixtures for MCP client initialization

# External Dependencies

## Third-Party Services

**OpenAI API**
- Model: GPT-5 (latest as of August 2025)
- Purpose: Natural language to automation plan conversion
- Required: `OPENAI_API_KEY` environment variable
- Used by: `LLMOrchestrator` class

## NPM Packages

**Core Dependencies**
- `playwright` & `playwright-core` (1.57.0-alpha): Browser automation engine
- `@modelcontextprotocol/sdk`: MCP protocol implementation for client-server communication

**Development Dependencies**
- `@playwright/test`: Testing framework
- `@types/node`: TypeScript type definitions
- `zod-to-json-schema`: Schema conversion for tool definitions
- TypeScript, Vite, React (for extension UI)

## Python Packages

**Core Dependencies**
- `flask`: Web application framework
- `flask-cors`: Cross-origin resource sharing support
- `openai`: OpenAI API client for LLM integration
- `mcp`: Model Context Protocol Python client
- `playwright` (Python): For generated code execution

## Browser Dependencies

- Chromium/Chrome (default)
- Firefox (optional)
- WebKit (optional)
- Installed via Playwright's built-in installer (`npx playwright install`)

## Infrastructure

**MCP Server Communication**
- stdio (standard input/output) transport for local MCP server
- WebSocket relay for Chrome extension mode
- HTTP/HTTPS test servers for integration testing

**File System**
- `output/` directory: Automation results and execution logs
- `generated_code/` directory: Generated Python Playwright scripts
- Extension user data directory for persistent browser profiles