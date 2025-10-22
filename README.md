# AI Browser Automation Agent

> **Dual-engine browser automation platform powered by OpenAI and Playwright with intelligent fallback and self-healing capabilities**

## Overview

A professional-grade AI browser automation system offering both a web interface and CLI tools for intelligent browser automation. The system features:

- **Dual-Engine Architecture**: browser-use + Playwright MCP with automatic fallback
- **Web Interface**: User-friendly Flask application for interactive automation
- **Self-Healing Code Generation**: Convert automations into maintainable Playwright scripts
- **Production Ready**: Clean architecture with professional code organization

## Quick Start

### Web Application

```bash
# Start the Flask web server
python app.py
```

Then open your browser to `http://localhost:5000`

### CLI Automation

```bash
# Direct automation
python -m src.automation.cli "search for Python tutorials on Google"

# Generate reusable code
python -m src.automation.cli "fill out login form" --generate-code --output login.py

# Execute with self-healing
python -m src.automation.cli --execute-code login.py --verbose
```

## Features

### Web Application
- 🎨 **Interactive UI**: Clean, modern interface for browser automation
- 🔄 **Real-time Execution**: Stream results as automation runs
- 🔀 **Engine Selection**: Choose between browser-use, Playwright MCP, or auto-fallback
- 📤 **Code Export**: Convert executions to Playwright code (Python/JavaScript)
- 🛠️ **API Endpoints**: RESTful API for programmatic access

### Automation Engines
- **browser-use**: AI-powered automation with natural language understanding
- **Playwright MCP**: Model Context Protocol integration for structured automation
- **Auto Mode**: Intelligent fallback system (browser-use → MCP)

### Code Generation & Self-Healing
- 🔧 **Self-Healing Locators**: Automatically fixes broken selectors
- 📝 **Clean Code Output**: Production-ready Playwright scripts
- 🎯 **Multiple Strategies**: Text, role, ID, label, CSS, XPath with fallbacks
- 🔄 **AI Recovery**: Two-level recovery ensures automation never fails

## Architecture

```
ai-browser-automation/
├── src/                          # Core application code
│   ├── automation/              # CLI automation modules
│   │   ├── automation_engine.py
│   │   ├── playwright_code_generator.py
│   │   ├── self_healing_executor.py
│   │   ├── locator_utils.py
│   │   └── examples/
│   └── web/                     # Flask web application
│       ├── __init__.py          # Flask app factory
│       ├── routes.py            # API endpoints
│       ├── services/            # Business logic
│       │   ├── browser_use/     # 🤖 browser-use engine
│       │   │   ├── __init__.py
│       │   │   └── engine.py
│       │   ├── playwright_mcp/  # 🛠️ Playwright MCP engine
│       │   │   ├── __init__.py
│       │   │   ├── engine.py
│       │   │   ├── client.py
│       │   │   └── browser_agent.py
│       │   ├── automation_engine_interface.py
│       │   └── engine_manager.py
│       ├── static/              # CSS, JavaScript
│       └── templates/           # HTML templates
├── tools/                       # Development tools
│   └── mcp-server/             # Playwright MCP Node.js server
├── app.py                      # Web application entry point
├── pyproject.toml              # Python dependencies
└── config.ini                  # Application configuration
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for MCP server)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))

## Installation

### On Replit (Recommended)

Dependencies are pre-installed. Simply add your `OPENAI_API_KEY` when prompted.

### Local Installation

1. **Install Python dependencies**:
```bash
pip install -e .
```

2. **Install Node.js dependencies** (for MCP server):
```bash
cd tools/mcp-server
npm install
cd ../..
```

3. **Install Playwright browsers**:
```bash
python -m playwright install chromium
```

4. **Set your OpenAI API key**:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

## Usage

### Web Interface

1. **Start the server**:
```bash
python app.py
```

2. **Open your browser**: Navigate to `http://localhost:5000`

3. **Enter instructions**: Type natural language commands like:
   - "Navigate to google.com and search for 'Playwright MCP'"
   - "Open github.com and find trending repositories"
   - "Go to example.com and tell me the page title"

