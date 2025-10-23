# AI Browser Automation

A professional hybrid-engine browser automation system powered by AI, offering intelligent automation with automatic fallback for maximum reliability through a modern Flask web interface.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Automation Engines](#automation-engines)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [Windows](#windows-setup)
  - [Linux](#linux-setup)
  - [macOS](#macos-setup)
  - [Replit](#replit-setup)
- [Running the Application](#running-the-application)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Security](#security)
- [Testing](#testing)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project provides intelligent browser automation using natural language instructions. Users can choose between three powerful automation engines through an intuitive web interface, with the Hybrid engine providing the best of both worlds through automatic fallback mechanisms.

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

---

## Features

- **Hybrid Intelligence**: Smart automation with automatic fallback for reliability
- **Triple Engine System**: Choose between hybrid, AI-powered, or tool-based automation
- **Headless/Headful Modes**: Run browser invisibly for speed or visibly for debugging
- **Natural Language Instructions**: Describe tasks in plain English
- **Real-time Feedback**: See step-by-step execution progress with engine metadata
- **Modern Web Interface**: Clean two-column layout with configuration panel
- **Quick Examples**: Pre-loaded examples for common automation tasks
- **RESTful API**: Programmatic access to automation capabilities
- **Security Features**: API authentication, rate limiting, input validation, CORS support
- **Cross-Platform**: Works on Windows, Linux, macOS, and Replit

---

## Architecture

### Directory Structure

```
.
├── app/                           # Flask web application
│   ├── __init__.py               # Application factory
│   ├── middleware/               # Security & validation
│   │   └── security.py           # Auth, rate limiting, validation
│   ├── services/                 # Business logic layer
│   │   └── engine_orchestrator.py  # Engine coordination
│   ├── routes/                   # API endpoints
│   │   └── api.py                # REST routes
│   ├── templates/                # HTML templates
│   │   └── index.html
│   ├── static/                   # Static assets
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── utils/                    # Utilities
│       └── timeout.py            # Timeout handling
├── browser_use_codebase/         # Browser-Use engine
│   ├── engine.py                 # Browser-Use implementation
│   └── config/                   # Configuration helpers
├── hybrid_engine/                # Hybrid engine (recommended)
│   ├── __init__.py              # Package initialization
│   └── engine.py                # Intelligent fallback logic
├── playwright_mcp_codebase/      # Playwright MCP engine
│   ├── agent/                    # Conversation agent
│   │   └── conversation_agent.py
│   ├── client/                   # MCP STDIO client
│   │   └── stdio_client.py
│   └── config/                   # Configuration helpers
├── tests/                        # Unit tests
│   ├── test_api_routes.py
│   └── test_engine_orchestrator.py
├── config/                       # Configuration files
│   └── config.ini                # Application configuration
├── node/                         # Node.js dependencies
│   ├── cli.js                    # Playwright MCP server entry point
│   ├── index.js                  # Package main entry
│   ├── index.d.ts                # TypeScript definitions
│   ├── package.json              # Node.js dependencies
│   └── package-lock.json         # Dependency lock file
├── main.py                       # Application entry point
├── pyproject.toml                # Python dependencies (uv)
├── requirements.txt              # Python dependencies (pip)
├── uv.lock                       # Python dependency lock file
├── LICENSE                       # License file
└── README.md                     # This file
```

### Design Patterns

**Frontend Architecture:**
- Vanilla JavaScript with server-side Jinja2 templates
- Two-column responsive layout
- RESTful API communication using fetch API

**Backend Architecture:**
- Application Factory Pattern for Flask initialization
- Service-oriented architecture with clear separation of concerns
- Blueprint pattern for modular route organization
- Engine orchestration for managing multiple automation engines

### Thread Safety

**Browser-Use Engine:**
- Creates fresh browser instances per request
- Uses new event loop for each execution
- No instance caching to prevent loop affinity issues
- Automatic cleanup in finally blocks

**Playwright MCP Engine:**
- Subprocess-based communication is thread-safe
- Instances cached by headless mode setting
- Shared across requests for efficiency

---

## Technology Stack

### Backend
- **Python 3.11+** with Flask web framework
- **OpenAI GPT-4o-mini** for AI reasoning
- **Playwright** (via browser-use and MCP)
- **browser-use** library for autonomous automation
- **langchain-openai** for LLM integration
- **gunicorn** for production WSGI server

### Frontend
- Modern HTML5/CSS3/JavaScript
- RESTful API communication
- Real-time status updates

### Infrastructure
- Subprocess-based MCP communication (Playwright)
- Async execution with thread-safe event loops (Browser-Use)
- Environment-based secret management

---

## Prerequisites

- **Python 3.11+**: Required for async features
- **Node.js 18+**: Required for Playwright MCP server
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys

---

## Installation & Setup

### Windows Setup

#### 1. Install Prerequisites

**Python 3.11+:**
Download from https://www.python.org/downloads/

**Node.js 18+:**
Download from https://nodejs.org/

#### 2. Clone Repository

```bash
git clone <repository-url>
cd ai-browser-automation
```

#### 3. Install Python Dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using uv (faster):
```bash
pip install uv
uv sync
```

#### 4. Install Node.js Dependencies

```bash
npm install
```

#### 5. Install Playwright Browsers

```bash
npx playwright install chromium
```

#### 6. Configure OpenAI API Key

Set as environment variable (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"
```

Or set as environment variable (Command Prompt):
```cmd
set OPENAI_API_KEY=sk-your-actual-api-key-here
```

For persistent configuration, add to System Environment Variables:
1. Search "Environment Variables" in Windows
2. Click "Environment Variables" button
3. Add new User or System variable: `OPENAI_API_KEY`

#### 7. Run the Application

```bash
python main.py
```

Access at: `http://localhost:5000`

---

### Linux Setup

#### 1. Install Prerequisites

**Python 3.11+:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Node.js 18+:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 2. Clone Repository

```bash
git clone <repository-url>
cd ai-browser-automation
```

#### 3. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

Or using uv:
```bash
pip3 install uv
uv sync
```

#### 4. Install Node.js Dependencies

```bash
npm install
```

#### 5. Install Playwright Browsers

```bash
npx playwright install chromium
npx playwright install-deps chromium
```

#### 6. Configure OpenAI API Key

```bash
export OPENAI_API_KEY=sk-your-actual-api-key-here
```

For persistent configuration, add to `~/.bashrc` or `~/.profile`:
```bash
echo 'export OPENAI_API_KEY=sk-your-actual-api-key-here' >> ~/.bashrc
source ~/.bashrc
```

#### 7. Run the Application

```bash
python3 main.py
```

Access at: `http://localhost:5000`

---

### macOS Setup

#### 1. Install Prerequisites

**Python 3.11+:**
```bash
brew install python@3.11
```

**Node.js 18+:**
```bash
brew install node@18
```

#### 2. Clone Repository

```bash
git clone <repository-url>
cd ai-browser-automation
```

#### 3. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

Or using uv:
```bash
pip3 install uv
uv sync
```

#### 4. Install Node.js Dependencies

```bash
npm install
```

#### 5. Install Playwright Browsers

```bash
npx playwright install chromium
```

#### 6. Configure OpenAI API Key

```bash
export OPENAI_API_KEY=sk-your-actual-api-key-here
```

For persistent configuration, add to `~/.zshrc` or `~/.bash_profile`:
```bash
echo 'export OPENAI_API_KEY=sk-your-actual-api-key-here' >> ~/.zshrc
source ~/.zshrc
```

#### 7. Run the Application

```bash
python3 main.py
```

Access at: `http://localhost:5000`

---

### Replit Setup

This application is pre-configured for Replit with optimized deployment settings.

#### 1. Environment Variables

Set in Replit Secrets (click the lock icon 🔒):

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key

**Automatically Provided:**
- `SESSION_SECRET`: Flask session secret (auto-generated by Replit)

**Optional (for production):**
- `API_KEY`: Enable API authentication
- `CORS_ALLOWED_ORIGINS`: Comma-separated allowed origins (default: `*`)

#### 2. Workflow Configuration

The workflow is pre-configured to run:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

Port 5000 is used as it's the only non-firewalled port in Replit.

#### 3. Deployment Configuration

- **Target**: VM (always-running, stateful)
- **Required for**: Browser automation state persistence
- **Benefits**: MCP subprocess persistence, no browser recreation overhead

#### 4. Browser Installation

Playwright browsers are pre-installed. If needed:
```bash
npx playwright install chromium
```

#### 5. Running on Replit

Click the **Run** button or restart the workflow. The application will:
- Start on port 5000
- Disable cache for proper hot-reload
- Show webview preview automatically

Access via the Replit webview or your Replit domain.

---

## Running the Application

### Development Mode

**All Platforms:**
```bash
python main.py
```

The server starts on `http://0.0.0.0:5000`

Access the web interface:
```
http://localhost:5000
```

### Production Mode

Use a production WSGI server like gunicorn:

```bash
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 main:app
```

For Replit (pre-configured):
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

---

## Usage

### Web Interface

1. **Select Engine**: Choose between Hybrid (Recommended), Browser-Use, or Playwright MCP
2. **Configure Mode**: Toggle headless mode on/off
3. **Enter Instruction**: Describe your automation task in natural language
4. **Execute**: Click the Execute button
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

---

## API Documentation

### Base URL
```
http://localhost:5000
```

### Authentication

If `API_KEY` environment variable is set, include in requests:

**Header (Recommended):**
```http
X-API-Key: your-api-key-here
```

**Query Parameter:**
```
?api_key=your-api-key-here
```

### Endpoints

#### Execute Instruction

```http
POST /api/execute
Content-Type: application/json
X-API-Key: your-api-key-here

{
  "instruction": "Go to example.com",
  "engine": "hybrid",
  "headless": false
}
```

**Parameters:**
- `instruction` (string, required): Natural language instruction
- `engine` (string, optional): `hybrid`, `browser_use`, or `playwright_mcp` (default: `hybrid`)
- `headless` (boolean, optional): Run headless browser (default: `false`)

**Response:**
```json
{
  "success": true,
  "message": "Task completed successfully",
  "steps": [...],
  "iterations": 3,
  "engine": "hybrid",
  "engine_metadata": {
    "primary_engine": "browser_use",
    "fallback_used": false
  }
}
```

#### List Available Tools

```http
GET /api/tools?engine=playwright_mcp
X-API-Key: your-api-key-here
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
X-API-Key: your-api-key-here

{
  "engine": "hybrid"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Agent reset successfully",
  "engine": "hybrid"
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
    "hybrid": "available",
    "browser_use": "available",
    "playwright_mcp": "available"
  },
  "message": "Hybrid-engine browser automation ready",
  "security": {
    "authentication": "enabled",
    "rate_limiting": "enabled"
  }
}
```

### Rate Limiting

- **Default**: 10 requests per minute per IP
- **Response on limit**:
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again in 45 seconds.",
  "retry_after": 45
}
```

---

## Security

### Environment Variables

**Never commit secrets to version control**. Always use environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for AI automation |
| `API_KEY` | No | - | API key for endpoint authentication |
| `CORS_ALLOWED_ORIGINS` | No | `*` | Comma-separated allowed origins |
| `SESSION_SECRET` | Recommended | - | Flask session secret key |

### Security Features

1. **API Authentication**
   - Optional API key protection for all automation endpoints
   - Header or query parameter authentication
   - Disabled by default (development mode)

2. **Rate Limiting**
   - 10 requests/minute per IP by default
   - Prevents abuse and cost exhaustion
   - Automatic cleanup of old request records

3. **Input Validation**
   - All inputs validated before processing
   - Instruction: max 5000 characters
   - Engine type: must be valid option
   - Headless: must be boolean

4. **CORS Configuration**
   - Control which domains can access the API
   - Configure via `CORS_ALLOWED_ORIGINS`
   - Default: `*` (all origins - development)

5. **Error Sanitization**
   - Internal error details hidden from users
   - Prevents information leakage
   - Generic user-facing messages

6. **Timeout Protection**
   - 5-minute timeout on all requests
   - Cross-platform implementation
   - Automatic resource cleanup

7. **Process Monitoring**
   - Automatic subprocess recovery
   - Detects and handles crashed processes
   - Zombie process cleanup

### Best Practices

1. **Use HTTPS in production**
   - Configure with reverse proxy (nginx/Apache)
   - API keys transmitted over HTTP can be intercepted

2. **Rotate credentials regularly**
   - Change `API_KEY` periodically
   - Update `OPENAI_API_KEY` if compromised

3. **Monitor API usage**
   - Track OpenAI API costs: https://platform.openai.com/usage
   - Monitor authentication failures
   - Alert on unusual traffic patterns

4. **Production Deployment Checklist**
   - [ ] Set `API_KEY` to strong random value
   - [ ] Set `CORS_ALLOWED_ORIGINS` to specific domains
   - [ ] Set `SESSION_SECRET` to secure random value
   - [ ] Enable HTTPS with reverse proxy
   - [ ] Monitor logs for authentication failures
   - [ ] Set up alerting for rate limit violations

### Reporting Security Issues

If you discover a security vulnerability:
1. **Do NOT** open a public issue
2. Contact the maintainer privately
3. Include description, reproduction steps, and potential impact

---

## Testing

### Running Tests

Run all tests:
```bash
python -m pytest tests/
```

Run specific test file:
```bash
python -m pytest tests/test_engine_orchestrator.py
python -m pytest tests/test_api_routes.py
```

Run with coverage:
```bash
python -m pytest --cov=app tests/
```

### Test Structure

- `test_engine_orchestrator.py` - Engine coordination and caching tests
- `test_api_routes.py` - Flask API endpoint tests

### Writing New Tests

1. Create file starting with `test_`
2. Import `unittest` or use `pytest`
3. Add test methods starting with `test_`
4. Use mocks for external dependencies (browsers, OpenAI API)

---

## Deployment

### Development

The application runs on Flask's development server, suitable for testing and local development.

### Production

#### Using Gunicorn (Recommended)

```bash
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 main:app
```

#### Using Reverse Proxy

**Nginx Configuration Example:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt
RUN npm install
RUN npx playwright install chromium --with-deps

EXPOSE 5000

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "main:app"]
```

Build and run:
```bash
docker build -t ai-browser-automation .
docker run -p 5000:5000 -e OPENAI_API_KEY=sk-your-key ai-browser-automation
```

#### Replit Deployment

Pre-configured for Replit VM deployment:
- Always-running, stateful instance
- MCP subprocess persistence
- Port 5000 (non-firewalled)
- Click "Deploy" in Replit UI to publish

---

## Configuration

### config/config.ini

Application-level configuration file (non-sensitive settings):

```ini
[server]
host = 0.0.0.0
port = 5000

[browser]
headless = true
browser = chromium

[openai]
model = gpt-4o-mini

[agent]
max_steps = 100
```

**Note**: Never store API keys in config.ini. Use environment variables.

### Customizing Rate Limits

Edit `app/middleware/security.py`:

```python
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
```

---

## Troubleshooting

### Port Already in Use

**Linux/macOS:**
```bash
lsof -ti:5000 | xargs kill -9
```

**Windows:**
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Missing OpenAI API Key

Ensure environment variable is set:

**Check (Linux/macOS):**
```bash
echo $OPENAI_API_KEY
```

**Check (Windows PowerShell):**
```powershell
$env:OPENAI_API_KEY
```

### Playwright Installation Issues

**Linux:**
```bash
npx playwright install-deps chromium
npx playwright install chromium
```

**All platforms:**
```bash
npx playwright install chromium
```

### Browser Crashes

- Ensure sufficient memory (2GB+ recommended)
- Try headless mode for lower resource usage
- Check Playwright logs for specific errors

### Cached CSS Not Loading (Windows)

Clear browser cache with hard refresh:
- Chrome/Edge: `Ctrl + Shift + R` or `Ctrl + F5`
- Firefox: `Ctrl + Shift + R` or `Ctrl + F5`
- Alternative: Open DevTools (F12) → Right-click refresh → "Empty Cache and Hard Reload"

### Permission Denied Errors (Linux/macOS)

```bash
chmod +x cli.js
```

---

## Performance Considerations

### OpenAI API Costs

- Each instruction execution calls OpenAI API multiple times
- Browser-Use: 1-5 calls per instruction (autonomous)
- Playwright MCP: 2-10+ calls per instruction (iterative)
- Hybrid: Uses Browser-Use first, falls back to MCP if needed
- Monitor usage at: https://platform.openai.com/usage

### Resource Usage

- **Headless mode**: ~200-500MB RAM per browser instance
- **Headful mode**: ~500MB-1GB RAM per browser instance
- **Recommended**: 4GB+ total system RAM for optimal performance

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Submit a pull request

---

## License

See LICENSE file for details.

---

## Support

For issues and questions:
- Check the Troubleshooting section above
- Review console output for error messages
- Verify OpenAI API key is valid and has credits
- Ensure all dependencies are installed correctly
- Check the health endpoint: `http://localhost:5000/health`

---

**Built with ❤️ using Playwright, browser-use, OpenAI GPT-4o-mini, and Flask**
