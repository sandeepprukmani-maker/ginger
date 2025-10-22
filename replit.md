# AI Browser Automation CLI with Self-Healing Code Generation

## Overview
A Python CLI tool that performs OpenAI-powered browser automation with **self-healing Playwright code generation**. The tool has two key features:
1. **AI Browser Automation**: Run tasks using natural language with browser-use
2. **Self-Healing Code Generation**: Convert browser-use actions into reusable Playwright code with automatic locator healing

## Current State
- **Status**: Active Development - Self-Healing Features Added
- **Language**: Python 3.11
- **Framework**: browser-use + OpenAI gpt-4o-mini + Playwright + LangChain
- **Last Updated**: October 22, 2025

## Recent Changes
### October 22, 2025 - Enhanced Self-Healing with AI Fallback Execution
- **ENHANCED**: Self-healing now includes browser-use AI fallback execution
  - When healed locator fails, browser-use AI executes the specific action
  - AI gracefully exits after completing the action
  - Automation script continues with remaining steps
  - No manual intervention required
- Added AIExecutedMarker class to track AI-executed actions
- Updated documentation with enhanced self-healing flow

### October 22, 2025 - Self-Healing Code Generation Added
- **NEW**: PlaywrightCodeGenerator - Converts browser-use actions to reusable Playwright code
- **NEW**: SelfHealingExecutor - AI-powered locator healing for generated code execution
- **NEW**: CLI modes: --generate-code and --execute-code with self-healing
- **NEW**: Locator utilities with multiple fallback strategies
- Updated automation engine to support code generation mode
- Created test workflow for validation
- Updated documentation with new features

### October 22, 2025 - Initial Setup
- Initial project setup
- Installed dependencies: browser-use, langchain-openai, python-dotenv, playwright
- Installed Chromium browser via Nix system dependencies
- Created core CLI application (main.py)
- Implemented browser automation engine (automation_engine.py)
- Added project documentation (README.md)

## Project Architecture

### Main Components
1. **main.py** - CLI entry point with three modes: automation, code generation, and self-healing execution
2. **automation_engine.py** - Core automation logic with browser-use and code generation support
3. **playwright_code_generator.py** - Converts browser-use action history to Playwright code
4. **self_healing_executor.py** - Executes generated code with AI-powered locator healing
5. **locator_utils.py** - Helper utilities for robust locator strategies
6. **test_workflow.py** - Test script for the complete workflow

### Dependencies
- **browser-use (0.5.9+)**: AI-powered browser automation framework
- **langchain-openai**: OpenAI integration for LangChain
- **playwright**: Browser automation backend for code execution
- **python-dotenv**: Environment variable management
- **openai**: OpenAI API client

### Technology Stack
- Python 3.11+
- OpenAI gpt-4o-mini (newest model, released August 7, 2025)
- Playwright for generated code execution
- browser-use for initial automation and self-healing
- LangChain for AI orchestration

## How It Works

### Mode 1: Direct Browser Automation (Original)
1. User provides natural language task via CLI
2. browser-use Agent interprets and executes the task
3. Results returned to user

### Mode 2: Code Generation (NEW)
1. User provides task with `--generate-code` flag
2. browser-use Agent performs the automation
3. Action history is captured and parsed
4. PlaywrightCodeGenerator converts actions to reusable Python code
5. Generated code includes multiple locator fallback strategies
6. Code saved to file for later execution

### Mode 3: Self-Healing Execution with AI Fallback (ENHANCED)
1. User runs generated code with `--execute-code` flag
2. SelfHealingExecutor loads and runs the Playwright script
3. **When a locator fails:**
   - Execution pauses (same browser session maintained)
   - browser-use AI intervenes to analyze the page
   - AI finds the element using intelligent heuristics
   - New working locator is generated and cached
   - Execution resumes smoothly with remaining steps
4. **If healed locator also fails:**
   - browser-use AI steps in to execute the specific failed action
   - AI completes just that one action (click, fill, etc.)
   - AI gracefully exits, returning control to the automation script
   - Script continues executing remaining steps normally