4. **Choose engine**: Select Auto (recommended), browser-use only, or Playwright MCP only

5. **View results**: See real-time execution steps and results

6. **Export code**: Click "Export Playwright Code" to get reusable scripts

### CLI Automation

#### Basic Automation

```bash
# Simple tasks
python -m src.automation.cli "go to example.com and tell me the page title"

# Web scraping
python -m src.automation.cli "scrape the top 10 Hacker News posts with their titles and URLs"

# Form automation
python -m src.automation.cli "go to example.com/contact and fill out the contact form with name: John Doe, email: john@example.com"

# Multi-step workflows
python -m src.automation.cli "compare prices for iPhone 15 on Amazon and Best Buy"
```

#### Code Generation

```bash
# Generate Python Playwright code
python -m src.automation.cli "login to example.com" --generate-code --output login.py

# Execute generated code (with self-healing)
python -m src.automation.cli --execute-code login.py --verbose
```

## API Endpoints

### Web Application API

- `GET /` - Web interface
- `POST /api/execute` - Execute automation instruction
- `GET /api/engines` - List available automation engines
- `POST /api/reset` - Reset agent conversation state
- `POST /api/export-playwright` - Export execution as Playwright code
- `GET /health` - Health check endpoint

### Example API Call

```bash
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "go to example.com",
    "engine_mode": "auto",
    "headless": true
  }'
```

## How It Works

### Web Application Flow

1. **User Input**: Natural language instruction entered in browser
2. **Engine Selection**: Auto-select or user-specified engine
3. **AI Processing**: OpenAI interprets instruction and plans actions
4. **Execution**: Browser automation performed via selected engine
5. **Fallback** (Auto mode): If browser-use fails, automatically retry with MCP
6. **Results**: Real-time streaming of execution steps and outcomes
7. **Export**: Optional conversion to reusable Playwright code

### Self-Healing Code Generation

1. **Initial Execution**: browser-use performs automation with AI
2. **Code Generation**: Actions converted to Playwright code with robust locators
3. **Self-Healing** (when generated code runs):
   - **Level 1**: If locator fails, AI finds element and updates locator
   - **Level 2**: If healing fails, browser-use AI executes the action
4. **Zero Downtime**: Same browser session, state preserved throughout

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Required: Your OpenAI API key
- `FLASK_SECRET_KEY` - Optional: Flask session secret

### config.ini

```ini
[openai]
model = gpt-4o-mini
temperature = 0.7

[browser]
headless = false
timeout = 30000
```

## Troubleshooting

### Port 5000 already in use
Edit `app.py` and change the port:
```python
app.run(host='0.0.0.0', port=8000)
```

### OpenAI API Key not set
Verify it's set: `echo $OPENAI_API_KEY`

### Playwright browsers not installed
```bash
python -m playwright install chromium
```

### Module import errors
Make sure you're in the project root and dependencies are installed:
```bash
pip install -e .
```

## Cost Considerations

- OpenAI API charges based on token usage
- Each automation typically uses 2-5 API calls
- Monitor usage at: https://platform.openai.com/usage
- Consider using caching and code generation to reduce repeated API calls

## Production Deployment

### For web application:

1. **Use a production WSGI server**:
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

2. **Set environment variables** securely
3. **Add security headers** and configure CORS
4. **Use HTTPS** in production

### Replit Deployment

The project is pre-configured for Replit deployment. Simply click "Deploy" in the Replit interface.

## Technology Stack

- **Flask 3.1+** - Web framework
- **OpenAI GPT-4o-mini** - Natural language understanding
- **browser-use** - AI browser automation
- **Playwright** - Browser automation backend  
- **Playwright MCP** - Model Context Protocol integration
- **Python 3.11+** - Modern Python features
- **Node.js 18+** - MCP server runtime

## License

MIT License - See LICENSE file for details

## Support

If you encounter issues:
1. Check console output for error messages
2. Verify all prerequisites are installed
3. Ensure OpenAI API key is valid and has credits
4. Check that required ports are not blocked

---

**Built with AI-powered automation using OpenAI, browser-use, and Playwright** 🤖
