# Browser Automation with Natural Language

This Python automation system allows you to control browser automation using natural language commands. It combines:
- **Playwright MCP Server** - Browser automation backend
- **OpenAI GPT-5** - Natural language understanding
- **Python Orchestration** - Execution engine

## 🚀 Features

- **Natural Language Input**: Describe what you want to automate in plain English
- **Automatic Execution**: System translates to browser actions and executes them
- **Code Generation**: Generates reusable Python code for your automation
- **Result Tracking**: Saves execution results and generated code

## 📋 Prerequisites

1. **Playwright MCP Server** (already running on port 3000)
2. **OpenAI API Key** - Required for natural language processing
3. **Python 3.11+** (already installed)

## 🔧 Setup

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. The system is ready to use!

## 💡 Usage

### Command Line Mode
```bash
python main.py "navigate to google.com and search for Playwright"
```

### Interactive Mode
```bash
python main.py
```

Then enter commands interactively:
```
➜ go to github.com and click the sign in button
➜ navigate to example.com and take a snapshot
➜ open reddit.com and search for python
```

## 📝 Example Commands

```bash
# Navigation
python main.py "open https://www.example.com"

# Search
python main.py "go to google.com and search for 'Playwright automation'"

# Interaction
python main.py "navigate to github.com, click sign in, and take a screenshot"

# Data extraction
python main.py "go to hacker news and get the top stories"
```

## 📂 Output

The system generates two types of output:

### 1. Execution Results (`output/`)
- JSON files with complete execution details
- Includes plan, results, and timestamp
- Example: `results_20241016_123456.json`

### 2. Reusable Code (`generated_code/`)
- Python scripts for each automation
- Ready to run and modify
- Example: `automation_20241016_123456.py`

## 🏗️ Architecture

```
┌─────────────────┐
│  Natural        │
│  Language Input │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM            │
│  Orchestrator   │  ← Converts to automation plan
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MCP Client     │  ← Sends commands to Playwright
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Playwright     │
│  MCP Server     │  ← Executes browser automation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Results +      │
│  Generated Code │
└─────────────────┘
```

## 🔍 How It Works

1. **Input**: You provide a natural language command
2. **Planning**: LLM analyzes the command and creates a step-by-step plan
3. **Execution**: MCP client sends commands to Playwright server
4. **Code Generation**: LLM creates reusable Python code
5. **Output**: Results and code are saved to disk

## 📚 Components

- `automation/mcp_client.py` - Communicates with Playwright MCP server
- `automation/llm_orchestrator.py` - LLM-powered planning and code generation
- `automation/automation_engine.py` - Main orchestration engine
- `main.py` - Entry point and CLI interface

## 🛠️ Advanced Usage

### Using Generated Code

The generated code in `generated_code/` can be:
- Run directly: `python generated_code/automation_*.py`
- Modified for your needs
- Integrated into larger projects
- Scheduled with cron/task scheduler

### Custom MCP Server URL

```python
from automation import AutomationEngine

engine = AutomationEngine(mcp_url="http://your-server:3000/mcp")
await engine.initialize()
await engine.execute_automation("your command")
```

## 🐛 Troubleshooting

**Error: OPENAI_API_KEY not set**
- Make sure to export your OpenAI API key before running

**Error: Cannot connect to MCP server**
- Ensure Playwright MCP server is running on port 3000
- Check with: `curl http://localhost:3000/`

**Error: Empty response from LLM**
- Check your OpenAI API key is valid
- Ensure you have API credits available

## 📄 License

Uses Playwright MCP (Apache 2.0) and requires OpenAI API access.
