# AI Browser Automation Agent

A powerful web application that enables AI-powered browser automation using natural language instructions. The application supports multiple automation engines and provides an intuitive web interface for executing browser tasks.

## 🚀 Features

- **Natural Language Control**: Tell the AI what you want to do on the web in plain English
- **Multiple Automation Engines**:
  - **Browser-use**: Powered by the browser-use library with OpenAI
  - **Playwright MCP**: Microsoft's Playwright Model Context Protocol server
  - **Auto Mode**: Intelligent fallback between engines
- **Real-time Execution**: See step-by-step execution of your automation tasks
- **Beautiful UI**: Clean, modern interface with execution results display
- **Flexible Configuration**: Customize browser settings and capabilities

## 📋 Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm 10 or higher
- OpenAI API key

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-name>
```

### 2. Install Python Dependencies

The project uses `uv` for Python package management. All dependencies are defined in `pyproject.toml`:

```bash
# Dependencies will be installed automatically on Replit
# Or manually install with:
pip install -e .
```

**Key Python Dependencies:**
- Flask 3.1.2+ (Web framework)
- browser-use 0.8.1+ (Browser automation)
- playwright 1.55.0+ (Browser control)
- langchain-openai 1.0.1+ (LLM integration)
- openai 1.109.1+ (OpenAI API)
- gunicorn 23.0.0+ (WSGI server)
- flask-sqlalchemy 3.1.1+ (Database ORM)
- psycopg2-binary 2.9.11+ (PostgreSQL adapter)

### 3. Install Node.js Dependencies

The Playwright MCP server requires Node.js dependencies:

```bash
cd tools/mcp-server
npm install
```

### 4. Install Playwright Browsers

Install the Chromium browser for Playwright:

```bash
cd tools/mcp-server
npx playwright install chromium
```

### 5. Configure Environment Variables

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

Or add it to Replit Secrets if running on Replit.

### 6. Create Configuration File

Copy the example configuration and customize as needed:

```bash
cp config.ini.example config.ini
```

Edit `config.ini`:

```ini
[browser]
# Run browser in headless mode (true/false)
headless = true

# Browser to use (chromium, firefox, webkit)
browser = chromium

# Comma-separated capabilities to enable
capabilities = testing
```

## 🎯 Running the Application

### Development Mode

Start the application with auto-reload enabled:

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Production Mode

For production deployment:

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port main:app
```

The application will be available at `http://localhost:5000`

## 📖 Usage

### Web Interface

1. Open your browser and navigate to `http://localhost:5000`
2. Enter your automation instruction in the text area, for example:
   - "Go to google.com and search for 'Playwright MCP'"
   - "Navigate to github.com and find the trending repositories"
   - "Open example.com and click the first button"
3. Select your preferred automation engine:
   - **Auto**: Tries browser-use first, falls back to MCP if needed
   - **Browser-use only**: Uses only the browser-use engine
   - **Playwright MCP only**: Uses only the Playwright MCP engine
4. Click the execute button and watch the AI perform the task
5. View the detailed execution results and steps in the right panel

### Programmatic Usage

#### Using the LLM Client Module

The project provides a centralized LLM client for consistent OpenAI integration:

```python
from llm_client import get_browser_use_client, get_playwright_mcp_client

# Get ChatOpenAI client for browser-use
browser_use_llm = get_browser_use_client()

# Get OpenAI client for Playwright MCP
mcp_client = get_playwright_mcp_client()
mcp_model = get_playwright_mcp_model()
```

#### Using Automation Engines Directly

```python
from src.web.services.browser_use.engine import BrowserUseAutomationEngine
from src.web.services.playwright_mcp.engine import MCPAutomationEngine

# Browser-use engine
browser_engine = BrowserUseAutomationEngine()
result = browser_engine.execute_instruction(
    "Go to example.com",
    headless=True
)

# Playwright MCP engine
mcp_engine = MCPAutomationEngine()
result = mcp_engine.execute_instruction(
    "Navigate to github.com",
    headless=True
)
```

## 🏗️ Project Structure

