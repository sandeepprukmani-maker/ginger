# VisionVault - AI-Powered Browser Automation

## Overview
VisionVault is an AI-powered browser automation tool that converts natural language commands into executable Playwright code. The system features automated healing for broken tests and persistent learning capabilities.

## Project Type
- **Language**: Python 3.11
- **Framework**: Flask + Socket.IO
- **Automation**: Playwright
- **AI**: OpenAI (optional)
- **Database**: SQLite (with optional vector search using FAISS)

## Current State
The application has been successfully set up to run in the Replit environment:
- ✅ All Python dependencies installed
- ✅ Playwright Chromium browser installed
- ✅ Web server configured to run on 0.0.0.0:5000
- ✅ CORS configured for all origins (required for Replit proxy)
- ✅ Workflow configured for development
- ✅ Deployment configured (VM type for stateful operation)

## Key Features
1. **Natural Language to Code**: Convert plain English to Playwright automation scripts
2. **Intelligent Code Reuse**: Automatically reuses code and locators from existing tasks when generating new automation
3. **Test Execution**: Run automation scripts in headless or headful mode
4. **Automated Healing**: Auto-fix broken locators when UI elements change
5. **Persistent Learning**: Store and reuse successful automation tasks
6. **Semantic Search**: Find similar tasks using vector embeddings (requires Gemini API key)
7. **Agent-Based Execution**: Distribute automation across connected agents

## Project Architecture

### Main Components
- **Web Server** (`visionvault/web/app.py`): Flask application with Socket.IO for real-time communication
- **Agents** (`visionvault/agents/`): Remote execution agents with healing capabilities
- **Services** (`visionvault/services/`): Core automation services (executor, healing, code validation, vector store)
- **Core** (`visionvault/core/`): Database models and schemas

### Entry Points
- `run_server.py`: Start the web server (port 5000)
- `run_agent.py`: Start an automation agent

## Environment Configuration

### Required Environment Variables
None required for basic operation.

### Optional Environment Variables
- `OPENAI_API_KEY`: Enable AI code generation (uses GPT-4o-mini)
- `GEMINI_API_KEY`: Enable semantic search with Gemini embeddings (text-embedding-004)
- `SESSION_SECRET`: Flask session secret (defaults to dev key if not set)
- `PORT`: Server port (defaults to 5000)

## Development Setup

### Running the Server
The server is automatically started via the "Server" workflow which runs:
```bash
python run_server.py
```

### Running the Agent (Optional)
To enable headful mode and distributed browser automation:

**On Replit (same environment as server):**
```bash
python run_agent.py
```

**On your local machine (connecting to Replit server):**
```bash
# Set the server URL to your Replit domain
export AGENT_SERVER_URL=https://<your-replit-domain>
python run_agent.py
```

**Auto-detection:** The agent automatically detects the server on ports 7890, 5000, 8000, or 3000 when running locally. You can override this with the `AGENT_SERVER_URL` environment variable

### Database
- Location: `data/automation.db`
- Type: SQLite
- Schema: Test history, learned tasks, task executions
- Vector index: `data/vector_index.faiss` (for semantic search)

## Deployment
- **Type**: VM (stateful, always-on)
- **Command**: `python run_server.py`
- **Port**: 5000
- **Host**: 0.0.0.0 (required for Replit)

## Notes
- The application works without API keys but with limited functionality:
  - Without OPENAI_API_KEY: AI code generation is disabled
  - Without GEMINI_API_KEY: Semantic search is disabled
- Playwright browser automation requires system dependencies (automatically handled in Replit)
- SocketIO is configured with gevent for async support
- CORS is enabled for all origins to support Replit's iframe proxy
- Embeddings use Google Gemini (768 dimensions) instead of OpenAI (1536 dimensions)

## Recent Changes
- **2025-10-12**: Migration to Replit environment completed
  - Replaced OpenAI embeddings with Google Gemini embeddings (text-embedding-004)
  - Removed hardcoded API keys for security
  - Separated OPENAI_API_KEY (for code generation) and GEMINI_API_KEY (for semantic search)
  - Configured Flask to bind to 0.0.0.0:5000
  - Created .gitignore for Python project
  - Set up development workflow
  - Configured VM deployment
  - Enhanced recording functionality:
    - Auto-stop recording when browser closes
    - Extract and display actions with locators
    - Direct save to task library from recordings
    - Improved persistent learning integration
  - History re-execution feature:
    - Added API endpoint to re-run tests from history
    - Automatically uses healed script when available (falls back to generated script)
    - History view loads command in read-only prompt with visual indicator
    - Execute button detects history mode and uses appropriate API
    - Displays script source (healed vs generated) with color-coded badges
  - **2025-10-13**: Agent configuration fixes & Intelligent Code Reuse
    - Fixed hardcoded server URL in agent config (was 7890, now auto-detects port 5000)
    - Added auto-detection for local server ports
    - Added AGENT_SERVER_URL environment variable for remote connections
    - **Intelligent Code Reuse System**:
      - System now searches for similar tasks (top 3) before generating code
      - Three-tier reuse strategy:
        * >75% similarity: Use existing task as-is
        * 30-75% similarity: AI reuses code/locators from similar tasks, generates only missing parts
        * <30% similarity: Generate from scratch
      - AI receives similar tasks as context to reuse URLs, selectors, patterns, and logic
      - Frontend displays reuse status with visual indicators
      - Significantly reduces code generation time and improves consistency
