# AI Automation Runner with MCP Integration

A Python Flask-based AI automation runner that integrates with Microsoft Playwright MCP server to execute AI-generated test plans using accessibility-driven browser automation.

## Features

- **MCP Client Integration**: Connects to Microsoft Playwright MCP server (@playwright/mcp) with configurable browser options
- **DOM Accessibility Tree Analysis**: Captures full page structure and builds searchable element registry
- **Intelligent Locator Selection**: Ranks and validates elements based on role, text, aria-labels, and DOM hierarchy
- **Confidence Scoring**: Evaluates uniqueness and stability of identified elements before execution
- **Multi-Step Test Plans**: Translates JSON plans into validated MCP tool calls
- **Intelligent Retry Mechanism**: Escalating fallback strategies (exact → partial → accessibility tree → structural)
- **Multi-Page Navigation**: Seamless navigation across multiple pages with automatic DOM re-analysis
- **Multi-Tab Support**: Open, switch between, and close browser tabs with context preservation
- **Alert/Dialog Handling**: Accept, dismiss, and interact with JavaScript alerts, confirms, and prompts
- **Comprehensive Logging**: DOM audit logs showing element analysis, locator candidates, and confidence scores
- **Flask HTTP API**: Endpoints for test plan submission, status queries, and execution reports
- **Execution Summaries**: MCP tool statistics, locator accuracy metrics, and DOM analysis details
- **Screenshot Capture**: Timestamped screenshots via MCP page_snapshot tool

## Prerequisites

- Python 3.11+
- Node.js 18+ (for MCP server)

## Installation

Dependencies are already installed:
- Flask
- Pydantic
- Requests
- Python-dotenv

## Configuration

Environment variables (see `.env.example`):

```env
DEBUG=False
MCP_BROWSER=chrome              # chrome, firefox, webkit, msedge
MCP_HEADLESS=false              # true/false
MCP_DEVICE=                     # Optional: "iPhone 15", etc.
MAX_RETRIES=3
RETRY_DELAY=2.0
LOCATOR_CONFIDENCE_THRESHOLD=0.7
```

## API Endpoints

### Health Check
```bash
GET /api/health
```

### Execute Test Plan
```bash
POST /api/execute
Content-Type: application/json

{
  "id": "test_001",
  "name": "My Test",
  "description": "Test description",
  "browser": "chrome",
  "headless": false,
  "steps": [
    {
      "action": "navigate",
      "description": "Open page",
      "target": "https://example.com",
      "timeout": 5000
    },
    {
      "action": "click",
      "description": "Click button",
      "target": "Submit",
      "timeout": 3000
    }
  ]
}
```

### List Executions
```bash
GET /api/executions
```

### Get Execution Details
```bash
GET /api/executions/{execution_id}
```

### Get Execution Report
```bash
GET /api/executions/{execution_id}/report
```

### Upload Test Plan
```bash
POST /api/test-plans
```

### List Test Plans
```bash
GET /api/test-plans
```

### Get DOM Analysis
```bash
GET /api/dom-analysis/{execution_id}
```

## Test Plan Format

```json
{
  "id": "unique_id",
  "name": "Test Name",
  "description": "Test description",
  "browser": "chrome",
  "headless": false,
  "steps": [
    {
      "action": "navigate|click|type|snapshot|wait|handle_alert|switch_tab|wait_for_new_tab|close_tab|get_alert_text",
      "description": "Step description",
      "target": "URL or element description",
      "value": "Text to type (for type action) or prompt text (for alerts)",
      "timeout": 5000,
      "alert_action": "accept|dismiss (for handle_alert)",
      "tab_index": 0
    }
  ]
}
```

## Supported Actions

### Basic Actions
- **navigate**: Navigate to URL (target = URL)
- **click**: Click element (target = element description)
- **type**: Type text (target = element description, value = text)
- **snapshot**: Capture accessibility tree and screenshot
- **wait**: Wait for specified time (timeout in ms)

### Alert/Dialog Actions
- **handle_alert**: Accept or dismiss JavaScript alerts/confirms (alert_action = "accept"|"dismiss", value = prompt text for prompts)
- **get_alert_text**: Retrieve text from current alert dialog

### Multi-Tab Actions
- **wait_for_new_tab**: Wait for a new tab/window to open after an action
- **switch_tab**: Switch to a specific tab (tab_index = 0, 1, 2, etc.)
- **close_tab**: Close a specific tab or current tab (tab_index = optional)

## DOM Analysis

The system analyzes the accessibility tree to find elements using:

1. **Exact text match** (confidence: 0.95)
2. **Partial text match** (confidence: 0.75)
3. **ARIA label match** (confidence: 0.85)
4. **Placeholder match** (confidence: 0.80)

Confidence scoring considers:
- Element role (button, link, input, etc.)
- ARIA labels
- DOM depth
- Child count

## Retry Mechanism

When element location fails, the system:

1. Retries with fresh accessibility tree snapshot
2. Uses fallback locators (text, role, siblings)
3. Adjusts confidence threshold (80% of original)
4. Maximum retries: 3 (configurable)

## Execution Reports

Reports include:
- MCP tool usage statistics
- DOM elements analyzed count
- Locators corrected count
- Total retry attempts
- Screenshots captured
- Step-by-step execution details
- Error summaries

## Example Usage

```bash
# Execute example test plan
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d @test_plans/example_google_search.json

# Check execution status
curl http://localhost:5000/api/executions/{execution_id}

# Get DOM analysis
curl http://localhost:5000/api/dom-analysis/{execution_id}
```

## Architecture

- **app.py**: Flask application and API endpoints
- **mcp_client.py**: MCP server subprocess management
- **dom_analyzer.py**: Accessibility tree parsing and element registry
- **locator_selector.py**: Intelligent locator selection with confidence scoring
- **test_executor.py**: Test plan execution with retry logic
- **models.py**: Pydantic data models
- **config.py**: Configuration management
- **execution_logger.py**: Logging setup

## Directories

- `logs/`: Execution logs
- `screenshots/`: Captured screenshots
- `test_plans/`: Test plan JSON files
- `reports/`: Execution reports

## MCP Integration

This application uses Microsoft's Playwright MCP server (@playwright/mcp) which provides:
- Browser automation via Model Context Protocol
- Accessibility tree snapshots for deterministic element identification
- Support for multiple browsers (Chrome, Firefox, WebKit, Edge)
- Headless and headful modes
- Device emulation
