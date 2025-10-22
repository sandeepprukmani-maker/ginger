# AI Browser Automation CLI

> **A powerful Python CLI tool for AI-powered browser automation with self-healing code generation**

## Quick Start

```bash
# Basic automation
python main.py "go to example.com and tell me the page title"

# Generate reusable code
python main.py "fill out login form" --generate-code --output login.py

# Execute with self-healing
python main.py --execute-code login.py --verbose
```

## Features

✨ **Natural Language Interface** - Describe tasks in plain English  
🤖 **AI-Powered Automation** - Uses OpenAI GPT-4o-mini and browser-use  
🔧 **Self-Healing Code** - Automatically fixes broken locators  
🚀 **Production Ready** - Generate maintainable Playwright scripts  

## Documentation

📚 **[Complete Documentation](DOCUMENTATION.md)** - Installation, usage, examples, and troubleshooting

## Project Structure

```
ai-browser-automation/
├── src/                    # Core modules
│   ├── automation_engine.py
│   ├── playwright_code_generator.py
│   ├── self_healing_executor.py
│   └── locator_utils.py
├── examples/              # Example scripts
├── main.py               # CLI entry point
├── DOCUMENTATION.md      # Full documentation
└── .env.example         # Environment template
```

## Prerequisites

- Python 3.11+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Technology Stack

- **browser-use** - AI browser automation
- **OpenAI gpt-4o-mini** - Natural language understanding
- **Playwright** - Browser automation backend
- **Python 3.11+** - Modern Python features

## License

MIT License

---

**Built with ❤️ using OpenAI, browser-use, and Playwright**
