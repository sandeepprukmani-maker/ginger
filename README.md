# AI Browser Automation CLI

A powerful Python CLI tool that performs OpenAI-powered browser automation with comprehensive basic and advanced capabilities. Simply describe what you want to do in natural language, and let AI handle the browser automation for you.

## Features

- **Natural Language Interface**: Describe tasks in plain English
- **Advanced Browser Automation**: Navigation, clicking, form filling, data extraction, multi-step workflows
- **AI-Powered**: Uses OpenAI gpt-4o-mini with browser-use for intelligent task execution
- **Complex Task Support**: Web scraping, multi-page workflows, data collection across sites
- **Real-time Progress**: See what the AI is doing as it automates your task

## Prerequisites

- Python 3.11 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation

1. Install dependencies:
```bash
pip install browser-use langchain-openai python-dotenv
```

2. Install Playwright browser (if not using system Chromium):
```bash
playwright install chromium
```

3. Set up your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

**Note:** The tool will automatically detect system Chromium/Chrome. If you need to specify a custom path, set `CHROMIUM_PATH` in your `.env` file.

## Usage

### Basic Usage

Run a task with natural language:

```bash
python main.py "search for Python tutorials on Google"
```

### Advanced Examples

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

### Command Options

```bash
python main.py [OPTIONS] "task description"

Options:
  -h, --help        Show help message
  --headless        Run browser in headless mode (default: True)
  --no-headless     Show browser window
  --model MODEL     OpenAI model to use (default: gpt-4o-mini)
  --verbose         Show detailed logs
```

## Examples

### Example 1: Simple Search
```bash
python main.py "search Google for 'best Python IDE'"
```

### Example 2: Extract Information
```bash
python main.py "go to news.ycombinator.com and get the title of the top story"
```

### Example 3: Multi-step Task
```bash
python main.py "search for 'Replit' on Google, click the first result, and tell me the page title"
```

## How It Works

1. You provide a natural language task description
2. The CLI initializes the browser automation agent with OpenAI
3. The AI agent interprets your task and executes the necessary browser actions
4. You see real-time progress as the agent works
5. The agent returns the results when complete

## Troubleshooting

**Error: Missing OPENAI_API_KEY**
- Make sure you've created a `.env` file with your OpenAI API key

**Browser fails to start**
- Check that Chromium is properly installed
- Try running with `--no-headless` to see what's happening

## Advanced Usage

The tool uses the browser-use library which provides:
- Automatic page navigation
- Intelligent element detection
- Form filling
- Data extraction
- Multi-page workflows
- Dynamic content handling

## Technology Stack

- **browser-use**: AI-powered browser automation
- **OpenAI gpt-4o-mini**: Natural language understanding
- **Playwright**: Browser automation backend
- **Python 3.11+**: Modern Python features

## License

MIT License
