# 🎮 Interactive Browser Automation Mode

An intuitive, powerful REPL interface for controlling browser automation with natural language.

## Features

- 🎯 **Natural Language Commands** - Just describe what you want in plain English
- 📊 **Real-time Metrics** - See cache hits, response times, and performance stats
- 📜 **Command History** - Track and review all your automation steps
- 🎨 **Rich UI** - Beautiful terminal interface with progress indicators
- ⚡ **All Enhanced Features** - Full access to caching, parallel execution, GPT-4o vision

## Quick Start

### Basic Usage

```bash
python interactive.py
```

### With GPT-4o (Maximum Intelligence)

```bash
python interactive.py --gpt4o
```

### Show Browser Window

```bash
python interactive.py --visible
```

### All Options

```bash
python interactive.py --gpt4o --visible
```

## Available Commands

Once in interactive mode:

### Natural Language Commands

Just type what you want to do:

```
🤖 go to google.com
🤖 click the search button
🤖 fill the email field with test@example.com
🤖 take a screenshot
🤖 get all links from the page
```

### Quick Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `help` | `h` | Show help menu |
| `metrics` | `m` | Display performance metrics |
| `history` | | Show command history |
| `clear` | `cls` | Clear the screen |
| `quit` | `exit`, `q` | Exit interactive mode |

## Example Session

```
╔═══════════════════════════════════════════════════════════╗
║   🚀 ULTRA-ENHANCED BROWSER AUTOMATION - INTERACTIVE MODE  ║
║                                                           ║
║   ⚡ Intelligent Caching    🧠 GPT-4o Vision             ║
║   🔄 Parallel Execution     🔍 Semantic Matching          ║
║   🔮 Predictive Loading     📊 Real-time Metrics          ║
╚═══════════════════════════════════════════════════════════╝

Configuration:
  • AI Model: GPT-4o (Max Intelligence)
  • Vision: Enabled
  • Caching: Enabled
  • Parallel: Enabled
  • Max Retries: 5

Type 'help' for commands, or just describe what you want to do!

🤖 navigate to github.com

⚡ Executing: navigate to github.com...
✓ Status: success

📋 Result
✓ browser_navigate: Navigation successful

⏱️  Execution time: 2.34s | Cache hit rate: 0.0%

🤖 click the sign in button

⚡ Executing: click the sign in button...
🔍 First retry - activating GPT-4o Vision for intelligent element detection...
✨ Vision suggests: a.btn-primary
✓ Status: success

📋 Result
✓ browser_click: Click successful

⏱️  Execution time: 3.12s | Cache hit rate: 33.3% | 🧠 Vision calls: 1

🤖 metrics

📊 Performance Metrics
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Metric              ┃     Value ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Total Commands      │         2 │
│ Cache Hit Rate      │     33.3% │
│ Cache Hits          │         2 │
│ Cache Misses        │         4 │
│ Vision API Calls    │         1 │
│ Total Retries       │         1 │
│ Avg Response Time   │     2.73s │
│ Session Duration    │  0:01:23  │
└─────────────────────┴───────────┘

Cache Efficiency: ✅ Good
```

## Pro Tips

### Chain Multiple Actions

```
🤖 navigate to amazon.com, search for laptop, and click the first result
```

### Extract Data

```
🤖 get all product titles from this page
🤖 extract all email addresses
🤖 find all links to PDF files
```

### Smart Element Detection

The system uses:
- Text matching: "click the login button"
- Fuzzy matching: "click the log in btn" (will find "Login Button")
- Vision AI: Sees the page like you do and finds elements visually
- Semantic search: Understands intent, not just exact words

### Performance Optimization

- **First run**: May be slower as cache builds
- **Subsequent runs**: 30-300% faster with intelligent caching
- **Vision calls**: Only used on first retry for maximum speed
- **Parallel execution**: Multiple operations run simultaneously

## Command Line Options

```bash
python interactive.py [options]

Options:
  --gpt4o, -4          Use GPT-4o for maximum intelligence
  --no-vision          Disable vision-based element detection
  --visible, -v        Show browser window (non-headless)
  --help, -h           Show help message
```

## Environment Variables

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=sk-...
```

Or you'll be prompted to enter it when starting interactive mode.

## Integration with Other Scripts

You can also use the interactive mode programmatically:

```python
from src.automation.interactive_mode import start_interactive_mode
import asyncio

async def main():
    await start_interactive_mode(
        api_key="your-api-key",
        use_gpt4o=True,
        enable_vision=True,
        headless=True
    )

asyncio.run(main())
```

## Troubleshooting

### Browser doesn't start

Make sure Playwright browsers are installed:
```bash
playwright install
```

### OpenAI API errors

Check your API key is set correctly:
```bash
echo $OPENAI_API_KEY
```

### Commands not executing

- Use the `metrics` command to check status
- Review `history` to see what went wrong
- Try simpler commands first
- Enable `--visible` mode to see what's happening

## Performance Metrics Explained

- **Cache Hit Rate**: % of operations served from cache (higher = faster)
- **Vision API Calls**: How many times GPT-4 Vision was used for element detection
- **Total Retries**: Number of automatic retry attempts (system handles these)
- **Avg Response Time**: Average time per command (improves with caching)

## What Makes This Fast?

1. **Intelligent Caching**: Page context, elements, and screenshots cached with smart TTL
2. **Parallel Execution**: Independent operations run simultaneously
3. **Predictive Pre-loading**: System fetches likely-needed data in advance
4. **Semantic Matching**: Finds elements faster with fuzzy search
5. **Adaptive Retries**: Only uses expensive vision when needed

## What Makes This Intelligent?

1. **GPT-4o Brain**: Superior reasoning for complex tasks (when enabled)
2. **Vision AI**: Sees the page like a human, finds elements visually
3. **Session Memory**: Learns from successful patterns
4. **Multi-step Planning**: Breaks complex tasks into steps automatically
5. **Fuzzy Matching**: Understands intent, not just exact text

Enjoy your interactive automation! 🚀
