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
- **Intelligent Unified Engine**: Automatically selects the best automation strategy (MCP Direct or Code Generation) based on task complexity and historical performance
- **Natural Language Commands**: Convert plain English to browser actions
- **Adaptive Learning**: System learns which approach works best for different task types and improves over time
- **Headless/Headful Modes**: Toggle between invisible background execution or visible browser window
- **Self-Healing**: Automatically fixes failed automation attempts with progressive escalation
- **Vision Analysis**: Uses GPT-4 Vision to understand page structure
- **Teaching Mode**: Record browser interactions to generate code
- **Persistent Learning**: Learns from successes and failures, tracks strategy performance
- **Semantic Search**: Find similar tasks using AI embeddings
- **Real-time Updates**: WebSocket-based live execution monitoring with progress streaming

## Intelligent Automation System

VisionVault uses a **Unified Automation Engine** that intelligently combines two powerful approaches:

### Adaptive Strategy Selection
The system automatically analyzes each task and chooses the best approach:

**🚀 MCP Direct (Model Context Protocol)**
- **When used**: Simple tasks, single actions, high-confidence operations
- **How it works**: AI directly controls the browser via intelligent action planning
- **Advantages**: Fast execution, minimal overhead, real-time adaptation
- **Features**: Vision-based analysis, DOM scanning, fuzzy element matching

**🔧 Code Generation (Playwright)**
- **When used**: Complex multi-step workflows, tasks requiring code review
- **How it works**: AI generates executable Playwright Python code
- **Advantages**: Full control, debuggable, reusable, modifiable
- **Features**: Self-healing, intelligent code reuse, semantic similarity matching

### Progressive Escalation
If the primary strategy fails, the system automatically escalates:
1. **First attempt**: Selected strategy (MCP or CodeGen)
2. **Healing**: DOM scanning → Vision analysis → Multi-strategy healing
3. **Alternative strategy**: Falls back to the other approach if needed
4. **Manual widget**: Headful mode allows manual element selection

### Continuous Learning
The system tracks which strategy works best for different task patterns and automatically improves its decision-making over time.

**Browser Modes**:
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
- **2025-10-19**: Unified Automation Engine Complete
  - **Merged Legacy Playwright and MCP into ONE intelligent system**
  - Created UnifiedAutomationEngine with adaptive strategy selection
  - Implemented intelligent scoring system (analyzes complexity, confidence, DOM availability)
  - Built progressive escalation: MCP → CodeGen → Multi-strategy healing → Manual widget
  - Extended SelfLearningEngine to track strategy performance by task type
  - Added historical learning: System recommends strategies based on past success rates
  - **Simplified UI**: Removed manual engine selector - system auto-selects best approach
  - Updated Flask `/api/execute` endpoint to use unified orchestration
  - Added real-time strategy selection notifications via Socket.IO
  - Continuous learning: System improves decision-making over time
  - Maintained full backward compatibility with agents

- **2025-10-19**: MCP Integration
  - Integrated Model Context Protocol (MCP) as second automation engine
  - Implemented headless/headful browser mode toggle
  - Created MCPAutomationManager service for async execution
  - Added real-time progress streaming via Socket.IO
  - Installed Python MCP SDK and required dependencies

- **2025-10-18**: Initial Replit setup
  - Installed Python 3.11 and all dependencies
  - Configured Playwright with Chromium browser
  - Set up system dependencies for browser automation
  - Created Flask server workflow on port 5000
