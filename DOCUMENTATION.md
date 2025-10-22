# AI Browser Automation CLI with Self-Healing Code Generation

## Overview

A powerful Python CLI tool that performs AI-powered browser automation and generates reusable Playwright code with automatic self-healing capabilities. Simply describe what you want to do in natural language, and the AI handles everything—including fixing broken locators in generated code.

**Key Features:**
1. **AI Browser Automation**: Run tasks using natural language with browser-use
2. **Self-Healing Code Generation**: Convert browser-use actions into reusable Playwright code with automatic locator healing
3. **Enhanced AI Fallback**: Two-level recovery system ensures automation never fails

---

## Features

### Core Capabilities
- **Natural Language Interface**: Describe tasks in plain English
- **Advanced Browser Automation**: Navigation, clicking, form filling, data extraction, multi-step workflows
- **AI-Powered**: Uses OpenAI gpt-4o-mini with browser-use for intelligent task execution

### Self-Healing Code Generation ⭐
- **Generate Reusable Code**: Convert automation into clean Playwright Python scripts
- **Multiple Locator Strategies**: Text, role, ID, label, CSS, XPath with automatic fallbacks
- **AI-Powered Self-Healing**: When locators fail in generated code, AI automatically finds elements and fixes locators **within the same browser session**
- **Production-Ready**: Generated code is maintainable, testable, and adapts to page changes

### Enhanced AI Fallback Execution ⭐⭐
- **Two-Level Recovery System**: Ensures automation never fails
- **Level 1 - Locator Healing**: AI finds new locators when elements move or change
- **Level 2 - AI Fallback**: If healed locators fail, browser-use AI steps in to execute the specific action
- **Same Browser Session**: No restarts, state preserved throughout recovery
- **Zero Manual Intervention**: Completely automated recovery process

**Important**: Self-healing applies only to **generated code execution**, not initial automation (which already uses AI natively).

---

## Prerequisites

- Python 3.11 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Replit environment (if running on Replit)

---

## Installation

### On Replit (Recommended)

The project is pre-configured for Replit. You only need to:

1. **Add your OpenAI API key**:
   - The system will automatically prompt you for the `OPENAI_API_KEY`
   - Get your API key from https://platform.openai.com/api-keys
   - Add it to Replit Secrets when prompted

2. **Dependencies are pre-installed**:
   - browser-use
   - langchain-openai
   - playwright
   - python-dotenv
   - openai

3. **Playwright browsers are pre-installed**:
   - Chromium is already configured and ready to use

### Manual Installation (Local)

If running locally:

1. Install dependencies:
```bash
pip install browser-use langchain-openai python-dotenv playwright openai
```

2. Install Playwright browser:
```bash
python -m playwright install chromium
```

3. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

---

## Usage

### Mode 1: Direct Browser Automation

Run tasks using natural language:

```bash
python main.py "search for Python tutorials on Google"
```

**Examples:**

**Web Scraping:**
```bash
python main.py "scrape the top 10 Hacker News posts with their titles and URLs"
```

**Form Automation:**
```bash
python main.py "go to example.com/contact and fill out the contact form with name: John Doe, email: john@example.com"
```

**Multi-step Workflows:**
```bash
python main.py "compare prices for iPhone 15 on Amazon and Best Buy"
```

**Data Collection:**
```bash
python main.py "find the top 5 Python automation libraries on GitHub and extract their star counts"
```

**Simple Tasks:**
```bash
python main.py "go to example.com and tell me the page title"
```

### Mode 2: Code Generation

Generate reusable Playwright code from your automation:

```bash
python main.py "go to example.com and click login" --generate-code
```

**With custom output file:**
```bash
python main.py "search for Python on Google" --generate-code --output search_google.py
```

**With verbose logging:**
```bash
python main.py "navigate to GitHub trending" --generate-code --verbose
```

### Mode 3: Self-Healing Execution

Execute generated code with automatic self-healing:

```bash
python main.py --execute-code generated_automation.py
```

**With verbose healing logs:**
```bash
python main.py --execute-code search_google.py --verbose
```

The self-healing will automatically:
- Detect when locators fail
- Use AI to find correct elements
- Generate new working locators
- Resume execution smoothly
- If healing fails, AI executes the action directly

### Complete Workflow Example

```bash
# Step 1: Record and generate code
python main.py "go to example.com, click login, fill email with test@email.com" \
  --generate-code --output login_flow.py --verbose

# Step 2: Execute with self-healing (even if page changes)
python main.py --execute-code login_flow.py --verbose
```