5. Process continues until all steps complete

## Usage Examples

### Basic Automation (Mode 1)
```bash
# Simple task
python main.py "go to example.com and tell me the page title"

# Web scraping
python main.py "scrape top 10 Hacker News posts" --verbose

# Form automation
python main.py "fill out contact form with test data" --no-headless
```

### Code Generation (Mode 2)
```bash
# Generate reusable Playwright code
python main.py "go to example.com and click login" --generate-code

# Specify custom output file
python main.py "search for Python on Google" --generate-code --output search_google.py

# Generate with verbose logging
python main.py "navigate to GitHub trending" --generate-code --verbose
```

### Self-Healing Execution (Mode 3)
```bash
# Execute generated code with self-healing
python main.py --execute-code generated_automation.py

# Execute with verbose healing logs
python main.py --execute-code search_google.py --verbose

# The self-healing will automatically:
# - Detect when locators fail
# - Use AI to find correct elements
# - Generate new working locators
# - Resume execution smoothly
```

### Complete Workflow
```bash
# Step 1: Record and generate code
python main.py "go to example.com, click login, fill email with test@email.com" \
  --generate-code --output login_flow.py --verbose

# Step 2: Execute with self-healing (even if page changes)
python main.py --execute-code login_flow.py --verbose
```

## Environment Variables
- `OPENAI_API_KEY` (required): OpenAI API key for gpt-4o-mini access

## Key Features

### 1. Multiple Locator Strategies
Generated code includes fallback locators:
- Text-based locators (exact and partial match)
- Role-based locators (ARIA roles)
- Label-based locators
- ID and test-ID locators
- CSS and XPath selectors

### 2. Enhanced AI-Powered Self-Healing with Fallback Execution
When locators break (page changes, updates, etc.):
- **Level 1 Healing**: AI finds new locator for the element
  - Same browser session maintained - no restart needed
  - AI analyzes the current page state
  - Intelligent element detection using heuristics
  - New locator generated and cached
- **Level 2 Fallback (NEW)**: If healed locator also fails
  - browser-use AI steps in to execute the specific action
  - AI completes just that one step (click, fill, etc.)
  - AI gracefully exits, returning control to automation
  - Script continues with remaining steps
- **Zero manual intervention required** - fully automated recovery

### 3. Verbose Logging
Track the entire process:
- Initial automation steps
- Code generation progress
- Locator failure detection
- Healing attempts and results
- Final execution status

## User Preferences
- Prefers AI-powered self-healing for generated code execution
- Wants healing to happen within the same browser session
- Wants clear separation: browser-use for initial automation, self-healing for generated code

## Technical Implementation Notes

### Enhanced Self-Healing Flow (Two-Level Recovery)
1. **Generated code execution starts** with Playwright
2. **Locator fails** → Exception caught
3. **Browser session preserved** → No browser restart
4. **Level 1: Locator Healing**
   - browser-use analyzes page via CDP connection
   - Smart heuristics match element by common patterns (login, search, submit, etc.)
   - New locator created and cached for reuse
   - If successful → Execution resumes with new locator
5. **Level 2: AI Fallback Execution (NEW)**
   - If healed locator also fails → browser-use AI steps in
   - AI executes the specific failed action (click, fill, etc.)
   - AI completes only that one step, nothing more
   - AI gracefully exits, returning control to automation script
   - If successful → Execution continues with remaining steps
6. **Complete automation** → All steps execute successfully

### Code Generation Process
1. browser-use records all actions (goto, click, fill, extract, etc.)
2. Action history parsed to extract element details
3. For each element, multiple locator strategies generated
4. Python code template populated with async/await Playwright syntax
5. Self-healing helper function included in generated code
6. Output saved as executable Python script

## Future Enhancements
- Export to Playwright Codegen format
- Video recording of healing process
- Locator confidence scoring
- Multi-language code generation (TypeScript, Java, C#)
- Configuration file for healing strategies
- Session replay and debugging tools
