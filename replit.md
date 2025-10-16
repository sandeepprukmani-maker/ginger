# Overview

This is a Playwright MCP (Model Context Protocol) server implementation that enables AI agents to control and automate web browsers through the MCP protocol. The project serves as a bridge between AI models (particularly OpenAI) and Playwright browser automation, allowing natural language commands to be translated into browser actions. It can be run as a command-line tool or through a web interface.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Components

**MCP Server Architecture**
- Implements the Model Context Protocol to expose Playwright browser automation capabilities as MCP tools
- Built as an npm package (`@playwright/mcp`) that can be installed and run as a CLI tool via `mcp-server-playwright`
- Uses Playwright's alpha version (1.57.0-alpha) for cutting-edge browser automation features
- Designed to work with MCP clients (like Claude Desktop) to enable AI-driven browser control

**Automation Engine Design**
- `PlaywrightAutomationEngine` class handles actual browser automation execution
- Supports multiple browser actions: navigate, click, fill forms, screenshot capture, etc.
- Headless browser mode by default for efficient automation
- Async/await pattern throughout for non-blocking operations

**Web Interface Layer**
- Flask-based web UI (`web_ui.py`) provides a visual interface for the automation engine
- Persistent event loop running in a separate thread to handle async operations from Flask's sync context
- Global MCP app instance initialized once and reused across requests
- Coroutine execution bridge (`run_coroutine`) to safely execute async code from sync Flask routes

**AI Integration Pattern**
- OpenAI client integration for translating natural language to browser actions
- Tool/function calling pattern to map AI decisions to Playwright commands
- Environment variable based API key configuration

## Technology Stack

**Backend Runtime**
- Node.js (>=18) for the MCP server component
- Python with asyncio for the automation engine and web interface
- Flask for HTTP server functionality

**Browser Automation**
- Playwright as the core automation framework
- Supports Chromium, Firefox, and WebKit browsers
- Alpha version tracking with automated config updates from upstream Playwright

**Development Workflow**
- Multiple test configurations (Chrome, Firefox, WebKit, Docker)
- Automated README updates via npm scripts
- Docker support for containerized testing

# External Dependencies

**Primary Dependencies**
- `playwright` and `playwright-core` (1.57.0-alpha): Core browser automation
- `@modelcontextprotocol/sdk`: MCP protocol implementation
- `@playwright/test`: Testing framework for browser automation tests

**AI/ML Services**
- OpenAI API: Required for natural language to automation translation
- API key configured via `OPENAI_API_KEY` environment variable

**Web Framework**
- Flask: Python web server for UI
- Standard Flask templating for HTML rendering

**Development Tools**
- Zod with JSON Schema conversion for type validation and API contracts
- TypeScript type definitions (@types/node) for Node.js development
- Docker for containerized testing environments

**Testing Infrastructure**
- Multiple browser test profiles (Chrome, Firefox, WebKit)
- Docker-based testing with MCP_IN_DOCKER environment flag
- Playwright Test as the test runner