# AI Browser Automation CLI - Project Documentation

## Overview
A Python CLI tool that performs OpenAI-powered browser automation with comprehensive basic and advanced capabilities. Users describe tasks in natural language, and the AI handles the browser automation.

## Current State
- **Status**: Active Development
- **Language**: Python 3.11
- **Framework**: browser-use + OpenAI gpt-4o-mini + LangChain
- **Last Updated**: October 22, 2025

## Recent Changes
### October 22, 2025
- Initial project setup
- Installed dependencies: browser-use, langchain-openai, python-dotenv, playwright
- Installed Chromium browser via Nix system dependencies
- Created core CLI application (main.py)
- Implemented browser automation engine (automation_engine.py)
- Added project documentation (README.md)

## Project Architecture

### Main Components
1. **main.py** - CLI entry point with argument parsing
2. **automation_engine.py** - Core automation logic with browser-use and OpenAI integration
3. **.env** - Environment variables (not in git, use .env.example as template)

### Dependencies
- **browser-use (0.5.9)**: AI-powered browser automation framework
- **langchain-openai**: OpenAI integration for LangChain
- **playwright**: Browser automation backend
- **python-dotenv**: Environment variable management
- **pydantic**: Data validation and structured outputs

### Technology Stack
- Python 3.11+
- OpenAI gpt-4o-mini (newest model, released August 7, 2025)
- Playwright for browser control
- LangChain for AI orchestration

## How It Works
1. User provides natural language task via CLI
2. CLI loads environment variables and initializes the automation engine
3. Engine creates OpenAI gpt-4o-mini client and browser instance
4. browser-use Agent interprets task and executes browser actions
5. Real-time progress displayed to user
6. Results returned when task completes

## Usage Examples
```bash
# Simple search
python main.py "search for Python tutorials on Google"

# Web scraping
python main.py "scrape top 10 Hacker News posts with titles and URLs"

# Form automation
python main.py "fill out contact form with test data"

# Multi-step workflow
python main.py "compare iPhone prices on Amazon and Best Buy"
```

## Environment Variables
- `OPENAI_API_KEY` (required): OpenAI API key for gpt-4o-mini access

## User Preferences
- None specified yet

## Future Enhancements
- Structured output support with Pydantic models
- Task history and session management
- Configuration file for common tasks
- Interactive mode for multi-step workflows
- Video recording capability
