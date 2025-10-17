# 🚀 Local Setup Guide

Complete guide to set up and run the Browser Automation Framework on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.11 or higher**
   - Download from: https://www.python.org/downloads/
   - Verify: `python --version` or `python3 --version`

2. **Node.js 18 or higher** (required for Playwright MCP)
   - Download from: https://nodejs.org/
   - Verify: `node --version`

3. **uv (Python package installer)** - Recommended
   - Install: `pip install uv`
   - Or use pip/pip3 instead

4. **Git** (to clone the repository)
   - Download from: https://git-scm.com/

## Installation Steps

### 1. Clone or Download the Project

```bash
# If using git
git clone <your-repository-url>
cd <project-directory>

# Or download and extract the ZIP file
```

### 2. Install Python Dependencies

**Option A: Using uv (Recommended - Faster)**
```bash
# Install uv if you haven't
pip install uv

# Install Python dependencies
uv pip install -r requirements.txt
```

**Option B: Using pip**
```bash
# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install manually:
```bash
pip install mcp>=1.18.0 openai>=2.4.0 playwright>=1.55.0 pydantic>=2.12.2 python-dotenv>=1.1.1 rich>=14.2.0 tenacity>=9.1.2
```

### 3. Install Node.js Dependencies (for MCP)

```bash
npm install
```

This installs the Playwright MCP package (`@playwright/mcp`).

### 4. Install Playwright Browsers

```bash
# Install Chromium browser
python -m playwright install chromium

# Or install all browsers (chromium, firefox, webkit)
python -m playwright install

# Install system dependencies (may require sudo on Linux)
# On Ubuntu/Debian:
sudo python -m playwright install-deps

# On macOS (using Homebrew):
# Dependencies usually install automatically
```

### 5. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file
touch .env
```

Add your OpenAI API key to `.env`:

```bash
# OpenAI API Configuration (REQUIRED)
OPENAI_API_KEY=your-actual-api-key-here

# Browser Configuration (Optional)
BROWSER_TYPE=chromium
HEADLESS=true
TIMEOUT=30000
MAX_RETRIES=3

# Logging Configuration (Optional)
LOG_LEVEL=INFO
```

**Get your OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy it to the `.env` file

### 6. Create Required Directories

```bash
# Create directories for screenshots and sessions
mkdir -p screenshots sessions cookies
```

## Running the Project

### 🌟 Enhanced MCP-Powered Automation (Recommended)

The most powerful way - uses Playwright MCP with AI:

```bash
# Using uv
uv run python nl_automation_mcp.py

# Using python directly
python nl_automation_mcp.py
```

**What you'll see:**
1. Prompt to enable vision mode (recommended: `y`)
2. Interactive console to type natural language commands
3. AI automatically selects tools and executes

**Example commands:**
- "Go to google.com and search for Python tutorials"
- "Navigate to news.ycombinator.com and extract top 5 story titles"
- "Fill the contact form with name John and email john@example.com"

### 🎯 Enhanced Natural Language Automation

Alternative automation with vision capabilities:

```bash
python nl_automation.py
```

### 🎮 Interactive Demo Menu

Traditional demo with various automation examples:

```bash
python main.py
```

Choose from:
1. Web Automation Demo
2. Form Automation Demo
3. Data Extraction Demo
4. AI Code Generation

### 📚 Run Individual Examples

```bash
# Web scraping
python examples/web_scraping_example.py

# Form filling
python examples/form_filling_example.py

# AI code generation
python examples/ai_code_generation_example.py

# Advanced automation
python examples/advanced_automation_example.py
```

## Troubleshooting

### Issue: Playwright browsers not installed
```bash
# Error: "Executable doesn't exist at..."
# Solution:
python -m playwright install chromium
```

### Issue: OPENAI_API_KEY not found
```bash
# Error: "OPENAI_API_KEY environment variable not set"
# Solution:
# 1. Verify .env file exists
# 2. Check API key is set correctly
# 3. Try exporting directly:
export OPENAI_API_KEY='your-key-here'  # macOS/Linux
set OPENAI_API_KEY=your-key-here       # Windows CMD
$env:OPENAI_API_KEY='your-key-here'    # Windows PowerShell
```

### Issue: Module not found errors
```bash
# Error: "ModuleNotFoundError: No module named 'mcp'"
# Solution:
pip install --upgrade pip
pip install -r requirements.txt
# Or install missing module directly:
pip install mcp openai playwright rich
```

### Issue: Permission errors on Linux/Mac
```bash
# Error: Permission denied
# Solution:
sudo python -m playwright install-deps
# Or run Python scripts with appropriate permissions
```

### Issue: Node.js/npm not found
```bash
# Error: "npm: command not found"
# Solution:
# Install Node.js from https://nodejs.org/
# Verify installation:
node --version
npm --version
```

### Issue: Browser won't start in headless mode
```bash
# Solution: Try headed mode
# Edit .env file:
HEADLESS=false
# Or modify code to set headless=False
```

## Project Structure

```
.
├── src/automation/              # Core automation framework
│   ├── mcp_client.py           # Playwright MCP client
│   ├── browser_engine.py       # Browser automation engine
│   ├── enhanced_nl_executor.py # Enhanced NL automation
│   ├── vision_analyzer.py      # GPT-4 Vision analysis
│   ├── session_memory.py       # Learning system
│   ├── selectors.py            # Smart selector system
│   ├── task_executor.py        # Task execution
│   └── ...
├── examples/                    # Example scripts
├── nl_automation_mcp.py        # MCP automation (PRIMARY)
├── nl_automation.py            # Enhanced NL automation
├── main.py                     # Interactive demo
├── .env                        # Environment variables (create this)
├── pyproject.toml              # Python dependencies
├── package.json                # Node.js dependencies
└── README.md                   # Documentation
```

## Verification Checklist

Before running, verify:

- [ ] Python 3.11+ installed: `python --version`
- [ ] Node.js 18+ installed: `node --version`
- [ ] Python packages installed: `pip list | grep playwright`
- [ ] Node packages installed: `npm list`
- [ ] Playwright browsers installed: `python -m playwright install chromium`
- [ ] `.env` file created with `OPENAI_API_KEY`
- [ ] Required directories exist: `screenshots/`, `sessions/`

## Quick Start Command Sequence

Copy-paste these commands for a fresh setup:

```bash
# 1. Install Python dependencies
pip install uv
uv pip install mcp openai playwright pydantic python-dotenv rich tenacity

# 2. Install Node.js dependencies
npm install

# 3. Install Playwright browsers
python -m playwright install chromium

# 4. Create .env file
echo "OPENAI_API_KEY=your-key-here" > .env

# 5. Create required directories
mkdir -p screenshots sessions cookies

# 6. Run the MCP automation
python nl_automation_mcp.py
```

## Getting Your OpenAI API Key

1. Visit https://platform.openai.com/
2. Sign up or log in
3. Go to API Keys section: https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (you won't see it again!)
6. Add to `.env` file

## System Requirements

- **OS:** Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** ~500MB for browsers and dependencies
- **Internet:** Required for AI features and web automation

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the main README.md
3. Check Playwright docs: https://playwright.dev/
4. Check OpenAI docs: https://platform.openai.com/docs

---

**Happy Automating! 🎭✨**
