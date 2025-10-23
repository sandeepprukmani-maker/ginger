# Self-Healing Browser Automation System

## Project Overview

Production-ready Flask web application that implements a self-healing browser automation system. The system uses browser-use for AI-powered automation with Microsoft Playwright MCP server as an intelligent fallback for locator healing.

## Recent Changes

- **2025-10-23**: Initial project creation
  - Complete Flask application with WebSocket support
  - Database models for tasks, action logs, and healing events
  - Browser-use service integration
  - Microsoft Playwright MCP server integration
  - Healing orchestrator with two-tier healing logic
  - Code generator for Playwright scripts
  - Professional dashboard UI with real-time monitoring

## Project Architecture

### Backend Services

1. **Database Layer** (`app/models/database.py`)
   - SQLAlchemy ORM with SQLite
   - Tables: tasks, action_logs, healing_events
   - DatabaseManager for session management

2. **Browser-Use Service** (`app/services/browser_use_service.py`)
   - AI-powered automation using browser-use library
   - OpenAI GPT-4 integration
   - Single step execution for healing

3. **MCP Server Service** (`app/services/mcp_service.py`)
   - Microsoft Playwright MCP server integration
   - Subprocess management for MCP server
   - JSON-RPC communication
   - Accessibility-based locator generation

4. **Healing Orchestrator** (`app/services/healing_orchestrator.py`)
   - Two-tier healing system
   - Browser-use healing first (2 retries)
   - MCP fallback healing (2 retries)
   - Real-time WebSocket updates

5. **Code Generator** (`app/services/code_generator.py`)
   - Generates executable Playwright Python scripts
   - Uses healed locators from action logs
   - Includes error handling and best practices

### Frontend

- **Dashboard** (`app/templates/index.html`)
  - Task submission form
  - Real-time execution monitor
  - Statistics dashboard
  - Task history table
  - Task detail modal

- **JavaScript** (`app/static/js/app.js`)
  - Socket.IO client for WebSocket communication
  - Real-time event handling
  - REST API integration
  - Bootstrap UI interactions

### Configuration

- **YAML Config** (`config/config.yaml`)
  - Healing parameters (retries, timeouts)
  - Browser settings
  - MCP server configuration
  - Export directories

- **Environment Variables**
  - OPENAI_API_KEY: Required for browser-use
  - SESSION_SECRET: Flask session security (configured)

## User Preferences

- Production-ready application with NO placeholders
- Real Microsoft Playwright MCP server integration
- Actual browser-use AI automation
- Full working implementation

## Dependencies

### Python
- Flask 3.x (web framework)
- Flask-SocketIO 5.x (WebSocket support)
- browser-use (AI automation)
- playwright (browser control)
- SQLAlchemy 2.x (ORM)
- pydantic (data validation)
- APScheduler (background tasks)
- eventlet (async worker)

### Node.js
- @playwright/mcp (Microsoft Playwright MCP server)

## Running the Application

The Flask server runs on port 5000 with:
- WebSocket support via Flask-SocketIO
- Eventlet async worker
- Real-time bidirectional communication
- SQLite database with WAL mode

## Key Features

1. **Natural Language Automation**: Submit tasks in plain English
2. **Self-Healing**: Automatic locator recovery on failures
3. **Two-Tier Healing**: browser-use AI → MCP server fallback
4. **Real-Time Updates**: Live WebSocket monitoring
5. **Code Generation**: Export working Playwright scripts
6. **Comprehensive Logging**: Full audit trail of all actions
7. **Statistics Dashboard**: Healing metrics and success rates

## API Endpoints

- REST API for task management
- WebSocket events for real-time updates
- Script generation and download
- Statistics and reporting

## Database Schema

All tables use SQLAlchemy ORM with proper relationships and indexes for production use.