---

## Command Options

```bash
python main.py [OPTIONS] "task description"

Options:
  -h, --help              Show help message
  --headless              Run browser in headless mode (default: False)
  --no-headless           Show browser window
  --model MODEL           OpenAI model to use (default: gpt-4o-mini)
  --verbose               Show detailed logs
  --generate-code         Generate reusable Playwright Python code
  --output FILE           Output file for generated code (default: generated_automation.py)
  --execute-code FILE     Execute a previously generated automation script with self-healing
```

---

## How It Works

### Mode 1: Direct Browser Automation
1. User provides natural language task via CLI
2. browser-use Agent interprets and executes the task
3. Results returned to user

### Mode 2: Code Generation
1. User provides task with `--generate-code` flag
2. browser-use Agent performs the automation
3. Action history is captured and parsed
4. PlaywrightCodeGenerator converts actions to reusable Python code
5. Generated code includes multiple locator fallback strategies
6. Code saved to file for later execution

### Mode 3: Self-Healing Execution with AI Fallback
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

---

## Enhanced Self-Healing with AI Fallback

### Two-Level Recovery System

The self-healing executor features a **two-level recovery system** that ensures your automation scripts run successfully even when pages change dramatically.

### Level 1: Locator Healing

When a locator fails (e.g., button moved, ID changed):
1. AI analyzes the current page
2. Finds the element using smart heuristics
3. Generates a new working locator
4. Caches it for future use
5. ✅ Continues execution with the new locator

### Level 2: AI Fallback Execution

If the healed locator also fails (e.g., element structure completely changed):
1. 🤖 browser-use AI steps into the **same browser session**
2. AI executes **just that one specific action** (click, fill, etc.)
3. AI reports success and **gracefully exits**
4. Your automation script **continues** with the next steps
5. ✅ Zero manual intervention needed

### Example Scenario

Imagine your script has these steps:
```python
1. Go to example.com
2. Click login button       ← Locator fails!
3. Fill email field
4. Click submit
```

**Without AI Fallback:**
```
Step 1: ✅ Success
Step 2: ⚠️  Locator failed
        🔧 Healing attempt...
        ❌ Healed locator also failed
        ❌ SCRIPT FAILS - Manual fix required
```

**With AI Fallback (Enhanced):**
```
Step 1: ✅ Success
Step 2: ⚠️  Locator failed
        🔧 Healing attempt...
        ❌ Healed locator also failed
        🤖 browser-use AI stepping in...
        ✅ AI clicked the login button
        🔄 Continuing with automation script...
Step 3: ✅ Success (fills email field)
Step 4: ✅ Success (clicks submit)
        ✅ AUTOMATION COMPLETED
```

### Verbose Output Example

When running with `--verbose`, you'll see:

```bash
$ python main.py --execute-code login_automation.py --verbose

🚀 Starting execution with self-healing enabled
   Max healing attempts per locator: 3

   # Step 1: Navigate to page
   ✓ page.goto("https://example.com")

   # Step 2: Click login button
   ⚠️  Locator failed: page.get_by_text("Login")
      Error: Timeout 10000ms exceeded

🔧 Healing attempt 1/3
   Failed locator: page.get_by_text("Login")
   Action: click login button
   🤖 AI analyzing page to find element...
   🔗 Connecting to browser session: ws://127.0.0.1:...
   ✅ Healing successful! New locator: page.get_by_role("button", name="Sign In")

   # Trying healed locator...
   ❌ Healed locator also failed: Timeout 10000ms exceeded

🤖 Healed locator failed - browser-use AI stepping in to execute action...
   Action: click login button
   🤖 AI executing action in current browser session...
   ✅ AI successfully executed the action!
   🔄 Continuing with automation script...

   # Step 3: Fill email field
   ✓ Locator found immediately

   # Step 4: Click submit
   ✓ Locator found immediately

✅ Execution completed successfully!
   Healed 1 locator(s) during execution
```

### Key Benefits

1. **Zero Manual Intervention**: Scripts fix themselves completely
2. **Handles Severe Changes**: Even if page structure changes dramatically
3. **Same Browser Session**: No restart, state preserved
4. **Surgical Precision**: AI executes only the failed action, nothing more
5. **Graceful Handoff**: Control returns smoothly to your script

### When Is This Useful?

