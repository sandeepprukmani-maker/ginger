# Self-Healing Browser Automation System

A production-ready Flask web application for self-healing browser automation using browser-use AI execution and Microsoft's Playwright MCP server as an intelligent fallback mechanism.

## Features

- **Natural Language Instructions**: Execute browser automation tasks using plain English
- **Two-Tier Healing System**: 
  - First attempt: browser-use AI-powered healing
  - Fallback: Microsoft Playwright MCP server for robust locator recovery
- **Real-Time Monitoring**: WebSocket-based live updates of execution progress
- **Action Logging**: Complete history of all steps, locators, and healing events
- **Code Generation**: Automatically generate executable Playwright Python scripts with healed locators
- **Reporting Dashboard**: Statistics on healing success, sources, and locator stability
- **Production-Ready**: SQLAlchemy ORM, proper error handling, and comprehensive logging

## Architecture

### Components

1. **Browser-Use Executor**: AI-powered initial automation execution
2. **MCP Server Integration**: Microsoft Playwright MCP server for accessibility-based healing
3. **Healing Orchestrator**: Routes failed steps to appropriate healing mechanism
4. **Action Log Database**: SQLite persistence for all execution data
5. **Code Generator**: Creates Playwright scripts from healed action logs
6. **Flask Web App**: Dashboard UI with real-time WebSocket updates

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key (for browser-use)

### Setup

1. Install dependencies (already configured in Replit):
   - Python packages: flask, browser-use, playwright, sqlalchemy, etc.
   - Node packages: @playwright/mcp

2. Configure environment variables via Replit Secrets:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SESSION_SECRET`: Flask session secret (already configured)

3. The application will automatically:
   - Create the SQLite database
   - Initialize all required directories
   - Install Playwright browsers

## Usage

### Starting the Application

The Flask server runs on port 5000 with WebSocket support.

### Executing Tasks

1. Enter a natural language instruction in the dashboard
2. Click "Execute with Healing"
3. Monitor real-time execution progress
4. View healing attempts and their sources
5. Download generated Playwright script

### Example Instructions

- "Go to google.com and search for 'browser automation'"
- "Navigate to github.com, click the sign in button, and fill the username field with 'testuser'"
- "Open example.com and click on the contact us link"

## Healing Flow

1. **Initial Execution**: browser-use attempts to execute the instruction
2. **Failure Detection**: Monitor detects element not found, timeout, or other errors
3. **Browser-Use Healing**: Retry with browser-use AI (up to 2 attempts)
4. **MCP Fallback**: If browser-use fails, Microsoft Playwright MCP server takes over
5. **Locator Update**: Successful healing updates action log with healed locator
6. **Code Generation**: Generate Playwright script with all healed locators

## API Endpoints

- `GET /`: Main dashboard
- `GET /api/tasks`: List all tasks
- `GET /api/tasks/<id>`: Get task details
- `GET /api/tasks/<id>/logs`: Get action logs
- `GET /api/tasks/<id>/healing`: Get healing events
- `POST /api/tasks/<id>/generate-script`: Generate Playwright script
- `GET /api/tasks/<id>/download-script`: Download generated script
- `GET /api/stats`: Get dashboard statistics
- `GET /health`: Health check endpoint

## WebSocket Events

### Client → Server
- `execute_task`: Submit new automation task

### Server → Client
- `task_created`: Task created successfully
- `task_update`: Task status changed
- `step_update`: Action step completed
- `healing_attempt`: Healing attempt in progress
- `healing_fallback`: Switched to fallback healing
- `healing_event`: Healing attempt result
- `task_complete`: Task execution finished
- `task_error`: Task execution error

## Configuration

Edit `config/config.yaml` to adjust:

- Retry thresholds
- Timeout settings
- Browser configuration
- MCP server options
- Export directories

## Database Schema

### Tables

1. **tasks**: Main task records
2. **action_logs**: Individual step execution logs
3. **healing_events**: Healing attempt records

All tables include comprehensive metadata for debugging and analysis.

## Generated Scripts

Scripts are saved in `data/generated_scripts/` and include:

- All successful and healed steps
- Current working locators
- Error handling
- Async/await Playwright patterns
- Ready to execute independently

## Technology Stack

- **Backend**: Flask, Flask-SocketIO, SQLAlchemy
- **Automation**: browser-use, Playwright, Microsoft Playwright MCP
- **Frontend**: Bootstrap 5, Socket.IO, Chart.js
- **Database**: SQLite with WAL mode
- **AI/LLM**: OpenAI GPT-4

## License

MIT License
