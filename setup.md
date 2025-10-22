# NL2Playwright Setup Guide

## Prerequisites

- Python 3.11 or higher
- pip or uv package manager

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd nl2playwright
```

### 2. Install Dependencies

#### Using pip:
```bash
pip install -r requirements.txt
```

#### Using uv (recommended):
```bash
uv sync --no-install-project
```

### 3. Install Playwright Browser

```bash
playwright install chromium
```

### 4. Configure Environment Variables

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` and add one of the following API keys:

```bash
# Choose one:
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GEMINI_API_KEY=your-gemini-key-here
BROWSER_USE_API_KEY=your-browser-use-cloud-key-here
```

**How to get API keys:**
- **OpenAI**: Sign up at https://platform.openai.com/ and create an API key
- **Anthropic**: Sign up at https://console.anthropic.com/ and create an API key
- **Google Gemini**: Sign up at https://ai.google.dev/ and create an API key
- **Browser Use**: Sign up at https://browser-use.com/ for their cloud LLM

## Running the Application

Start the CLI application:

```bash
python main.py
```

## Usage

Once the application starts:

1. You'll see a welcome banner
2. Enter your natural language task when prompted
3. The AI agent will execute the task in a browser
4. A Playwright script will be generated and saved to `generated_scripts/`

### Example Tasks

```
> go to google.com and search for cute dogs
> navigate to github.com, click on sign in
> go to example.com and take a screenshot
> open amazon.com, search for "laptop", and click the first result
```

## Configuration Options

You can customize the behavior by editing `.env`:

```bash
# Run browser in headless mode (no visible window)
HEADLESS=true

# Change output directory for generated scripts
OUTPUT_DIR=my_scripts

# Slow down browser actions (milliseconds)
SLOW_MO=500
```

## Troubleshooting

### Import errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.11+)

### Playwright browser not found
- Run: `playwright install chromium`

### No API key found error
- Ensure you've created a `.env` file
- Verify you've added at least one valid API key
- Check that the key is not wrapped in quotes in the `.env` file

## Output

Generated Playwright scripts are saved to the `generated_scripts/` directory with timestamps. You can run them directly:

```bash
python generated_scripts/your_script_20241022_123456.py
```

## Support

For issues and questions, please check the README.md or open an issue on the repository.
