# Windows Setup Guide - Playwright MCP Browser Automation

Complete guide for setting up and running the Playwright MCP browser automation on Windows.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Running the Project](#running-the-project)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Install Node.js (Required)

The MCP server requires Node.js 18 or newer.

**Download and Install:**
1. Visit https://nodejs.org/
2. Download the **LTS version** (recommended) for Windows
3. Run the installer (`.msi` file)
4. Follow the installation wizard - keep all default settings
5. Verify installation:
   ```cmd
   node --version
   npm --version
   ```
   You should see version numbers (e.g., `v20.x.x` and `10.x.x`)

### 2. Install Python (Required)

The automation script requires Python 3.11 or newer.

**Download and Install:**
1. Visit https://www.python.org/downloads/
2. Download **Python 3.11** or newer for Windows
3. Run the installer
4. **IMPORTANT**: Check "Add Python to PATH" during installation
5. Verify installation:
   ```cmd
   python --version
   pip --version
   ```
   You should see version numbers

### 3. Install Git (Optional, for cloning)

**Download and Install:**
1. Visit https://git-scm.com/download/win
2. Download Git for Windows
3. Run the installer - keep default settings
4. Verify installation:
   ```cmd
   git --version
   ```

---

## Installation Steps

### Step 1: Get the Project Files

**Option A: Clone from GitHub (if available)**
```cmd
cd C:\Users\YourUsername\Documents
git clone https://github.com/microsoft/playwright-mcp.git
cd playwright-mcp
```

**Option B: Download ZIP**
1. Download the project as a ZIP file
2. Extract to a folder (e.g., `C:\Users\YourUsername\Documents\playwright-mcp`)
3. Open Command Prompt or PowerShell
4. Navigate to the folder:
   ```cmd
   cd C:\Users\YourUsername\Documents\playwright-mcp
   ```

### Step 2: Install Node.js Dependencies

```cmd
npm install
```

This will install all required packages including Playwright.

### Step 3: Install Python Dependencies

```cmd
pip install httpx openai mcp
```

Or if you have the `pyproject.toml` file:
```cmd
pip install -e .
```

### Step 4: Install Playwright Browsers

```cmd
npx playwright install chromium
```

This downloads the Chromium browser for automation.

---

## Configuration

### Set Up OpenAI API Key

The automation script requires an OpenAI API key.

#### Get Your API Key:
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create new secret key**
5. Copy the key (starts with `sk-`)

#### Set the API Key on Windows:

**Option A: Environment Variable (Persistent)**

1. Press `Windows + R`, type `sysdm.cpl`, press Enter
2. Go to **Advanced** tab → Click **Environment Variables**
3. Under **User variables**, click **New**
4. Variable name: `OPENAI_API_KEY`
5. Variable value: Paste your API key
6. Click **OK** on all windows
7. **Restart Command Prompt** for changes to take effect

**Option B: Command Prompt (Temporary - Current Session Only)**
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

**Option C: PowerShell (Temporary - Current Session Only)**
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

**Option D: Create .env File**
1. Create a file named `.env` in the project folder
2. Add this line:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

---

## Running the Project

### Step 1: Start the MCP Server

Open a **new Command Prompt** window:

```cmd
cd C:\Users\YourUsername\Documents\playwright-mcp
node cli.js --port 8080 --browser chromium
```

**What you should see:**
```
Listening on http://localhost:8080
Put this in your client config:
{
  "mcpServers": {
    "playwright": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

**Keep this window open** - the server needs to stay running.

### Step 2: Run Browser Automation

Open a **second Command Prompt** window:

**Command Line Mode:**
```cmd
cd C:\Users\YourUsername\Documents\playwright-mcp
python browser_automation.py "Go to google.com and search for Python"
```

**Interactive Mode:**
```cmd
python browser_automation.py
```
Then enter your prompt when asked.

---

## Usage Examples

### Example 1: Simple Navigation
```cmd
python browser_automation.py "Navigate to github.com"
```

### Example 2: Search on Google
```cmd
python browser_automation.py "Go to google.com and search for 'Playwright automation'"
```

### Example 3: Form Filling
```cmd
python browser_automation.py "Go to example.com/login, fill username with test@example.com and password with password123"
```

### Example 4: Complex Workflow
```cmd
python browser_automation.py "Navigate to github.com, click search, type 'playwright', and click the first result"
```

### Example 5: Multi-step Automation
```cmd
python browser_automation.py "Go to amazon.com, search for 'laptop', click on the first result, and take a screenshot"
```

---

## Output Files

The script generates:

1. **Console Output** - Shows real-time execution
2. **automation_script.py** - Rerunnable Python script in your current directory

You can run the generated script:
```cmd
python automation_script.py
```

---

## Troubleshooting

### Issue 1: "node is not recognized"

**Solution:** Node.js is not in PATH
1. Reinstall Node.js and ensure "Add to PATH" is checked
2. Or manually add to PATH:
   - Default location: `C:\Program Files\nodejs\`
   - Add to System PATH environment variable

### Issue 2: "python is not recognized"

**Solution:** Python is not in PATH
1. Reinstall Python and check "Add Python to PATH"
2. Or find Python location (usually `C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\`)
3. Add to System PATH environment variable

### Issue 3: "OPENAI_API_KEY not set"

**Solution:** API key not configured
```cmd
set OPENAI_API_KEY=sk-your-actual-key-here
python browser_automation.py "your prompt"
```

Or set it permanently in Environment Variables (see Configuration section).

### Issue 4: "Connection refused to localhost:8080"

**Solution:** MCP server is not running
1. Open a separate Command Prompt
2. Navigate to project folder
3. Run: `node cli.js --port 8080 --browser chromium`
4. Keep that window open
5. Run your Python script in a different window

### Issue 5: "Module not found" errors

**Solution:** Dependencies not installed

For Node.js packages:
```cmd
npm install
npx playwright install chromium
```

For Python packages:
```cmd
pip install httpx openai mcp
```

### Issue 6: Browser fails to launch

**Solution:** Install Playwright browsers
```cmd
npx playwright install chromium
```

If that doesn't work, try:
```cmd
npx playwright install-deps chromium
```

### Issue 7: Permission Denied errors

**Solution:** Run Command Prompt as Administrator
1. Press Windows key
2. Type "cmd"
3. Right-click "Command Prompt"
4. Select "Run as administrator"

### Issue 8: Firewall Blocking

**Solution:** Allow Node.js through Windows Firewall
1. Windows Security → Firewall & network protection
2. Allow an app through firewall
3. Find Node.js and check both Private and Public

---

## Running in Headless Mode (No Browser Window)

If you don't want to see the browser window:

```cmd
node cli.js --port 8080 --browser chromium --headless
```

---

## Advanced Configuration

### Change Server Port

```cmd
node cli.js --port 9000 --browser chromium
```

Then update `browser_automation.py` line 24:
```python
MCP_SERVER_URL = "http://localhost:9000/mcp"
```

### Use Different Browser

**Firefox:**
```cmd
node cli.js --port 8080 --browser firefox
npx playwright install firefox
```

**WebKit (Safari engine):**
```cmd
node cli.js --port 8080 --browser webkit
npx playwright install webkit
```

### Save Session State

```cmd
node cli.js --port 8080 --browser chromium --user-data-dir "C:\Users\YourUsername\playwright-profile"
```

This saves cookies and login sessions between runs.

---

## Running as Background Service (Optional)

### Using Windows Task Scheduler

1. Create a batch file `start_mcp_server.bat`:
   ```batch
   @echo off
   cd C:\Users\YourUsername\Documents\playwright-mcp
   node cli.js --port 8080 --browser chromium --headless
   ```

2. Open Task Scheduler
3. Create Basic Task
4. Set trigger (e.g., "When I log on")
5. Action: Start a program
6. Program: `C:\Users\YourUsername\Documents\playwright-mcp\start_mcp_server.bat`

---

## Quick Start Checklist

- [ ] Install Node.js 18+ from nodejs.org
- [ ] Install Python 3.11+ from python.org
- [ ] Clone or download project files
- [ ] Run `npm install` in project directory
- [ ] Run `pip install httpx openai mcp`
- [ ] Run `npx playwright install chromium`
- [ ] Get OpenAI API key from platform.openai.com
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Start MCP server: `node cli.js --port 8080 --browser chromium`
- [ ] Run automation: `python browser_automation.py "your prompt"`

---

## Need Help?

### Verify Your Setup

Run these commands to check everything:

```cmd
node --version
npm --version
python --version
pip --version
echo %OPENAI_API_KEY%
```

All should return version numbers (last one should show your API key).

### Test the Server

```cmd
node cli.js --port 8080 --browser chromium
```

Should show: "Listening on http://localhost:8080"

### Test Python Script

```cmd
python browser_automation.py "Navigate to example.com"
```

Should connect and perform the automation.

---

## Additional Resources

- Node.js Documentation: https://nodejs.org/docs
- Python Documentation: https://docs.python.org/
- Playwright Documentation: https://playwright.dev
- OpenAI API Documentation: https://platform.openai.com/docs

---

**Last Updated:** October 16, 2025

For more details on the Python automation features, see `PYTHON_USAGE.md`.
