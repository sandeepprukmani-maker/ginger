# AI Automation Runner with MCP Integration

## Overview

This is a Python Flask-based AI automation testing framework that executes AI-generated test plans using the Microsoft Playwright MCP (Model Context Protocol) server. The system translates JSON test plans into browser automation actions, using intelligent DOM analysis and accessibility-tree-based element location to interact with web pages. It provides a comprehensive HTTP API for test execution, reporting, and monitoring.

The core innovation is the intelligent locator selection system that analyzes the DOM accessibility tree, ranks potential element matches by confidence scores, and implements fallback strategies for robust automation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Layer (Flask HTTP API)
- **Framework**: Flask web server with REST endpoints
- **Port Configuration**: Runs on 0.0.0.0:5000 (configurable via Config class)
- **Main Endpoints**:
  - Test plan execution (`/api/execute`)
  - Execution status and reporting (`/api/executions/*`)
  - Test plan management (`/api/test-plans`)
  - Health monitoring (`/api/health`)
- **State Management**: In-memory dictionary storing execution reports keyed by execution ID

### Test Execution Engine
- **Core Component**: `TestExecutor` class orchestrates the entire test execution lifecycle
- **Process Flow**:
  1. Initializes MCP client with browser configuration
  2. Executes test steps sequentially
  3. Captures DOM snapshots for analysis
  4. Generates execution reports with detailed metrics
- **Retry Strategy**: Configurable retry mechanism with escalating fallback strategies (exact match → partial match → accessibility tree → structural analysis)
- **Confidence Scoring**: Validates element locators based on uniqueness and stability before execution
- **Multi-Page Support**: Seamlessly navigates across multiple pages with automatic DOM re-analysis
- **Tab Management**: Opens, switches between, and closes browser tabs while preserving context
- **Alert Handling**: Accepts, dismisses, and interacts with JavaScript alerts, confirms, and prompts

### Browser Automation (MCP Integration)
- **MCP Client**: Subprocess-based integration with `@playwright/mcp` npm package
- **Communication**: JSON-RPC over stdin/stdout pipes
- **Browser Support**: Chrome, Firefox, WebKit, MS Edge (configurable)
- **Execution Modes**: Headless and headed modes, optional device emulation
- **Tool Calls**: Translates test actions into MCP tool invocations (navigate, click, type, snapshot)

### DOM Analysis System
- **DOMAnalyzer**: Parses accessibility tree snapshots into searchable element registry
- **Element Indexing**: Builds hierarchical map of page elements with roles, text, ARIA labels, and XPath
- **Search Capabilities**:
  - Exact and partial text matching
  - ARIA label matching
  - Role-based element lookup
  - Attribute-based filtering

### Locator Intelligence
- **LocatorSelector**: Implements confidence-based element matching algorithm
- **Ranking Strategy**:
  - Exact text match: 0.95 base score
  - Partial text match: 0.75 base score
  - ARIA label match: 0.85 base score
- **Confidence Threshold**: Configurable minimum confidence (default 0.7)
- **Candidate Generation**: Creates multiple locator candidates per target, ranks by confidence

### Data Models (Pydantic)
- **TestPlan**: JSON schema for test definitions with steps, browser config
- **TestStep**: Individual action definitions (navigate, click, type, snapshot, wait)
- **ExecutionReport**: Comprehensive execution results with step details, MCP statistics
- **LocatorCandidate**: Element matching results with confidence scoring
- **DOMElement**: Structured representation of accessibility tree nodes

### Configuration Management
- **Environment-based**: Loads settings from `.env` file using python-dotenv
- **Key Settings**:
  - Browser selection and headless mode
  - Retry parameters (max retries, delay)
  - Locator confidence threshold
  - Directory paths for logs, screenshots, reports

### Logging and Reporting
- **Dual Output**: File-based logs and console streaming
- **Timestamped Files**: Creates unique log files per execution session
- **Execution Summaries**: MCP tool statistics, locator accuracy metrics, DOM analysis details
- **Screenshot Capture**: Timestamped screenshots via MCP page_snapshot tool

### File Storage
- **Directory Structure**:
  - `logs/`: Execution logs with timestamps
  - `screenshots/`: Page snapshots from MCP
  - `test_plans/`: JSON test plan definitions
  - `reports/`: Execution report outputs
- **Test Plans**: JSON files defining multi-step automation scenarios

## External Dependencies

### Python Packages
- **Flask**: Web framework for HTTP API
- **Pydantic**: Data validation and schema definition
- **Requests**: HTTP client library
- **python-dotenv**: Environment variable management

### Node.js Packages
- **@playwright/mcp**: Microsoft Playwright MCP server for browser automation
- **Execution**: Spawned as subprocess, communicates via JSON-RPC

### Browser Requirements
- Requires Node.js 18+ runtime
- Playwright browser binaries (Chrome, Firefox, WebKit, Edge)
- Installed automatically via npx on first run

### System Dependencies
- Python 3.11+ runtime
- Subprocess support for MCP server communication
- File system access for logs, screenshots, and reports