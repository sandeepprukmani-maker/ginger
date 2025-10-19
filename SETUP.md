# VisionVault - Local Setup Guide

Complete guide to set up and run VisionVault browser automation platform on your local machine.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Optional Setup](#optional-setup)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

1. **Python 3.11+**
   ```bash
   # Check your Python version
   python --version
   # or
   python3 --version
   ```
   Download from: https://www.python.org/downloads/

2. **Node.js 18+ and npm**
   ```bash
   # Check versions
   node --version
   npm --version
   ```
   Download from: https://nodejs.org/

3. **Git** (to clone the repository)
   ```bash
   git --version
   ```

### System Requirements
- **Operating System**: Linux, macOS, or Windows (WSL recommended for Windows)
- **RAM**: Minimum 4GB, recommended 8GB+
- **Disk Space**: At least 2GB free space

---

## Installation

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-name>
```

### Step 2: Set Up Python Environment

#### Option A: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### Option B: Using Conda

```bash
conda create -n visionvault python=3.11
conda activate visionvault
```

### Step 3: Install Python Dependencies

```bash
# Install all required Python packages
pip install -r requirements.txt
```

### Step 4: Install Playwright Browsers

```bash
# Install Playwright browser binaries
playwright install chromium

# Optional: Install other browsers
playwright install firefox
playwright install webkit

# Install system dependencies (Linux only)
# On Ubuntu/Debian:
sudo playwright install-deps
```

### Step 5: Install Node.js Dependencies

```bash
# Navigate to MCP directory and install dependencies
cd mcp
npm install
cd ..
```

The MCP server (`@playwright/mcp`) will be installed automatically via npx when needed.

---

## Configuration

### Step 1: Create Environment Variables File

Create a `.env` file in the root directory:

```bash
touch .env
```

### Step 2: Add Required Environment Variables

Edit `.env` and add the following:

```bash
# Required for AI-powered features
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here

# Server Configuration
PORT=5000
HOST=0.0.0.0
FLASK_ENV=development

# Database Configuration (Optional - SQLite is used by default)
# DATABASE_URL=postgresql://user:password@localhost:5432/visionvault

# Optional: Enable debug mode
DEBUG=false
```

### Step 3: Get API Keys

#### OpenAI API Key (Required for AI features)
1. Go to https://platform.openai.com/api-keys
2. Create an account or sign in
3. Click "Create new secret key"
4. Copy the key and paste it in `.env`

#### Google Gemini API Key (Optional - for semantic search)
1. Go to https://ai.google.dev/
2. Click "Get API key"
3. Follow the setup instructions
4. Copy the key and paste it in `.env`

---

## Running the Application

### Method 1: Development Server (Recommended for Local Testing)

```bash
# Make sure you're in the project root directory
# and your virtual environment is activated

python run_server.py
```

The server will start on `http://0.0.0.0:5000`

### Method 2: Using Gunicorn (Production-like)

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --reuse-port visionvault.web.app:app
```

### Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

---

## Understanding the Application

### What Works by Default

When you first run the application, the following components are active:

✅ **Working (No API Keys Required)**:
- Database (SQLite with persistent learning)
- Self-Learning Engine
- MCP Automation Manager
- Unified Automation Engine (basic mode)
- Web Interface

❌ **Disabled (Requires API Keys)**:
- MCP Direct Automation (needs `OPENAI_API_KEY`)
- Code Generation (needs `OPENAI_API_KEY`)
- HYBRID Mode (needs `OPENAI_API_KEY`)
- Intelligent Planner (needs `OPENAI_API_KEY`)
- Semantic Search (needs `GEMINI_API_KEY`)

### Execution Modes

The application supports three automation strategies:

1. **MCP Direct** - Fast, intelligent browser control via MCP server
   - Requires: `OPENAI_API_KEY`
   
2. **Code Generation** - AI-generated Playwright code with healing
   - Requires: `OPENAI_API_KEY`
   
3. **HYBRID** - Best of both worlds (MCP execution + code generation)
   - Requires: `OPENAI_API_KEY`
   - Executes with MCP intelligence
   - Generates reusable Playwright code from working traces

---

## Optional Setup

### PostgreSQL Database (Optional)

By default, the app uses SQLite. To use PostgreSQL:

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   ```

2. **Create Database**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE visionvault;
   CREATE USER visionvault_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE visionvault TO visionvault_user;
   \q
   ```

3. **Update .env**
   ```bash
   DATABASE_URL=postgresql://visionvault_user:your_password@localhost:5432/visionvault
   ```

### Running in Headful Mode (See Browser)

By default, browsers run in headless mode. To see the browser:

1. Open `visionvault/web/app.py`
2. Find the automation execution calls
3. Change `headless=True` to `headless=False`

Or modify the execution request from the web interface.

---

## Project Structure

```
.
├── visionvault/           # Main application package
│   ├── web/              # Flask web application
│   │   ├── app.py        # Main Flask app
│   │   └── templates/    # HTML templates
│   ├── services/         # Core services
│   │   ├── unified_engine.py      # Strategy orchestration
│   │   ├── mcp_manager.py         # MCP automation manager
│   │   ├── hybrid_codegen.py      # Code generation from traces
│   │   ├── healing_executor.py    # Self-healing execution
│   │   └── ...
│   ├── agents/           # Browser automation agents
│   └── core/             # Core models
├── mcp/                  # MCP integration
│   ├── src/
│   │   └── automation/   # MCP client and tools
│   └── package.json
├── data/                 # Data storage (auto-created)
│   ├── database/         # SQLite database
│   └── uploads/          # Screenshots and recordings
├── requirements.txt      # Python dependencies
├── run_server.py         # Server entry point
└── SETUP.md             # This file
```

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'flask'

**Solution**: Make sure you've activated your virtual environment and installed dependencies:
```bash
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

#### 2. Playwright browsers not installed

**Error**: `Executable doesn't exist at ...`

**Solution**:
```bash
playwright install chromium
# Linux users also need:
sudo playwright install-deps
```

#### 3. OpenAI API Error

**Error**: `OPENAI_API_KEY is required for MCP automation`

**Solution**: 
- Add your OpenAI API key to `.env` file
- Make sure the key is valid
- Restart the server after adding the key

#### 4. Port 5000 already in use

**Solution**: Either stop the process using port 5000 or change the port:
```bash
# Change port in .env
PORT=8080
```

#### 5. npx command not found

**Solution**: Install Node.js and npm:
```bash
# Verify installation
node --version
npm --version
```

#### 6. Browser automation not working on Linux

**Solution**: Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y \
    libgbm1 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2
```

### Getting Help

If you encounter issues not covered here:

1. Check the server logs for error messages
2. Ensure all prerequisites are installed correctly
3. Verify your API keys are valid
4. Make sure all dependencies are up to date

---

## Development Tips

### Running in Debug Mode

Enable Flask debug mode for development:

```bash
# In .env file
FLASK_ENV=development
DEBUG=true
```

### Viewing Logs

Server logs are printed to the console. For detailed MCP logs, check:
```
data/logs/  # (auto-created during execution)
```

### Testing Different Browsers

Change the browser in automation requests:
- `chromium` (default, fastest)
- `firefox`
- `webkit` (Safari engine)

### Code Formatting

The project uses standard Python formatting:
```bash
# Install formatters (optional)
pip install black flake8

# Format code
black .

# Check code quality
flake8 .
```

---

## Quick Start Summary

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd <repo-name>

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 4. Set up environment
echo "OPENAI_API_KEY=your_key_here" > .env

# 5. Run the server
python run_server.py

# 6. Open browser
# Navigate to http://localhost:5000
```

---

## Features Overview

- **Intelligent Browser Automation**: Natural language commands to browser actions
- **Three Execution Strategies**: MCP Direct, Code Generation, and HYBRID
- **Self-Learning Engine**: Learns from past executions to improve
- **Auto-Healing**: Automatically fixes failing automation scripts
- **Code Generation**: Generates reusable Playwright code
- **Real-time Updates**: WebSocket-based progress streaming
- **Screenshot Capture**: Visual verification of automation results

---

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

---

**Happy Automating! 🚀**