```
.
├── src/                          # Source code
│   ├── automation/              # Core automation modules
│   │   ├── automation_engine.py # Main automation engine
│   │   ├── playwright_code_generator.py
│   │   ├── self_healing_executor.py
│   │   └── examples/            # Example automations
│   └── web/                     # Web application
│       ├── services/            # Automation services
│       │   ├── browser_use/     # Browser-use engine
│       │   ├── playwright_mcp/  # Playwright MCP engine
│       │   └── engine_manager.py
│       ├── static/              # CSS, JS assets
│       ├── templates/           # HTML templates
│       └── routes.py            # Flask routes
├── tools/                        # Tools and utilities
│   └── mcp-server/              # Playwright MCP server
├── app.py                       # Flask app initialization
├── main.py                      # Application entry point
├── llm_client.py                # Centralized LLM client
├── config.ini                   # Configuration file
├── pyproject.toml               # Python dependencies
└── README.md                    # This file
```

## 🔑 LLM Client Module

The `llm_client.py` module provides centralized OpenAI client management:

### Available Clients

1. **Browser-Use Client** (`get_browser_use_client()`)
   - Default Model: gpt-4o-mini
   - Returns: ChatOpenAI instance
   - Used for: Natural language browser automation

2. **Playwright MCP Client** (`get_playwright_mcp_client()`)
   - Default Model: gpt-4o-mini
   - Returns: OpenAI instance
   - Used for: Playwright MCP browser control

3. **Automation Engine Client** (`get_automation_engine_client()`)
   - Default Model: gpt-4o-mini
   - Returns: ChatOpenAI instance
   - Used for: Core automation engine

4. **Self-Healing Client** (`get_self_healing_client()`)
   - Default Model: gpt-4o-mini
   - Returns: ChatOpenAI instance
   - Used for: AI-powered locator healing

### Configuration

Configure API keys via environment variable:

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"
```

Or use the factory with explicit API key:

```python
from llm_client import LLMClientFactory

factory = LLMClientFactory(api_key="sk-...")
llm = factory.get_browser_use_client(model="gpt-4")
```

### Changing Default Models

Edit the model constants in `llm_client.py`:

```python
class LLMClientFactory:
    BROWSER_USE_MODEL = "gpt-4o-mini"
    PLAYWRIGHT_MCP_MODEL = "gpt-4o-mini"
    AUTOMATION_ENGINE_MODEL = "gpt-4o-mini"
    SELF_HEALING_MODEL = "gpt-4o-mini"
```

## 🔧 Configuration

### Browser Settings

Edit `config.ini` to customize browser behavior:

- **headless**: Run browser in headless mode (true/false)
- **browser**: Browser engine to use (chromium, firefox, webkit)
- **capabilities**: Playwright capabilities (testing, vision, tracing)

### Model Settings

Change AI models in `llm_client.py` for different use cases:
- `gpt-4o-mini`: Fast, cost-effective (default)
- `gpt-4o`: More capable for complex tasks
- `gpt-4-turbo`: Balance of speed and capability

## 🚀 Deployment

The application is configured for deployment on Replit with auto-scaling:

```bash
# Deployment uses this command:
gunicorn --bind 0.0.0.0:5000 main:app
```

The deployment configuration is set to:
- **Target**: autoscale (stateless web application)
- **Port**: 5000
- **Server**: Gunicorn WSGI server

## 🛠️ Troubleshooting

### Common Issues

**1. "MCP server process is not running"**
- Ensure Node.js dependencies are installed: `cd tools/mcp-server && npm install`
- Install Playwright browsers: `npx playwright install chromium`
- Check that `config.ini` exists in the project root

**2. "'ChatOpenAI' object has no attribute 'provider'"**
- Ensure OPENAI_API_KEY environment variable is set
- Verify langchain-openai is properly installed
- Check that the API key is valid

**3. "ModuleNotFoundError: No module named 'flask'"**
- Install Python dependencies: `pip install -e .`
- Or manually: `pip install flask flask-sqlalchemy gunicorn`

**4. Port 5000 already in use**
- Stop other services on port 5000
- Or change the port in the gunicorn command

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Examples

### Example 1: Search Google

```
Instruction: "Go to google.com and search for 'AI automation'"
Engine: Auto
```

### Example 2: Navigate GitHub

```
Instruction: "Navigate to github.com and find the trending Python repositories"
Engine: Playwright MCP only
```

### Example 3: Web Scraping

```
Instruction: "Go to news.ycombinator.com and get the top 3 story titles"
Engine: Browser-use only
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 🙏 Acknowledgments

- **browser-use**: AI-powered browser automation library
- **Playwright**: Microsoft's browser automation framework
- **OpenAI**: GPT models for natural language processing
- **Flask**: Python web framework
- **Langchain**: LLM application framework

## 📞 Support

For issues, questions, or contributions, please open an issue on the repository.

---

**Built with ❤️ using Flask, Playwright, and OpenAI**
