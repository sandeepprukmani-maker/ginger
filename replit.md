# Overview

This is a browser automation framework built with Python and Playwright that provides multiple interfaces for web automation:

1. **Basic Browser Automation** - Direct Playwright-based automation with smart selectors and error handling
2. **Natural Language Automation** - AI-powered automation using OpenAI to convert natural language commands into browser actions
3. **MCP Integration** - Integration with Playwright's Model Context Protocol (MCP) server for advanced automation capabilities
4. **Vision-Based Analysis** - GPT-4 Vision integration for intelligent element detection and page understanding

The framework is designed to make browser automation accessible through multiple layers of abstraction, from low-level Playwright control to high-level natural language commands.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Components

### 1. Browser Engine (`browser_engine.py`)
- **Purpose**: Low-level Playwright wrapper providing browser lifecycle management
- **Key Features**:
  - Multi-browser support (Chromium, Firefox, WebKit)
  - Automatic directory setup for screenshots, videos, and sessions
  - Built-in retry logic using Tenacity
  - Smart selector system supporting CSS, XPath, text, and ARIA selectors
  - Configurable viewport, locale, timezone, and proxy settings
- **Design Decision**: Separated browser management from task execution for better modularity and testability

### 2. Task Executor (`task_executor.py`)
- **Purpose**: High-level task orchestration layer
- **Capabilities**: Navigate, click, fill forms, extract text/links, screenshots, waiting, scrolling, script execution
- **Design Pattern**: Command pattern with TaskType enum and TaskResult dataclass for structured execution
- **Rationale**: Provides a clean API layer between low-level browser operations and high-level automation logic

### 3. Smart Selectors (`selectors.py`)
- **Auto-detection Strategy**: Automatically tries CSS → XPath → Text → ARIA selectors until one succeeds
- **Configuration**: Supports timeout, element state (visible/hidden), and strict mode
- **Design Decision**: Fallback selector strategy improves reliability when dealing with dynamic web pages

### 4. AI Integration Layer

#### AI Task Generator (`ai_generator.py`)
- **Purpose**: Converts natural language task descriptions into executable Playwright code
- **Implementation**: Uses OpenAI GPT models with specialized system prompts
- **Graceful Degradation**: Framework functions without AI when OpenAI package/API key unavailable

#### Vision Analyzer (`vision_analyzer.py`)
- **Purpose**: Uses GPT-4 Vision to understand page layouts and locate elements visually
- **Use Case**: Fallback when traditional selectors fail or for complex visual element detection
- **Returns**: ElementLocation objects with suggested selectors and confidence scores

### 5. MCP Client (`mcp_client.py`)
- **Purpose**: Interface to Playwright's Model Context Protocol server
- **Communication**: Uses stdio-based IPC with the `@playwright/mcp` npm package
- **Environment Handling**: Includes NixOS-specific environment variable configuration
- **Design Decision**: Separates MCP communication from core browser automation, allowing the framework to work with or without MCP

### 6. Advanced Tools (`advanced_tools.py`)
- **Rich Context Capture**: Provides PageContext dataclass with URL, title, iframe detection, DOM snapshots, and screenshots
- **Capabilities**: Handles iframes, popups, dynamic content, file operations
- **Context History**: Maintains history of page states for debugging and analysis

### 7. Session Memory (`session_memory.py`)
- **Purpose**: Persistent storage of execution history and successful patterns
- **Storage Format**: JSON-based memory file tracking executions and patterns
- **Learning**: Records successes and failures to improve future automation attempts
- **Rationale**: Enables the framework to learn from past executions and avoid repeated mistakes

### 8. Browser Recorder (`recorder.py`)
- **Purpose**: Records user interactions and generates automation code
- **Mechanism**: Injects JavaScript into browser to capture DOM events
- **Storage**: Uses sessionStorage to persist events across page loads
- **Output**: Generates both natural language commands and Playwright code from recordings

## Configuration System

### Two-Level Configuration
1. **Browser Config** (`BrowserConfig`): Browser-specific settings (type, headless, viewport, user agent, proxy, etc.)
2. **Automation Config** (`AutomationConfig`): Framework-level settings (retries, delays, logging, directories)

### Config Loader (`config_loader.py`)
- **Format**: INI file support with environment variable substitution
- **Pattern**: Uses `${ENV_VAR}` syntax for sensitive values
- **Type Safety**: Helper methods for bool and int conversions

## Logging and Error Handling

### Rich Console Integration
- **Library**: Uses Rich library for beautiful terminal output
- **Features**: Colored logs, tables, panels, progress indicators
- **Themes**: Custom theme with info (cyan), warning (yellow), error (red), success (green)

### Error Recovery
- **Retry Logic**: Tenacity-based exponential backoff for network operations
- **Screenshots**: Automatic screenshot capture on errors when enabled
- **Graceful Degradation**: Framework components work independently; missing dependencies don't crash the system

## Entry Points

1. **main.py**: Interactive demo for basic web automation
2. **nl_automation_mcp.py**: Enhanced natural language automation with vision and memory
3. **test_automation.py**: Test suite for framework validation

# External Dependencies

## Python Packages
- **mcp** (≥1.18.0): Model Context Protocol for Playwright server communication
- **openai** (≥2.4.0): GPT-4 and GPT-4 Vision API access for AI-powered automation
- **playwright** (≥1.55.0): Core browser automation library
- **pydantic** (≥2.12.2): Data validation and settings management
- **python-dotenv** (≥1.1.1): Environment variable management
- **rich** (≥14.2.0): Terminal formatting and beautiful console output
- **tenacity** (≥9.1.2): Retry logic and error handling

## Node.js Packages
- **@playwright/mcp** (^0.0.43): Playwright MCP server for advanced automation capabilities
- **playwright** (1.57.0-alpha): Node.js Playwright for MCP server
- **playwright-core** (1.57.0-alpha): Core Playwright functionality

## External Services
- **OpenAI API**: Required for AI task generation and vision analysis features
  - API key configured via `OPENAI_API_KEY` environment variable
  - Used for: Natural language to code conversion, page structure analysis, element detection
  - Gracefully disabled when unavailable

## File System Dependencies
- **Screenshots Directory**: Configurable location for screenshot storage
- **Videos Directory**: For browser session recordings (when enabled)
- **Sessions Directory**: For session memory and execution history persistence
- **Downloads Path**: Optional custom downloads location

## Browser Binaries
- Playwright automatically downloads browser binaries for Chromium, Firefox, and WebKit
- Stored in Playwright's cache directory
- Managed automatically by Playwright installation

## Environment Variables
- `OPENAI_API_KEY`: Required for AI features
- `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`: Optional NixOS environment configuration