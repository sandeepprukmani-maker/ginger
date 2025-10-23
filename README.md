# AI Browser Automation Agent

A professional hybrid-engine browser automation system powered by AI, offering intelligent automation with automatic fallback for maximum reliability through a modern Flask web interface.

## Overview

This project provides intelligent browser automation using natural language instructions. Users can choose between three powerful automation engines through an intuitive web interface, with the Hybrid engine providing the best of both worlds.

### Automation Engines

1. **Hybrid Engine** ⭐ **Recommended - Default**
   - **Intelligent Fallback**: Combines Browser-Use with Playwright MCP fallback
   - Attempts Browser-Use first for autonomous, intelligent automation
   - Automatically falls back to Playwright MCP if Browser-Use fails
   - Provides execution metadata showing which engine succeeded
   - **Best reliability**: Get the power of AI with the stability of tool-based control
   - Ideal for production use cases requiring high success rates

2. **Browser-Use Engine**
   - AI-powered automation with advanced reasoning capabilities
   - Uses the browser-use library with LLM reasoning
   - Autonomous task completion with minimal tool calls
   - Best for complex, multi-step workflows requiring adaptability

3. **Playwright MCP Engine**
   - Tool-based automation using Playwright's Model Context Protocol
   - Discrete, controllable browser actions
   - Fine-grained control over each automation step
   - Best for precise, repeatable tasks with predictable behavior

## Features

- **Hybrid Intelligence**: Smart automation with automatic fallback for reliability
- **Triple Engine System**: Choose between hybrid, AI-powered, or tool-based automation
- **Headless/Headful Modes**: Run browser invisibly for speed or visibly for debugging
- **Natural Language Instructions**: Describe tasks in plain English
- **Real-time Feedback**: See step-by-step execution progress with engine metadata
- **Modern Web Interface**: Clean two-column layout with configuration panel
- **Quick Examples**: Pre-loaded examples for common automation tasks
- **RESTful API**: Programmatic access to automation capabilities

## Architecture

### Directory Structure

```
.
├── app/                           # Flask web application
│   ├── __init__.py               # Application factory
│   ├── services/                 # Business logic layer
│   │   └── engine_orchestrator.py  # Engine coordination
│   ├── routes/                   # API endpoints
│   │   └── api.py                # REST routes
│   ├── templates/                # HTML templates
│   │   └── index.html
│   └── static/                   # Static assets
│       ├── css/style.css
│       └── js/app.js
├── hybrid_engine/                # Hybrid engine (recommended)
│   ├── __init__.py              # Package initialization
│   └── engine.py                # Intelligent fallback logic
├── playwright_mcp_codebase/      # Playwright MCP engine
│   ├── agent/                    # Conversation agent
│   │   └── conversation_agent.py
│   ├── client/                   # MCP STDIO client
│   │   └── stdio_client.py
│   └── config/                   # Configuration helpers
├── browser_use_codebase/         # Browser-Use engine
│   ├── engine.py                 # Browser-Use implementation
│   └── config/                   # Configuration helpers
├── main.py                       # Application entry point
├── cli.js                        # Playwright MCP server (Node.js)
├── config.ini                    # Configuration file
├── package.json                  # Node.js dependencies
└── pyproject.toml                # Python dependencies
```

### Technology Stack

**Backend:**
- Python 3.11+ with Flask web framework
- OpenAI GPT-4o-mini for AI reasoning
- Playwright (via browser-use and MCP)
- browser-use library for autonomous automation
- langchain-openai for LLM integration

**Frontend:**
- Modern HTML5/CSS3/JavaScript
- RESTful API communication
- Real-time status updates

**Infrastructure:**
- Subprocess-based MCP communication (Playwright)
- Async execution with thread-safe event loops (Browser-Use)
- Environment-based secret management

## Setup Instructions

### Prerequisites

- **Python 3.11+**: Required for async features
- **Node.js 18+**: Required for Playwright MCP server
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-browser-automation
```

#### 2. Install Python Dependencies

This project uses `uv` package manager with `pyproject.toml`.

Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install flask openai requests sseclient-py browser-use langchain-openai python-dotenv
```

#### 3. Install Node.js Dependencies

```bash
npm install
```

#### 4. Install Playwright Browsers

```bash
npx playwright install chromium
```

#### 5. Configure OpenAI API Key

**Option A: Environment Variable (Recommended)**
```bash
export OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Option B: Configuration File**
Edit `config.ini` and replace the placeholder:
```ini
[openai]
api_key = sk-your-actual-api-key-here
model = gpt-4o-mini
```

**Important**: For security, use environment variables in production. Never commit API keys to version control.

## Running the Application

### Start the Flask Server

```bash
python main.py
```

The server will start on `http://0.0.0.0:5000`

### Access the Web Interface

Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Web Interface

