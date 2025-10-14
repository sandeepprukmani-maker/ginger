# VisionVault - Browser Automation Framework

## Overview
VisionVault is an intelligent browser automation framework that uses AI to generate, execute, and heal Playwright test scripts. The system can convert natural language commands into executable browser automation code, and automatically fix failing tests using multiple AI-powered strategies.

## Project Architecture

### Core Components

1. **Web Application** (`visionvault/web/`)
   - Flask-based web server with SocketIO for real-time communication
   - REST API for test history and task management
   - Serves the web UI for creating and managing automation tasks

2. **AI Services** (`visionvault/services/`)
   - **Code Generation**: Uses OpenAI GPT-4 to convert natural language to Playwright code
   - **Intelligent Planner**: Pre-execution analysis and risk assessment
   - **Self-Learning Engine**: Learns from past executions to improve success rates
   - **Semantic Search**: Vector-based task similarity search using Gemini embeddings
   - **Multi-Strategy Healer**: Attempts multiple healing approaches in parallel

3. **Agent System** (`visionvault/agents/`)
   - Local agent that connects to server for distributed execution
   - Browser automation execution and recording
   - Healing engine for fixing failed tests

4. **Database** (`visionvault/core/`)
   - SQLite-based storage for learned tasks and execution history
   - Task versioning and success/failure tracking

## Recent Changes
- **2025-10-14 (Latest)**: Enhanced healing flow and UI improvements ✅
  - **IMPROVED: Healing Flow** - AI healing now attempts first before manual intervention
    - Attempts 1-4: Automatic AI healing (step-by-step, multi-strategy, locator validation)
    - Attempt 5: Manual widget shown only as last resort if AI healing fails
    - Ensures user is only prompted when AI cannot fix the issue automatically
  - **IMPROVED: Script Panels UI** - Clean code display without decorative elements
    - Generated Script panel now displays only code (no extra headers/badges)
    - Healed Script panel now displays only code (no extra headers/badges)
    - Cleaner, more focused developer experience

- **2025-10-14 (Earlier)**: Project successfully imported and healing system fixed ✅
  - Installed Python 3.11 and all required dependencies
  - Configured Playwright browser automation with Chromium
  - Set up OpenAI and Gemini API keys for AI features
  - Workflow configured and running on port 5000 with Gunicorn
  - All AI services initialized successfully (code generation, semantic search, self-learning)
  - **FIXED: AI Healing System** - Complete healing flow now working end-to-end
    - Server properly processes healing requests: retrieves code, regenerates with AI, saves to DB, sends retry
    - Agent keeps browser open across healing attempts instead of closing immediately
    - Max retry protection (5 attempts) prevents infinite loops
    - Proper cleanup when healing completes or max retries reached
    - Browser lifecycle: stays open → waits for healed code → retries → repeats until success or max attempts
  - **FIXED: Screenshot route** - Optimized with cached absolute paths, screenshots now load correctly
  - **FIXED: Security vulnerability** - Removed hardcoded API keys, now uses environment variables
  - Previous fixes maintained: cache-control headers, Playwright API updates

## Environment Setup

### Required Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for code generation (optional but recommended)
- `GEMINI_API_KEY`: Google Gemini API key for semantic search (optional)
- `SESSION_SECRET`: Flask session secret (defaults to dev key if not set)

### Dependencies
- Python 3.11
- Flask, Flask-SocketIO for web server
- Playwright for browser automation
- OpenAI for AI code generation
- Google Generative AI for embeddings
- scikit-learn, numpy, faiss-cpu for ML features

## Running the Application

The application runs via Gunicorn with gevent workers for async support:
```bash
gunicorn -c config/gunicorn.conf.py visionvault.web.app:app
```

The server binds to `0.0.0.0:5000` for Replit compatibility.

## Key Features
1. **Natural Language to Code**: Converts commands like "go to google.com and search for cats" into Playwright code
2. **Intelligent Planning**: Pre-analyzes commands to predict issues and optimize strategies
3. **Self-Learning**: Improves over time by learning from successful and failed executions
4. **Semantic Task Reuse**: Finds and reuses similar task code from history
5. **Auto-Healing**: Multiple AI strategies to fix broken tests automatically
6. **Recording Mode**: Record browser interactions to generate code

## Database Schema
- `test_history`: Execution history with generated code and results
- `learned_tasks`: Persistent task library with embeddings for similarity search
- `task_executions`: Execution feedback for self-learning engine

## User Preferences
- None set yet
