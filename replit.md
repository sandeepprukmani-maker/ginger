# NL2Playwright - Natural Language to Playwright Converter

## Project Overview

NL2Playwright is a CLI application that converts natural language commands into executable Playwright scripts using browser-use AI agent. The tool allows users to describe web automation tasks in plain English and automatically generates ready-to-use Playwright code.

**Last Updated:** October 22, 2025

## Project Structure

```
.
├── main.py                  # Main entry point and CLI interface
├── converter.py             # Core converter logic using browser-use agent
├── action_capture.py        # Captures and converts browser actions to Playwright
├── playwright_generator.py  # Generates Playwright script code
├── example.py               # Example usage
├── pyproject.toml          # Python project configuration
├── requirements.txt        # Python dependencies list
├── setup.md                # Installation and setup instructions
├── .env                     # Environment variables (not tracked in git)
├── .env.example            # Example environment file
└── generated_scripts/      # Output directory for generated scripts
```

## Key Features

- 🤖 Natural language input (e.g., "go to google.com, search for dogs, click first link")
- 🎯 Generates Playwright-specific locators and actions
- 🔄 Supports multi-page navigation
- 📑 Handles multi-tab scenarios
- ⚠️ Alert handling
- 📝 Exports ready-to-use Playwright scripts

## How It Works

1. User enters a natural language task description
2. Browser-use AI agent executes the task in a real browser
3. Actions are captured and converted to Playwright selectors
4. A complete Playwright script is generated
5. Script is saved to `generated_scripts/` directory

## Dependencies

- **browser-use** (>=0.8.0): AI agent for browser automation
- **playwright** (>=1.48.0): Browser automation framework
- **python-dotenv** (>=1.0.0): Environment variable management
- **rich** (>=13.0.0): Terminal formatting and UI

## Configuration

### Environment Variables

The application requires one of the following LLM API keys (set in `.env` file):

- `OPENAI_API_KEY` - For OpenAI GPT models
- `ANTHROPIC_API_KEY` - For Anthropic Claude models
- `GEMINI_API_KEY` - For Google Gemini models
- `BROWSER_USE_API_KEY` - For Browser Use Cloud LLM

Optional settings:
- `HEADLESS=false` - Run browser in visible mode (default: false)
- `OUTPUT_DIR=generated_scripts` - Output directory for scripts

### Workflow

The project has a single workflow:
- **NL2Playwright CLI**: Runs `python main.py` to start the interactive CLI

## Usage

1. Ensure you have an API key set in the `.env` file (or as a Replit secret)
2. Run the workflow to start the CLI
3. Enter your natural language task when prompted
4. The generated Playwright script will be saved to `generated_scripts/`

Example tasks:
- "go to google.com and search for cute dogs"
- "navigate to github.com, click on sign in, and fill the username field"
- "go to example.com and take a screenshot"

## Recent Changes

- **October 22, 2025**: Initial setup in Replit environment
  - Installed Python 3.11 and all dependencies
  - Configured uv package manager
  - Installed Playwright Chromium browser
  - Set up workflow for CLI execution
  - Created .env file from .env.example
  - Added requirements.txt for pip-based installations
  - Created setup.md with detailed installation instructions

## Notes

- The application runs in console mode (no web interface)
- Browser runs in visible mode by default for better debugging
- Generated scripts are saved with timestamps to avoid conflicts
- The tool uses browser-use AI agent which requires LLM API access
