# Local Browser Automation

A **privacy-focused, local-only AI browser automation tool** built from the browser-use library. All processing runs on your machine with no telemetry or external data sharing.

## Overview

This tool enables you to automate browser tasks using AI, running entirely locally on your machine:
- ✅ **100% Local Execution** - Browser automation runs on your computer
- ✅ **No Telemetry** - Zero data collection or external analytics
- ✅ **Privacy First** - No cloud dependencies for browser control
- ✅ **Multiple LLM Support** - Works with OpenAI, Anthropic, Google, or local Ollama models

## Quick Start

### 1. Choose Your LLM Provider

The tool supports multiple AI model providers:
- **OpenAI** (GPT-4, GPT-3.5-turbo) - Requires API key
- **Anthropic** (Claude) - Requires API key
- **Google** (Gemini) - Requires API key
- **Ollama** (Local) - Runs completely offline, no API key needed

### 2. Set Up API Keys (if using cloud LLMs)

Add your API key through the Streamlit interface sidebar or as an environment variable:

```bash
# For OpenAI
export OPENAI_API_KEY="your-key-here"

# For Anthropic
export ANTHROPIC_API_KEY="your-key-here"

# For Google
export GOOGLE_API_KEY="your-key-here"
```

Or add them through Replit Secrets for security.

### 3. Run the App

The app is already running at port 5000. Just enter a task and click "Run Task"!

## Privacy & Security

### What Data Leaves Your Machine?
**Only API calls to your chosen LLM provider** (OpenAI, Anthropic, Google, etc.) for AI inference. If you use Ollama (local), nothing leaves your machine.

### What's Been Removed?
- ❌ PostHog telemetry
- ❌ Browser-Use Cloud branding
- ❌ Cloud browser dependencies
- ❌ Analytics tracking
- ❌ External data sync

### What Stays Local?
- ✅ Browser automation engine
- ✅ Web page data and screenshots
- ✅ Task results and history
- ✅ Browser session data
- ✅ All file operations

## Example Tasks

Try these example tasks:

```
Search Google for the latest AI news and summarize the top 3 results
```

```
Go to example.com and extract the page title and main heading
```

```
Find the number of GitHub stars for popular open-source AI projects
```

```
Navigate to a news website and get today's top headlines
```

## Technical Details

### Architecture
- **Python 3.12** - Runtime environment
- **Streamlit** - Web interface
- **Playwright** - Browser automation (Chromium)
- **uv** - Fast Python package manager
- **LangChain-compatible** - Works with various LLM providers

### Browser Configuration
- **Local Chromium**: Installed via Playwright
- **Headless Mode**: Optional (run browser in background)
- **User Data**: Stored in `~/.cache/browseruse/`
- **Extensions**: Supported (stored in `~/.config/browseruse/extensions/`)

### File Locations
- **Config**: `~/.config/browseruse/config.json`
- **Profiles**: `~/.config/browseruse/profiles/`
- **Cache**: `~/.cache/ms-playwright/chromium-*/`

## Testing

Run the verification test to confirm local-only operation:

```bash
uv run python test_local.py
```

This test verifies:
1. ✅ Telemetry is disabled
2. ✅ PostHog client is not initialized
3. ✅ Local browser starts successfully
4. ✅ Agent can run tasks (if API key provided)

## Advanced Usage

### Using Ollama (Completely Local)

For 100% offline operation, use Ollama with local models:

1. Install Ollama: https://ollama.ai
2. Download a model: `ollama pull llama3.2`
3. Select "Ollama (Local)" in the Streamlit sidebar
4. No API key needed!

### Command Line Usage

You can also use the library programmatically:

```python
import asyncio
from browser_use import Agent, Browser, ChatOpenAI

async def main():
    browser = Browser(headless=True)
    agent = Agent(
        task="Your task here",
        llm=ChatOpenAI(model="gpt-4"),
        browser=browser,
    )
    result = await agent.run()
    print(result.final_result())

asyncio.run(main())
```

### Custom Browser Profiles

Create custom browser profiles in `~/.config/browseruse/profiles/`:
- Separate cookies and session data
- Different browser settings
- Isolated automation contexts

## Deployment

This app is configured for **autoscale deployment** on Replit:
- Runs on-demand when accessed
- Automatically scales with traffic
- Cost-effective for intermittent use

## Troubleshooting

### Browser Won't Start
- Check if Chromium is installed: `ls ~/.cache/ms-playwright/`
- Reinstall: `uv run playwright install chromium`

### API Key Issues
- Verify key is correct and has credits
- Check environment variable is set
- Try re-entering in the Streamlit sidebar

### Import Errors
- Run: `uv sync` to reinstall dependencies
- Restart the Streamlit workflow

## Development

### Project Structure
```
.
├── app.py                      # Main Streamlit application
├── test_local.py              # Verification test script
├── browser_use/               # Core automation library
│   ├── agent/                 # AI agent logic
│   ├── browser/               # Browser control
│   ├── telemetry/            # (Disabled) Telemetry code
│   ├── llm/                  # LLM integrations
│   └── config.py             # Configuration
├── examples/                  # Example scripts
└── replit.md                 # This file
```

### Recent Changes

**2025-10-24**: Privacy-focused local-only transformation
- ✅ Permanently disabled telemetry (modified `browser_use/telemetry/service.py`)
- ✅ Removed PostHog analytics
- ✅ Removed Browser-Use Cloud branding
- ✅ Configured for local-only execution
- ✅ Updated Streamlit UI with privacy focus
- ✅ Added verification test script
- ✅ Chromium browser ready for local automation

## Resources

- **Original Project**: https://github.com/browser-use/browser-use
- **Playwright Docs**: https://playwright.dev
- **Streamlit Docs**: https://docs.streamlit.io

---

**Built with privacy in mind. Your data stays on your machine.** 🔒