1. **Select Engine**: Choose between Browser-Use (AI-Powered) or Playwright MCP (Tool-Based)
2. **Configure Mode**: Toggle headless mode on/off
3. **Enter Instruction**: Describe your automation task in natural language
4. **Execute**: Click the Execute button and watch the automation happen
5. **View Results**: See step-by-step execution logs in real-time

### Example Instructions

```
Go to example.com
```

```
Navigate to google.com and search for 'browser automation'
```

```
Open github.com/trending and find the top repository
```

```
Go to reddit.com and find the top post on the homepage
```

## API Documentation

### Base URL
```
http://localhost:5000
```

### Endpoints

#### Execute Instruction
```http
POST /api/execute
Content-Type: application/json

{
  "instruction": "Go to example.com",
  "engine": "browser_use",
  "headless": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Task completed successfully",
  "steps": [...],
  "iterations": 3,
  "engine": "browser_use",
  "headless": false
}
```

#### List Available Tools
```http
GET /api/tools?engine=playwright_mcp
```

**Response:**
```json
{
  "success": true,
  "tools": [...],
  "engine": "playwright_mcp"
}
```

#### Reset Agent
```http
POST /api/reset
Content-Type: application/json

{
  "engine": "playwright_mcp"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Agent reset successfully",
  "engine": "playwright_mcp"
}
```

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "engines": {
    "browser_use": "available",
    "playwright_mcp": "available"
  },
  "message": "Dual-engine browser automation ready"
}
```

## Configuration

### config.ini

```ini
[server]
host = 0.0.0.0
port = 5000

[browser]
headless = true
browser = chromium

[openai]
api_key = YOUR_OPENAI_API_KEY_HERE
model = gpt-4o-mini
```

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key (overrides config.ini)
- `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS`: Automatically set by MCP client

## Deployment

### Development
The application runs on Flask's development server, suitable for testing and local development.

### Production

For production deployment:

1. **Use a production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn --workers 4 --bind 0.0.0.0:5000 main:app
   ```

2. **Configure environment variables** for all secrets

3. **Enable HTTPS** using a reverse proxy (nginx, Apache)

4. **Set up monitoring** and logging

### Replit Deployment

This project is configured for Replit VM deployment:
- Always-running, stateful instance
- MCP subprocess persistence
- Port 5000 (non-firewalled)

## How It Works

### Browser-Use Engine Flow

1. User submits natural language instruction
2. Flask server creates Browser-Use engine instance
3. Engine initializes fresh browser and event loop
4. GPT-4o-mini agent autonomously navigates and interacts
5. Actions are executed with AI reasoning
6. Results with action history returned to UI
7. Browser and event loop cleaned up

### Playwright MCP Engine Flow

1. User submits natural language instruction
2. Flask server retrieves cached MCP client and agent
3. OpenAI agent determines required browser tool calls
4. MCP client communicates with Playwright subprocess via JSON-RPC
5. Playwright executes discrete browser actions
6. Results returned step-by-step to UI

## Thread Safety

### Browser-Use Engine
- Creates fresh browser instance per request
- Uses new event loop for each execution
- No instance caching to prevent loop affinity issues
- Automatic cleanup in finally blocks

### Playwright MCP Engine
- Subprocess-based communication is thread-safe
- Instances cached by headless mode setting
- Shared across requests for efficiency

## Troubleshooting

### Port Already in Use
```bash
lsof -ti:5000 | xargs kill -9
```

### Missing OpenAI API Key
Set the environment variable or update config.ini

### Playwright Installation Issues
```bash
npx playwright install-deps chromium
npx playwright install chromium
```

### Browser Crashes
- Ensure sufficient memory (2GB+ recommended)
- Try headless mode for lower resource usage
- Check Playwright logs for specific errors

## Performance Considerations

### OpenAI API Costs
- Each instruction execution calls OpenAI API multiple times
- Browser-Use: 1-5 calls per instruction (autonomous)
- Playwright MCP: 2-10+ calls per instruction (iterative)
- Monitor usage at: https://platform.openai.com/usage

### Resource Usage
- **Headless mode**: ~200-500MB RAM per browser instance
- **Headful mode**: ~500MB-1GB RAM per browser instance
- **Recommended**: 4GB+ total system RAM for optimal performance

## Development

### Project Structure Guidelines

- **app/**: Flask application (routing and web interface only)
- **playwright_mcp_codebase/**: Isolated Playwright MCP implementation
- **browser_use_codebase/**: Isolated Browser-Use implementation
- **Keep concerns separated**: Each codebase is independent and testable

### Adding New Features

1. Identify which engine(s) the feature applies to
2. Implement in the appropriate codebase package
3. Update the orchestrator if coordination is needed
4. Add API routes if exposing new endpoints
5. Update this README

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Check the Troubleshooting section above
- Review console output for error messages
- Verify OpenAI API key is valid and has credits
- Ensure all dependencies are installed correctly

---

**Built with ❤️ using Playwright, browser-use, and OpenAI GPT-4o-mini**
