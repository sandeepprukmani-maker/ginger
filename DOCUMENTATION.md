# Self-Healing Browser Automation System

**A production-ready Flask web application for intelligent browser automation with AI-powered self-healing capabilities.**

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [API Reference](#api-reference)
8. [WebSocket Events](#websocket-events)
9. [Self-Healing Mechanism](#self-healing-mechanism)
10. [Code Generation](#code-generation)
11. [Database Schema](#database-schema)
12. [Technology Stack](#technology-stack)
13. [Troubleshooting](#troubleshooting)
14. [Deployment](#deployment)
15. [Contributing](#contributing)
16. [License](#license)

---

## Overview

This system combines **browser-use** (AI-powered automation with GPT-4) and **Microsoft Playwright MCP server** (accessibility-based healing) to create a robust, self-healing browser automation platform. When automation steps fail due to changing locators or page structure, the system automatically attempts to heal the failure using a two-tier approach.

### Key Capabilities

- **Natural Language Instructions**: Execute browser tasks using plain English
- **Automatic Healing**: Two-tier recovery system (AI + accessibility-based)
- **Real-Time Monitoring**: WebSocket-based live execution updates
- **Code Generation**: Generate executable Playwright scripts with healed locators
- **Production Ready**: Comprehensive logging, error handling, and database persistence

---

## Features

### Core Features

- ✅ **Natural Language Automation**: Submit tasks in plain English (e.g., "Go to google.com and search for 'AI automation'")
- ✅ **Two-Tier Self-Healing**:
  - **Tier 1**: browser-use AI-powered healing (2 retries)
  - **Tier 2**: Microsoft Playwright MCP server fallback (2 retries)
- ✅ **Real-Time Dashboard**: Live WebSocket updates of execution progress
- ✅ **Action Logging**: Complete history of all steps, locators, and healing events
- ✅ **Script Generation**: Automatically generate executable Playwright Python scripts
- ✅ **Statistics & Reporting**: Track healing success rates and sources
- ✅ **Headless/Headful Mode**: User-selectable browser visibility
- ✅ **Cross-Platform**: Windows, macOS, and Linux compatible

### Technical Features

- Professional Bootstrap 5 UI with responsive design
- SQLAlchemy ORM with SQLite database
- Flask-SocketIO for real-time bidirectional communication
- Eventlet async worker for concurrent task handling
- Comprehensive error handling and logging
- YAML-based configuration system
- UTF-8 encoding for international character support

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (Browser)                 │
│            Bootstrap 5 + Socket.IO + JavaScript              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ WebSocket + REST API
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routes     │  │  Socket.IO   │  │  Main App    │      │
│  │   (API)      │  │   Events     │  │  (Entry)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer                               │
│  ┌──────────────────┐  ┌────────────────┐  ┌─────────────┐ │
│  │ Healing          │  │ Browser-Use    │  │ MCP Server  │ │
│  │ Orchestrator     │←→│ Service        │  │ Service     │ │
│  │ (Coordinator)    │  │ (AI Tier)      │  │ (Fallback)  │ │
│  └─────────┬────────┘  └────────────────┘  └─────────────┘ │
│            │                                                 │
│            ↓                                                 │
│  ┌──────────────────┐  ┌────────────────┐                  │
│  │ Code Generator   │  │ Database       │                  │
│  │ (Scripts)        │  │ Manager        │                  │
│  └──────────────────┘  └────────┬───────┘                  │
└─────────────────────────────────┼───────────────────────────┘
                                  │
                                  ↓
                    ┌──────────────────────────┐
                    │   SQLite Database        │
                    │  - tasks                 │
                    │  - action_logs           │
                    │  - healing_events        │
                    └──────────────────────────┘
```

### Component Descriptions

1. **Flask Application** (`application.py`)
   - Main entry point with Socket.IO configuration
   - Initializes all services and routes
   - Handles WebSocket events for real-time communication

2. **Routes** (`app/routes/main.py`)
   - REST API endpoints for task management
   - Script generation and download
   - Statistics and reporting

3. **Healing Orchestrator** (`app/services/healing_orchestrator.py`)
   - Coordinates the two-tier healing system
   - Manages retry logic and fallback mechanisms
   - Emits real-time progress updates

4. **Browser-Use Service** (`app/services/browser_use_service.py`)
   - AI-powered automation using OpenAI GPT-4
   - Primary execution and Tier 1 healing
   - Natural language task interpretation

5. **MCP Server Service** (`app/services/mcp_service.py`)
   - Microsoft Playwright MCP server integration
   - Accessibility-based Tier 2 healing
   - Subprocess management and JSON-RPC communication

6. **Code Generator** (`app/services/code_generator.py`)
   - Generates executable Playwright Python scripts
   - Includes healed locators and self-healing logic
   - UTF-8 encoded for cross-platform compatibility

7. **Database Manager** (`app/models/database.py`)
   - SQLAlchemy ORM models (Task, ActionLog, HealingEvent)
   - Session management with scoped sessions
   - Thread-safe database operations

---

## Installation & Setup

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher (for MCP server)
- **npm/npx**: Latest version
- **OpenAI API Key**: Required for browser-use

### Step 1: Install Python Dependencies

All Python dependencies are managed via `pyproject.toml` and are already installed in the Replit environment:

```bash
# Dependencies are automatically installed in Replit
# For local installation:
pip install -r requirements.txt
# or with uv:
uv pip install -e .
```

### Step 2: Install Node.js MCP Server

The Microsoft Playwright MCP server is required for Tier 2 healing. It's installed on-demand via `npx`:

#### On Linux/macOS:

```bash
# MCP server is automatically invoked via npx
# No manual installation needed
npx @playwright/mcp@latest --help
```

#### On Windows:

**Important**: Windows users need to ensure `npx` is in their PATH.

1. **Verify Node.js and npm installation**:
   ```cmd
   node --version
   npm --version
   ```

2. **Verify npx is available**:
   ```cmd
   npx --version
   ```

3. **If npx is not found**, add Node.js to PATH:
   - Find your Node.js installation path (usually `C:\Program Files\nodejs\`)
   - Add it to System PATH environment variable
   - Restart your terminal/IDE

4. **Test MCP server installation**:
   ```cmd
   npx -y @playwright/mcp@latest --help
   ```

5. **If you encounter issues**, install globally:
   ```cmd
   npm install -g @playwright/mcp
   ```

#### Troubleshooting MCP Installation

**Error**: `[WinError 2] The system cannot find the file specified`

**Solution**:
1. Ensure Node.js is installed and in PATH
2. Run `npm config get prefix` to verify npm installation
3. Add the npm global bin directory to PATH
4. Restart your terminal/command prompt

**Note**: The application will gracefully fall back to browser-use-only healing if MCP server is unavailable.

### Step 3: Install Playwright Browsers

```bash
playwright install chromium
# Optional: Install other browsers
playwright install firefox
playwright install webkit
```

### Step 4: Configure Environment Variables

Create or configure the following environment variables:

**In Replit**: Use the Secrets tab
**Locally**: Create a `.env` file

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional (defaults provided)
SESSION_SECRET=your-secure-random-secret-key
DATABASE_PATH=data/automation.db
```

### Step 5: Initialize Database

The database is automatically created on first run:

```bash
# Database and directories are auto-created
python application.py
```

### Step 6: Verify Installation

```bash
# Start the application
python main.py

# The server should start on http://0.0.0.0:5000
# Open your browser and navigate to http://localhost:5000
```

---

## Configuration

### YAML Configuration File

Edit `config/config.yaml` to customize behavior:

```yaml
# Healing Configuration
healing:
  max_retries: 3                    # Total retry attempts
  browser_use_retry_limit: 2        # Tier 1 (browser-use) retries
  mcp_retry_limit: 2                # Tier 2 (MCP) retries
  timeout_seconds: 30               # Timeout per healing attempt

# Browser Configuration
browser:
  headless: true                    # Default browser mode
  viewport_width: 1920              # Browser viewport width
  viewport_height: 1080             # Browser viewport height
  default_timeout: 30000            # Default timeout in milliseconds

# MCP Server Configuration
mcp:
  server_startup_timeout: 10        # Seconds to wait for MCP startup
  command_timeout: 60               # Command execution timeout
  browser: "chromium"               # Browser for MCP (chromium/firefox/webkit)
  capabilities: []                  # Additional browser capabilities

# Execution Configuration
execution:
  max_concurrent_tasks: 3           # Maximum parallel tasks
  step_delay_ms: 500                # Delay between steps
  screenshot_on_error: true         # Take screenshots on errors

# Logging Configuration
logging:
  level: "INFO"                     # Log level (DEBUG/INFO/WARNING/ERROR)
  file: "logs/automation.log"       # Log file path
  max_file_size: 10485760           # 10MB max log file size
  backup_count: 5                   # Number of backup log files

# Export Configuration
export:
  script_directory: "data/generated_scripts"
  action_log_directory: "data/action_logs"
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT-4 |
| `SESSION_SECRET` | No | Auto-generated | Flask session encryption key |
| `DATABASE_PATH` | No | `data/automation.db` | SQLite database path |

---

## Usage Guide

### Starting the Application

```bash
# Replit: Click the "Run" button or
python main.py

# The server starts on http://0.0.0.0:5000
# Access the dashboard at http://localhost:5000
```

### Executing Automation Tasks

1. **Navigate to the Dashboard**
   - Open http://localhost:5000 in your browser

2. **Enter an Instruction**
   - Type your task in plain English
   - Example: "Go to google.com and search for 'browser automation'"

3. **Select Browser Mode**
   - Toggle "Headless" for background execution
   - Or "Headful" to watch the browser in action

4. **Click "Execute with Healing"**
   - The task is submitted to the system
   - Real-time updates appear in the execution monitor

5. **Monitor Progress**
   - Watch the real-time execution monitor
   - See healing attempts as they occur
   - View success/failure status

6. **Review Results**
   - Check the task history table
   - Click on a task to view detailed logs
   - Download generated scripts

### Example Instructions

```text
Basic Navigation:
- "Go to example.com"
- "Navigate to github.com"

Search Tasks:
- "Go to google.com and search for 'AI automation'"
- "Open bing.com, search for 'python web scraping'"

Form Filling:
- "Go to example.com/contact and fill the name field with 'John Doe'"
- "Navigate to login.example.com, fill username with 'test@example.com'"

Click Actions:
- "Go to example.com and click the 'Sign Up' button"
- "Open example.com, click on 'Products', then click 'View Details'"

Complex Multi-Step:
- "Go to github.com, click sign in, fill username with 'test@example.com', and fill password with 'test123'"
- "Navigate to example.com, click on 'Contact Us', fill the form with name 'John', email 'john@example.com', and submit"
```

### Viewing Task Details

1. **In the Task History Table**
   - Click the eye icon next to any task
   - Modal opens with:
     - Task status and metrics
     - Action logs (step-by-step)
     - Healing events
     - Generated script preview

2. **Download Generated Script**
   - Click "Download Script" in the task detail modal
   - Script is a standalone Python file
   - Can be executed independently

### Executing Generated Scripts

**From the UI**:
- Click "Execute Script" in task details (if implemented)

**From Command Line**:
```bash
cd data/generated_scripts
python task_<id>_<timestamp>.py
```

---

## API Reference

### REST API Endpoints

#### Dashboard
```http
GET /
```
Returns the main dashboard HTML page.

---

#### List All Tasks
```http
GET /api/tasks
```

**Response**:
```json
{
  "success": true,
  "tasks": [
    {
      "id": 1,
      "instruction": "Go to google.com",
      "status": "completed",
      "created_at": "2025-10-23T12:00:00",
      "started_at": "2025-10-23T12:00:01",
      "completed_at": "2025-10-23T12:00:05",
      "total_steps": 1,
      "successful_steps": 1,
      "failed_steps": 0,
      "healed_steps": 0,
      "error_message": null,
      "generated_script_path": "data/generated_scripts/task_1_20251023_120005.py"
    }
  ]
}
```

---

#### Get Task Details
```http
GET /api/tasks/<task_id>
```

**Response**:
```json
{
  "success": true,
  "task": {
    "id": 1,
    "instruction": "Go to google.com and search for 'automation'",
    "status": "completed",
    ...
  }
}
```

---

#### Get Task Action Logs
```http
GET /api/tasks/<task_id>/logs
```

**Response**:
```json
{
  "success": true,
  "logs": [
    {
      "id": 1,
      "task_id": 1,
      "step_number": 1,
      "action_type": "execute_instruction",
      "status": "success",
      "healing_attempted": false,
      "healing_source": null,
      "execution_time": 2.5,
      ...
    }
  ]
}
```

---

#### Get Healing Events
```http
GET /api/tasks/<task_id>/healing
```

**Response**:
```json
{
  "success": true,
  "healing_events": [
    {
      "id": 1,
      "task_id": 1,
      "action_log_id": 5,
      "healing_source": "browser-use",
      "success": true,
      "healing_time": 1.2,
      ...
    }
  ]
}
```

---

#### Generate Script
```http
POST /api/tasks/<task_id>/generate-script
```

**Response**:
```json
{
  "success": true,
  "script_path": "data/generated_scripts/task_1_20251023_120005.py",
  "message": "Script generated successfully"
}
```

---

#### Download Script
```http
GET /api/tasks/<task_id>/download-script
```

Returns the script file as a download.

---

#### Get Script Content
```http
GET /api/tasks/<task_id>/script
```

**Response**:
```json
{
  "success": true,
  "content": "#!/usr/bin/env python3\n...",
  "path": "data/generated_scripts/task_1_20251023_120005.py",
  "filename": "task_1_20251023_120005.py"
}
```

---

#### Execute Script
```http
POST /api/tasks/<task_id>/execute-script
```

**Response**:
```json
{
  "success": true,
  "output": "Script execution output...",
  "error": "",
  "exit_code": 0,
  "message": "Script executed"
}
```

---

#### Get Statistics
```http
GET /api/stats
```

**Response**:
```json
{
  "success": true,
  "stats": {
    "tasks": {
      "total": 10,
      "completed": 8,
      "failed": 1,
      "running": 1
    },
    "healing": {
      "total_events": 5,
      "successful": 4,
      "browser_use": 3,
      "mcp": 1
    }
  }
}
```

---

#### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T12:00:00"
}
```

---

## WebSocket Events

### Client → Server Events

#### Execute Task
```javascript
socket.emit('execute_task', {
  instruction: "Go to google.com",
  headless: true
});
```

---

### Server → Client Events

#### Connection Response
```javascript
socket.on('connection_response', (data) => {
  console.log(data.status); // 'connected'
});
```

#### Task Created
```javascript
socket.on('task_created', (data) => {
  console.log('Task ID:', data.task_id);
  console.log('Instruction:', data.instruction);
});
```

#### Task Update
```javascript
socket.on('task_update', (data) => {
  console.log('Status:', data.status);
  // data contains full task object
});
```

#### Step Update
```javascript
socket.on('step_update', (data) => {
  console.log('Step:', data.step_number);
  console.log('Status:', data.status);
  // data contains full action log object
});
```

#### Healing Attempt
```javascript
socket.on('healing_attempt', (data) => {
  console.log('Source:', data.source); // 'browser-use' or 'mcp'
  console.log('Retry:', data.retry);
  console.log('Max Retries:', data.max_retries);
});
```

#### Healing Fallback
```javascript
socket.on('healing_fallback', (data) => {
  console.log('From:', data.from); // 'browser-use'
  console.log('To:', data.to);     // 'mcp'
});
```

#### Healing Event
```javascript
socket.on('healing_event', (data) => {
  console.log('Success:', data.success);
  console.log('Healing Time:', data.healing_time);
  // data contains full healing event object
});
```

#### Task Complete
```javascript
socket.on('task_complete', (data) => {
  console.log('Task ID:', data.task_id);
  console.log('Success:', data.success);
  console.log('Script Path:', data.script_path);
});
```

#### Task Error
```javascript
socket.on('task_error', (data) => {
  console.log('Task ID:', data.task_id);
  console.log('Error:', data.error);
});
```

#### Error
```javascript
socket.on('error', (data) => {
  console.log('Error Message:', data.message);
});
```

---

## Self-Healing Mechanism

### How It Works

The self-healing system operates in two tiers:

```
┌─────────────────────────────────────────────────────┐
│              Task Execution Begins                   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│         Browser-Use Executes Instruction             │
│              (Initial Attempt)                       │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    ✅ Success          ❌ Failure
         │                   │
         ↓                   ↓
┌─────────────┐    ┌────────────────────────────────┐
│  Complete   │    │  TIER 1: Browser-Use Healing   │
│  & Log      │    │  - Retry with AI (up to 2x)   │
└─────────────┘    │  - Natural language recovery   │
                   └────────────┬───────────────────┘
                                │
                      ┌─────────┴─────────┐
                      │                   │
                 ✅ Healed           ❌ Still Failing
                      │                   │
                      ↓                   ↓
             ┌─────────────┐    ┌────────────────────────────────┐
             │  Complete   │    │  TIER 2: MCP Fallback Healing  │
             │  & Log      │    │  - Accessibility-based search  │
             └─────────────┘    │  - DOM analysis (up to 2x)     │
                                └────────────┬───────────────────┘
                                             │
                                   ┌─────────┴─────────┐
                                   │                   │
                              ✅ Healed           ❌ Failed
                                   │                   │
                                   ↓                   ↓
                          ┌─────────────┐    ┌─────────────┐
                          │  Complete   │    │  Mark as    │
                          │  & Log      │    │  Failed     │
                          └─────────────┘    └─────────────┘
```

### Tier 1: Browser-Use Healing

**Method**: AI-powered re-interpretation of the task
**Retries**: Up to 2 attempts
**Strengths**:
- Understands context and intent
- Can adapt to significant page changes
- Natural language flexibility

**Example**:
```
Original instruction: "Click the submit button"
Browser-use healing: Re-analyzes the page to find any button that performs submission,
                     even if the button text changed from "Submit" to "Send"
```

### Tier 2: MCP Server Healing

**Method**: Accessibility-based element discovery
**Retries**: Up to 2 attempts
**Strengths**:
- Systematic DOM traversal
- ARIA label and role support
- Reliable for structured content

**Example**:
```
Failed selector: #submit-button
MCP healing: Searches for:
  1. Elements with id containing "submit"
  2. Buttons with text containing "submit"
  3. Elements with aria-label="submit"
  4. Returns: button.btn-primary (new selector)
```

### Healing Event Logging

Every healing attempt is logged with:
- **Original locator**: What failed
- **Healed locator**: What worked
- **Healing source**: browser-use or mcp
- **Success status**: true/false
- **Healing time**: Execution duration
- **Error messages**: If failed

This data is used to:
1. Generate improved scripts
2. Track healing success rates
3. Identify problematic selectors
4. Optimize healing strategies

---

## Code Generation

### Generated Script Features

The code generator creates standalone Playwright Python scripts with:

1. **Self-Healing Capabilities**: Built-in healing logic
2. **Healed Locators**: Uses proven, healed selectors
3. **Error Handling**: Try-except blocks for resilience
4. **Logging**: Console output for debugging
5. **UTF-8 Encoding**: Cross-platform compatibility

### Script Structure

```python
#!/usr/bin/env python3
"""
Auto-generated Self-Healing Playwright script from Task #1
Generated at: 2025-10-23 12:00:00
This script includes self-healing capabilities using browser-use and MCP.
"""

import asyncio
import os
import sys
from playwright.async_api import async_playwright

class SelfHealingScript:
    """Self-healing automation script"""
    
    async def initialize_healing(self):
        """Initialize healing services"""
        # Setup browser-use and MCP services
        
    async def heal_step(self, step_num, action, selector, error, value=""):
        """Attempt to heal a failed step"""
        # Tier 1: browser-use healing
        # Tier 2: MCP healing
        
    def update_script(self, step_num, old_selector, new_selector, healing_source):
        """Update this script file with healed selector"""
        # Self-modifying code to update selectors
        
    async def run(self):
        """Execute the automated workflow with self-healing"""
        failed_steps = []
        total_steps = 0
        
        # Step 1: Navigate to google.com
        try:
            await self.page.goto("https://google.com")
            total_steps += 1
        except Exception as e:
            healed_selector = await self.heal_step(1, "navigate", "https://google.com", str(e))
            if not healed_selector:
                failed_steps.append(1)
        
        # More steps...
        
        if failed_steps:
            print(f"[WARNING] Automation completed with {len(failed_steps)} failed step(s)")
            return False
        else:
            print("[SUCCESS] Automation completed successfully")
            return True

async def main():
    """Main entry point"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        script_path = os.path.abspath(__file__)
        healer = SelfHealingScript(page, script_path)
        success = await healer.run()
        
        await browser.close()
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

### Using Generated Scripts

**Execute Standalone**:
```bash
cd data/generated_scripts
python task_1_20251023_120000.py
```

**Customize and Reuse**:
```python
# Edit the script to add custom logic
# Example: Add assertions, screenshots, data extraction
async def run(self):
    # Original step
    await self.page.goto("https://example.com")
    
    # Add custom logic
    title = await self.page.title()
    assert "Example" in title, "Wrong page!"
    
    # Continue with automation...
```

---

## Database Schema

### Tables

#### `tasks`
Stores automation task metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| instruction | TEXT | Natural language instruction |
| status | VARCHAR(50) | pending/running/completed/failed |
| created_at | DATETIME | Task creation timestamp |
| started_at | DATETIME | Execution start time |
| completed_at | DATETIME | Execution end time |
| total_steps | INTEGER | Total step count |
| successful_steps | INTEGER | Successfully executed steps |
| failed_steps | INTEGER | Failed step count |
| healed_steps | INTEGER | Steps healed successfully |
| error_message | TEXT | Error details if failed |
| generated_script_path | VARCHAR(500) | Path to generated script |

---

#### `action_logs`
Stores individual step execution details.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| task_id | INTEGER | Foreign key to tasks |
| step_number | INTEGER | Step sequence number |
| action_type | VARCHAR(100) | execute_instruction/click/fill/etc |
| url | VARCHAR(2000) | Target URL (if applicable) |
| locator | JSON | Original locator data |
| original_locator | JSON | Pre-healing locator |
| status | VARCHAR(50) | pending/success/failed/healed |
| error_message | TEXT | Error details if failed |
| healing_attempted | BOOLEAN | Whether healing was tried |
| healing_source | VARCHAR(50) | browser-use/mcp/null |
| healed_locator | JSON | Post-healing locator |
| execution_time | FLOAT | Execution duration (seconds) |
| timestamp | DATETIME | Step execution time |
| retry_count | INTEGER | Number of retries |
| page_context | JSON | Page state during execution |

---

#### `healing_events`
Stores healing attempt details.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| action_log_id | INTEGER | Foreign key to action_logs |
| task_id | INTEGER | Foreign key to tasks |
| healing_source | VARCHAR(50) | browser-use/mcp |
| original_locator | JSON | Failed locator |
| healed_locator | JSON | Successful locator |
| success | BOOLEAN | Healing success status |
| error_message | TEXT | Error if healing failed |
| healing_time | FLOAT | Healing duration (seconds) |
| timestamp | DATETIME | Healing attempt time |

---

## Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| Flask | 3.1.2 | Web framework |
| Flask-SocketIO | 5.5.1 | WebSocket support |
| SQLAlchemy | 2.0.44 | ORM |
| Eventlet | 0.40.3 | Async worker |
| browser-use | 0.9.0 | AI automation |
| Playwright | 1.55.0 | Browser control |
| langchain-openai | 1.0.1 | OpenAI integration |
| Pydantic | 2.12.3 | Data validation |
| PyYAML | 6.0.3 | Config parsing |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Bootstrap | 5.3 | UI framework |
| Socket.IO | 4.x | WebSocket client |
| JavaScript | ES6+ | Frontend logic |
| Bootstrap Icons | 1.11 | Icons |
| Chart.js | 4.x | Visualizations (if used) |

### Infrastructure

| Component | Technology |
|-----------|------------|
| Database | SQLite 3 |
| MCP Server | @playwright/mcp (Node.js) |
| Logging | Python logging module |
| Config | YAML files |
| Session | Flask sessions |

---

## Troubleshooting

### Common Issues

#### 1. MCP Server Not Starting (Windows)

**Error**: `[WinError 2] The system cannot find the file specified`

**Cause**: `npx` is not in PATH or Node.js is not installed.

**Solution**:
```cmd
# Verify Node.js installation
node --version
npm --version

# Add Node.js to PATH (example path)
set PATH=%PATH%;C:\Program Files\nodejs

# Test npx
npx --version

# Install MCP globally if needed
npm install -g @playwright/mcp
```

---

#### 2. OpenAI API Key Not Found

**Error**: `OPENAI_API_KEY not found in environment`

**Solution**:
- **Replit**: Add to Secrets tab
- **Local**: Add to `.env` file:
  ```env
  OPENAI_API_KEY=sk-your-key-here
  ```
- Restart the application

---

#### 3. Database Locked Errors

**Error**: `database is locked`

**Cause**: Multiple processes accessing SQLite simultaneously.

**Solution**:
```python
# Already configured in DatabaseManager
# pool_pre_ping=True enables connection health checks
# check_same_thread=False allows multi-threaded access
```

For production, migrate to PostgreSQL.

---

#### 4. Port 5000 Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 5000
# Linux/macOS:
lsof -i :5000
kill -9 <PID>

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

---

#### 5. Browser-Use Task Fails Immediately

**Error**: `'ChatOpenAI' object has no attribute 'provider'`

**Status**: ✅ Fixed in codebase

The compatibility workaround is already applied in `app/services/browser_use_service.py`.

---

#### 6. Unicode Encoding Errors (Windows)

**Error**: `'charmap' codec can't encode character`

**Status**: ✅ Fixed in codebase

UTF-8 encoding is enforced in all file operations.

---

#### 7. Eventlet Warnings

**Error**: `An exception was thrown while monkey_patching for eventlet`

**Status**: ✅ Fixed in codebase

`eventlet.monkey_patch()` is called before all imports in `application.py`.

---

#### 8. Browser Launch Timeout on Windows

**Error**: `Event handler browser_use.browser.watchdog_base.BrowserSession.on_BrowserStartEvent timed out after 30.0s`

**Cause**: Browser-use library takes longer to launch Playwright browsers on Windows, especially on first run or if browsers aren't properly installed.

**Solutions**:

**Step 1: Install Playwright Browsers** (Most Important)
```cmd
# In your virtual environment
playwright install chromium

# Or with system dependencies (requires admin)
playwright install chromium --with-deps
```

**Step 2: Verify Installation**
```cmd
# Test Playwright directly
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); print('✓ Browser launched successfully'); browser.close(); p.stop()"
```

**Step 3: Check Antivirus/Firewall**
- Windows Defender or other antivirus software may block Playwright
- Add Python and Playwright to antivirus exceptions
- Temporarily disable to test if it's the cause

**Step 4: Increase Timeout (Already configured)**
The codebase now includes:
- 120-second browser launch timeout (up from 30s)
- 3-minute task execution timeout
- Better error messages for Windows users

**Step 5: Use Headless Mode**
```yaml
# In config/config.yaml
browser:
  headless: true  # Headless mode is faster on Windows
```

**Additional Windows Tips**:
1. Close other browsers before running to free up resources
2. Run terminal as Administrator if permission errors occur
3. Ensure you have at least 2GB free RAM
4. Check Windows Task Manager for hung Playwright processes and end them

---

---

### Debugging Tips

#### Enable Debug Logging

Edit `config/config.yaml`:
```yaml
logging:
  level: "DEBUG"  # Change from INFO to DEBUG
```

#### Check Application Logs

```bash
tail -f logs/automation.log
```

#### Inspect Database

```bash
sqlite3 data/automation.db

# List tables
.tables

# View tasks
SELECT * FROM tasks;

# View action logs
SELECT * FROM action_logs WHERE task_id = 1;

# View healing events
SELECT * FROM healing_events WHERE task_id = 1;

# Exit
.quit
```

#### Test MCP Server Manually

```bash
npx -y @playwright/mcp@latest --headless

# Send test command (JSON-RPC)
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"browser_navigate","arguments":{"url":"https://example.com"}}}
```

---

## Deployment

### Replit Deployment (Current)

The application is already configured for Replit:

1. **Workflow**: Configured in `.replit`
2. **Port**: 5000 (exposed)
3. **Secrets**: Managed via Replit Secrets
4. **Database**: SQLite in `data/` directory

**To Publish**:
- Click "Publish" in Replit
- Configure custom domain (optional)
- Enable "Always On" for 24/7 availability

---

### Local Deployment

#### Development Server

```bash
python main.py
```

Access at: http://localhost:5000

#### Production Server (Gunicorn)

```bash
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --worker-class eventlet \
         --reuse-port \
         application:app
```

---

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install Node.js for MCP
RUN apt-get update && apt-get install -y nodejs npm

# Install Python dependencies
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data logs

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "eventlet", "application:app"]
```

Build and run:
```bash
docker build -t self-healing-automation .
docker run -p 5000:5000 -e OPENAI_API_KEY=your-key self-healing-automation
```

---

### Production Considerations

#### 1. Database Migration

**Migrate from SQLite to PostgreSQL**:

```python
# Update application.py
db_manager = DatabaseManager(os.getenv('DATABASE_URL'))

# Set environment variable
export DATABASE_URL=postgresql://user:pass@localhost/automation_db
```

#### 2. Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. Process Management (Systemd)

Create `/etc/systemd/system/automation.service`:

```ini
[Unit]
Description=Self-Healing Automation System
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/automation
Environment="OPENAI_API_KEY=your-key"
ExecStart=/opt/automation/.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class eventlet application:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable automation
sudo systemctl start automation
```

#### 4. Monitoring & Logging

- **Sentry**: Error tracking
- **Datadog**: Performance monitoring
- **Logrotate**: Log rotation
- **Uptime Robot**: Availability monitoring

#### 5. Security

- Use HTTPS (Let's Encrypt)
- Set strong `SESSION_SECRET`
- Implement rate limiting
- Add authentication (if needed)
- Restrict CORS origins
- Enable firewall rules

---

## Contributing

### Development Setup

1. Fork the repository
2. Clone your fork
3. Install dependencies
4. Create a feature branch
5. Make your changes
6. Run tests (if available)
7. Submit a pull request

### Code Standards

- Follow PEP 8 for Python code
- Add type hints to functions
- Include docstrings for classes and methods
- Write descriptive commit messages
- Update documentation for new features

### Testing

```bash
# Run tests (when available)
pytest

# Check code quality
flake8 app/
black --check app/
mypy app/
```

---

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Support & Contact

For issues, questions, or contributions:

- **GitHub Issues**: Report bugs or request features
- **Documentation**: This file
- **Community**: Join discussions (if available)

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-23  
**Status**: Production Ready ✅
