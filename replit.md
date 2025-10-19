# VisionVault - AI-Powered Browser Automation

## Overview
VisionVault is an intelligent browser automation platform that converts natural language commands into executable Playwright code. It features advanced AI capabilities including self-healing, vision-based analysis, and continuous learning from past executions.

## Current State
✅ **Fully configured and running on Replit**
- Flask web server running on port 5000
- Playwright with Chromium browser installed
- All Python dependencies installed
- System dependencies configured for browser automation
- Database initialized

## Project Architecture

### Core Components
1. **Web Interface** (`visionvault/web/`)
   - Flask-SocketIO web application
   - Real-time browser automation dashboard
   - Teaching mode for recording interactions
   - Task library with semantic search

2. **Browser Automation** (`visionvault/agents/`)
   - Playwright-based test executor
   - Self-healing execution engine
   - Recording session manager
   - Browser manager with context handling

3. **AI Services** (`visionvault/services/`)
   - Code validator and generator
   - DOM inspector for intelligent element detection
   - Multi-strategy healing engine
   - Self-learning engine that improves over time
   - Vector store for semantic task search
   - Intelligent planner for pre-execution analysis
   - MCP automation manager for enhanced browser control

4. **MCP Integration** (`mcp/`)
   - Model Context Protocol for advanced automation
   - Vision analyzer using GPT-4
   - Session memory and browser recorder
   - Natural language automation interface

### Key Features
- **Dual Automation Engines**: Choose between Legacy (Playwright code generation) or MCP (Enhanced direct automation)
- **Natural Language Commands**: Convert plain English to Playwright code or direct browser actions
- **Headless/Headful Modes**: Toggle between invisible background execution or visible browser window
- **Self-Healing**: Automatically fixes failed automation attempts
- **Vision Analysis**: Uses GPT-4 Vision to understand page structure
- **Teaching Mode**: Record browser interactions to generate code
- **Persistent Learning**: Learns from successes and failures
- **Semantic Search**: Find similar tasks using AI embeddings
- **Real-time Updates**: WebSocket-based live execution monitoring with progress streaming

## Automation Engines

VisionVault offers two powerful automation engines:

### 1. Legacy Engine (Playwright Code Generation)
- **How it works**: AI generates Playwright code from natural language, then executes it
- **Best for**: Code review, learning automation, custom modifications
- **Features**: Self-healing, intelligent code reuse, semantic search
- **Output**: Generated Python/JavaScript code visible in dashboard

### 2. MCP Engine (Enhanced Direct Automation)
- **How it works**: Model Context Protocol directly controls browser via intelligent action planning
- **Best for**: Complex workflows, perfect execution, minimal intervention
- **Features**: Vision-based analysis, adaptive strategies, real-time progress streaming
- **Output**: Live action logs and screenshots, no code generation needed
- **Requires**: OPENAI_API_KEY for AI action planning

**Browser Modes** (Available in both engines):
- **Headless**: Invisible browser, faster execution, ideal for background tasks
- **Headful**: Visible browser window, watch automation in real-time (requires local agent)

## Configuration

### Required API Keys (Optional but Recommended)
The application works without API keys but features are limited:

- `OPENAI_API_KEY` - Enables AI code generation, MCP automation, and self-healing
- `GEMINI_API_KEY` - Enables semantic task search and embeddings
- `SESSION_SECRET` - Already configured for Flask sessions

**To enable full features:**
1. Click the "Secrets" tab in Replit
2. Add `OPENAI_API_KEY` with your OpenAI API key
3. Add `GEMINI_API_KEY` with your Google AI API key

Without these keys, the app gracefully degrades:
- ⚠️ AI code generation disabled (requires OPENAI_API_KEY)
- ⚠️ MCP automation disabled (requires OPENAI_API_KEY)
- ⚠️ Semantic search disabled (requires GEMINI_API_KEY)
- ⚠️ Intelligent planner disabled (requires OPENAI_API_KEY)
- ✅ Manual Playwright code execution still works
- ✅ Teaching mode recording still works

### Workflows
- **Server**: Runs Flask application on port 5000
  - Command: `python run_server.py`
  - Serves web interface and API endpoints
  - Handles WebSocket connections for real-time updates

### Database
- SQLite database at `data/automation.db`
- Stores execution history, learned tasks, and task executions
- Automatically initialized on first run
- Vector embeddings stored in `data/vector_index.faiss`

## Development

### File Structure
```
visionvault/
├── web/              # Flask web application
│   ├── app.py       # Main Flask app with routes
│   └── templates/   # HTML templates
├── agents/          # Agent components
│   ├── main.py      # Main agent entry point
│   ├── test_executor.py
│   └── healing_engine.py
├── services/        # AI and automation services
│   ├── executor.py
│   ├── healing_executor.py
│   ├── self_learning_engine.py
│   └── vector_store.py
└── core/            # Core models and database

mcp/                 # Model Context Protocol
├── src/automation/  # Automation modules
│   ├── ai_generator.py
│   ├── vision_analyzer.py
│   └── browser_engine.py
└── nl_automation_mcp.py

data/                # Data storage
├── automation.db    # SQLite database
├── vector_index.faiss
└── uploads/         # Screenshots and logs
```

### Running Locally
The server auto-starts via the workflow. To run manually:
```bash
python run_server.py
```

### Running an Agent (Optional)
To enable distributed execution with agents:
```bash
python run_agent.py
```

## Deployment
Configured for Replit Autoscale deployment:
- Uses Gunicorn with gevent workers
- Optimized for stateless web requests
- Automatic scaling based on traffic

## Technology Stack
- **Backend**: Python 3.11, Flask, Flask-SocketIO
- **Browser Automation**: Playwright
- **AI**: OpenAI GPT-4, Google Gemini
- **Database**: SQLite, FAISS vector store
- **ML**: scikit-learn, numpy
- **Frontend**: HTML, CSS, JavaScript (Socket.IO client)

## Usage Examples

1. **Natural Language Automation**
   - Navigate to the dashboard
   - Enter: "Go to Google and search for Python tutorials"
   - Click "Execute Automation"
   - Watch AI generate and execute Playwright code

2. **Teaching Mode**
   - Click "Teaching Mode" in sidebar
   - Perform actions in the browser
   - System records and generates code automatically

3. **Task Library**
   - Browse previously executed tasks
   - Search similar tasks semantically
   - Reuse and adapt existing code

## Notes
- Playwright runs in headless mode by default for performance
- Screenshots are captured for all executions
- The system learns from every execution to improve accuracy
- Self-healing attempts up to 2 retries before manual intervention

## Recent Changes
- **2025-10-19**: MCP Integration Complete
  - Integrated Model Context Protocol (MCP) as second automation engine
  - Added automation engine selector in dashboard (Legacy vs MCP)
  - Implemented headless/headful browser mode toggle
  - Created MCPAutomationManager service for async execution
  - Added real-time progress streaming via Socket.IO
  - Installed Python MCP SDK and required dependencies (tenacity, rich, mcp)
  - Installed Node.js @playwright/mcp package
  - Updated Flask `/api/execute` endpoint to support dual engines
  - Maintained full backward compatibility with legacy Playwright engine

- **2025-10-18**: Initial Replit setup
  - Installed Python 3.11 and all dependencies
  - Configured Playwright with Chromium browser
  - Set up system dependencies for browser automation
  - Created Flask server workflow on port 5000
  - Configured deployment settings
  - Added comprehensive .gitignore for Python project
