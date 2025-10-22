# AI Browser Automation Agent

## Overview
This is a Flask-based web application that provides AI-powered browser automation using OpenAI's GPT models. The application can control web browsers through natural language instructions, supporting two different automation engines with automatic fallback.

## Current Status
✅ Successfully migrated to Replit environment
✅ All dependencies installed and configured
✅ PostgreSQL database provisioned
✅ OpenAI API key configured
✅ Application running on port 5000

## Project Architecture

### Technology Stack
- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL (via Neon)
- **AI/LLM**: OpenAI GPT-4o-mini
- **Automation Engines**: 
  - browser-use library
  - Playwright MCP (Model Context Protocol)
- **Server**: Gunicorn with auto-reload for development

### Key Components
1. **src/web/**: Flask web application
   - `routes.py`: API endpoints and route handlers
   - `services/`: Automation engine implementations
     - `browser_use/`: Browser-use engine adapter
     - `playwright_mcp/`: Playwright MCP engine adapter
     - `engine_manager.py`: Engine orchestration with fallback logic
   - `static/`: CSS and JavaScript assets
   - `templates/`: HTML templates

2. **src/automation/**: Automation utilities
   - `automation_engine.py`: Core automation logic
   - `playwright_code_generator.py`: Code export functionality
   - `self_healing_executor.py`: Self-healing automation
   - `examples/`: Example automation scripts

3. **llm_client.py**: Centralized LLM client factory for OpenAI integration

## Features
- Natural language browser automation
- Dual-engine support with automatic fallback (browser-use → Playwright MCP)
- Export automation as Playwright code (Python or JavaScript)
- Self-healing automation capabilities
- Real-time execution feedback

## Environment Variables
- `OPENAI_API_KEY`: Required for AI automation
- `DATABASE_URL`: PostgreSQL connection (auto-configured)
- `SESSION_SECRET`: Flask session security (auto-configured)

## Recent Changes
- **2025-10-22**: Migrated from Replit Agent to Replit environment
- **2025-10-22**: Fixed security issue - removed hardcoded API key
- **2025-10-22**: Configured proper environment variable handling for OpenAI API
- **2025-10-22**: Fixed browser-use integration - created ChatOpenAIWithExtras wrapper
- **2025-10-22**: Resolved Pydantic v2 compatibility using ConfigDict(extra='allow')
- **2025-10-22**: Added model property for full browser-use compatibility

## Running the Application
The application runs automatically via the "Start application" workflow:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

Access the application at: `https://<your-replit-url>.repl.co`

## API Endpoints
- `GET /`: Main application interface
- `POST /api/execute`: Execute browser automation instruction
- `GET /api/engines`: Get available automation engines
- `POST /api/reset`: Reset agent state
- `POST /api/export-playwright`: Export automation as Playwright code
- `GET /health`: Health check endpoint

## User Preferences
None specified yet.

## Next Steps
The application is fully functional and ready for use. You can now:
1. Enter natural language instructions to automate browser tasks
2. Choose between different automation engines
3. Export successful automations as Playwright code
4. Build upon this foundation for your specific automation needs
