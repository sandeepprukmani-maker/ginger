# AI Browser Automation Agent

## Overview

A professional-grade AI browser automation platform that combines OpenAI's language models with two automation engines: browser-use (langchain-based) and Playwright MCP (Model Context Protocol). The system provides both a web interface and CLI tools for executing browser automation tasks via natural language instructions.

The platform features intelligent engine fallback, self-healing code generation capabilities, and can convert AI-driven automations into maintainable Playwright scripts.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

**Dual-Interface Design**
- **Web Application**: Flask-based server providing REST API and browser UI for interactive automation
- **CLI Tools**: Direct command-line access for automation execution and code generation

The application uses a clean separation between web serving (`src/web/`) and core automation logic (`src/automation/`).

### Automation Engine Architecture

**Multi-Engine Strategy with Intelligent Fallback**

The system implements three execution modes managed by `EngineManager`:

1. **Auto Mode** (Default): Attempts browser-use first, falls back to Playwright MCP on failure
2. **Browser-use Mode**: Uses langchain + OpenAI for AI-driven browser automation
3. **Playwright MCP Mode**: Uses Model Context Protocol with structured tool calling

**Rationale**: Different automation tasks have different characteristics. Browser-use excels at complex, multi-step workflows with natural language understanding, while Playwright MCP provides more structured, reliable execution for simpler tasks. The fallback mechanism ensures high success rates.

**Engine Implementations**:
- `BrowserUseAutomationEngine`: Wraps browser-use library with langchain's ChatOpenAI
- `MCPAutomationEngine`: Integrates Playwright MCP via subprocess communication and BrowserAgent for OpenAI-based instruction interpretation

### Self-Healing Code Generation

**Two-Phase Approach**:

1. **Code Generation Phase**: `PlaywrightCodeGenerator` converts browser-use action history into reusable Playwright Python scripts with multiple fallback locator strategies
2. **Self-Healing Execution Phase**: `SelfHealingExecutor` runs generated code and uses browser-use AI to fix failed locators in real-time

**Design Decision**: Generated code includes multiple locator strategies (text, role, label-based) to reduce brittleness. When all strategies fail during execution, the AI intervenes in the same browser session to locate and interact with elements, then records the successful strategy for future use.

**Trade-offs**:
- Pro: Generated scripts are more maintainable than pure AI automation
- Pro: Self-healing reduces maintenance burden when pages change
- Con: Adds latency during healing attempts (mitigated by max 3 attempts)

### Frontend Architecture

**Technology**: Vanilla JavaScript with async/await for API communication

**Design Pattern**: Single-page application with client-side rendering
- Event-driven interaction model
- RESTful API consumption via fetch
- Real-time status updates and result display

**Rationale**: Keeps frontend lightweight and avoids build tooling complexity while maintaining professional UX.

### Communication Protocols

**MCP Integration via STDIO**

The Playwright MCP server runs as a subprocess with JSON-RPC communication over stdin/stdout:
- `MCPStdioClient` manages subprocess lifecycle and bidirectional communication
- Threading model: separate threads for reading stdout and stderr
- Request/response correlation via ID-based pending request tracking

**Design Decision**: STDIO transport chosen over HTTP for:
- Simpler deployment (no port management)
- Tighter process coupling (server dies with client)
- Lower latency for tool calls

### Configuration Management

Uses INI file (`config.ini`) for:
- OpenAI API keys and model selection
- Browser preferences (headless mode, browser type)
- MCP capabilities configuration

**Security Note**: Code warns against committing API keys and recommends environment variables for production.

## External Dependencies

### AI Services
- **OpenAI API**: Required for both automation engines
  - browser-use uses via langchain's `ChatOpenAI` wrapper
  - Playwright MCP uses via native `OpenAI` client
  - Default model: `gpt-4o-mini` (explicitly specified, not to be changed without user request)

### Browser Automation
- **browser-use**: AI-powered automation library (v0.5.9+) using langchain
- **Playwright**: Core browser automation (v1.57.0-alpha)
- **Playwright MCP Server** (`@playwright/mcp`): Model Context Protocol implementation for Playwright
  - Runs as Node.js subprocess via `tools/mcp-server/cli.js`
  - Provides structured browser tools via MCP

### Web Framework
- **Flask**: Python web server for REST API and template serving
- No database required (stateless design)

### Python Dependencies
- `langchain-openai`: LangChain's OpenAI integration
- `playwright`: Browser automation library
- `openai`: Official OpenAI Python client
- `browser-use`: Natural language browser automation

### Node.js Dependencies (MCP Server)
- `playwright`: Playwright Node.js package
- `playwright-core`: Core Playwright engine
- `@modelcontextprotocol/sdk`: MCP protocol implementation
- Various express/CORS middleware for MCP server capabilities

### Browser Requirements
- Chromium browser (detected via environment variable `CHROMIUM_PATH` or system PATH)
- Supports Chrome, Chromium, or chromium-browser binaries

### Configuration Files
- `config.ini`: Application configuration (API keys, browser settings)
- `package.json`: Node.js MCP server dependencies and metadata
- No database schema files (application is stateless)