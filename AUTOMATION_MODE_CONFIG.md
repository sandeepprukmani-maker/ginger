# Automation Agent Mode Configuration

## ✅ Configuration Complete

The Playwright MCP engine is now configured to use **Automation Agent Mode** by default.

## What is Automation Agent Mode?

When you give the system a task, Automation Mode will:

1. **Execute the task directly** - Performs the browser automation in real-time
2. **Capture all steps** - Records every action taken during execution
3. **Generate a self-healing script** - Creates **1 standalone Python script** with retry logic and resilience features

### Output: 1 Script Per Task

Each automation task creates:
- ✅ **1 executable Python automation script** (`automation_<task_name>.py`)
- ✅ Self-healing capabilities (automatic retry on failures)
- ✅ Standalone - can be run independently without the framework

---

## Configuration Details

### 1. Config File: `config/config.ini`

```ini
[playwright_mcp]
server_mode = always_run
startup_timeout = 30

# Default Agent Mode
default_agent_mode = automation
```

**Location:** Lines 93-98 in `config/config.ini`

### 2. API Routes: `app/routes/api.py`

The default agent mode is loaded from config and used in all API endpoints:

```python
# Line 26-28: Load configuration
config = configparser.ConfigParser()
config.read('config/config.ini')
DEFAULT_AGENT_MODE = config.get('playwright_mcp', 'default_agent_mode', fallback='automation')

# Line 142: Used in /api/execute endpoint
agent_mode = data.get('agent_mode', DEFAULT_AGENT_MODE)

# Line 239: Used in /api/execute/stream endpoint
agent_mode = data.get('agent_mode', DEFAULT_AGENT_MODE)
```

### 3. Agent Implementation: `app/engines/playwright_mcp/agent/conversation_agent.py`

The automation mode is implemented in the `_execute_automation_mode` method (lines 499-570).

---

## Available Agent Modes

You can override the default by specifying `agent_mode` in your API request:

| Mode | Description | Output Files |
|------|-------------|--------------|
| **automation** ✅ | Execute task → Generate self-healing script | 1 Python script |
| direct | Direct execution only (no code generation) | 0 files |
| planner | Explore app → Create test plan | 1 Markdown spec |
| generator | Convert test plan → Playwright test | 1 Python test |
| healer | Fix failing tests | 1 fixed Python test |
| full_agent | Planner → Generator → Healer | 2 files (spec + test) |

---

## How to Use

### Via Dashboard (Web UI)
The dashboard will automatically use Automation Mode when you submit tasks through the web interface.

### Via API
```bash
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "Go to example.com and take a screenshot",
    "engine": "playwright_mcp",
    "headless": true
  }'
```

The `agent_mode` defaults to `automation` automatically.

### Override the Default
```bash
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "Go to example.com and take a screenshot",
    "engine": "playwright_mcp",
    "headless": true,
    "agent_mode": "direct"
  }'
```

---

## Verification

✅ **Application Status:** Running successfully on port 5000
✅ **Config File:** Updated with `default_agent_mode = automation`
✅ **API Routes:** Using DEFAULT_AGENT_MODE from config
✅ **Workflow:** Restarted and running without errors

---

## Migration Status

All migration tasks completed:

- [x] Install required packages
- [x] Restart workflow
- [x] Verify project is working
- [x] Configure Automation Agent Mode
- [x] Complete import

The application is fully operational and ready to use! 🎉