- **Website Redesigns**: Complete UI changes that break all locators
- **A/B Testing**: Site shows different versions to different users
- **Dynamic Content**: Elements that change frequently
- **Flaky Locators**: Selectors that work inconsistently
- **Complex Pages**: Modern SPAs with unpredictable DOM structures

---

## Technology Stack

- **Python 3.11+**: Modern Python features
- **browser-use (0.5.9+)**: AI-powered browser automation framework
- **OpenAI gpt-4o-mini**: Natural language understanding (newest model, released August 7, 2025)
- **Playwright**: Browser automation backend for generated code execution
- **langchain-openai**: OpenAI integration for LangChain
- **python-dotenv**: Environment variable management

---

## Project Architecture

### Main Components

1. **main.py** - CLI entry point with three modes: automation, code generation, and self-healing execution
2. **automation_engine.py** - Core automation logic with browser-use and code generation support
3. **playwright_code_generator.py** - Converts browser-use action history to Playwright code
4. **self_healing_executor.py** - Executes generated code with AI-powered locator healing
5. **locator_utils.py** - Helper utilities for robust locator strategies
6. **test_workflow.py** - Test script for the complete workflow

### Generated Code Features

Generated code includes:

1. **Multiple Locator Strategies**:
   - Text-based locators (exact and partial match)
   - Role-based locators (ARIA roles)
   - Label-based locators
   - ID and test-ID locators
   - CSS and XPath selectors

2. **Self-Healing Integration**:
   - Automatic locator healing when elements change
   - AI fallback execution for severe changes
   - Locator caching for performance
   - Same browser session continuity

3. **Clean, Maintainable Code**:
   - Async/await Playwright syntax
   - Proper error handling
   - Type hints
   - Descriptive variable names

---

## Troubleshooting

### Error: Missing OPENAI_API_KEY
- Make sure you've added your OpenAI API key to Replit Secrets
- On local machines, ensure the environment variable is set

### Browser fails to start
- On Replit: The browser is pre-configured and should work automatically
- On local machines: Check that Chromium is properly installed with `python -m playwright install chromium`
- Try running with `--no-headless` to see what's happening

### Locators keep failing even with self-healing
- Enable `--verbose` mode to see detailed healing logs
- Check if the element exists on the page
- Verify the action description is clear and accurate
- Ensure your OpenAI API key is valid and has credits

### API key rejected (401 error)
- Double-check your OpenAI API key is correct
- Verify the key starts with "sk-proj-" or "sk-"
- Ensure the key has not been revoked
- Check your OpenAI account has available credits

---

## Environment Variables

- `OPENAI_API_KEY` (required): OpenAI API key for gpt-4o-mini access
- `CHROMIUM_PATH` (optional): Custom path to Chromium browser (auto-detected on Replit)

---

## Best Practices

1. **Use descriptive action descriptions**: "click login button" is better than "click element"
2. **Enable verbose mode during development**: See exactly what's happening with `--verbose`
3. **Monitor healing frequency**: If AI fallback triggers often, consider updating locators
4. **Keep API key secure**: Store in environment variables, never in code
5. **Test generated code**: Run with `--execute-code` to verify it works before deploying
6. **Use meaningful output filenames**: Name generated scripts descriptively (e.g., `login_flow.py`, `checkout_process.py`)

---

## Limitations

- Requires active OpenAI API key with available credits
- AI execution takes slightly longer than direct locators (a few seconds)
- Self-healing applies only to generated code execution, not initial automation
- Limited to actions browser-use AI can understand (click, fill, navigate, extract, etc.)
- Requires `action_description` parameter for AI fallback to work effectively

---

## Recent Updates

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

### October 22, 2025 - Initial Setup
- Initial project setup on Replit
- Installed dependencies: browser-use, langchain-openai, python-dotenv, playwright
- Installed Chromium browser
- Created core CLI application (main.py)
- Implemented browser automation engine (automation_engine.py)

---

## Future Enhancements

- Export to Playwright Codegen format
- Video recording of healing process
- Locator confidence scoring
- Multi-language code generation (TypeScript, Java, C#)
- Configuration file for healing strategies
- Session replay and debugging tools
- Integration with CI/CD pipelines
- Support for more browsers (Firefox, WebKit)

---

## License

MIT License

---

## Support

For issues, questions, or contributions:
- Check the troubleshooting section above
- Review the verbose logs with `--verbose` flag
- Ensure your OpenAI API key is valid and has credits
- Verify all dependencies are properly installed

---

**Built with ❤️ using OpenAI, browser-use, and Playwright**
