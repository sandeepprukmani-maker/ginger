# Setup Guide - AI Browser Automation Agent

## Complete setup instructions for running this project on Windows

---

## Prerequisites

Before you begin, ensure you have the following installed on your Windows machine:

### 1. Python 3.11 or higher
- Download from: https://www.python.org/downloads/
- During installation, **check the box "Add Python to PATH"**
- Verify installation:
  ```cmd
  python --version
  ```

### 2. Node.js 18 or higher
- Download from: https://nodejs.org/
- Use the LTS (Long Term Support) version
- Verify installation:
  ```cmd
  node --version
  npm --version
  ```

### 3. Git (optional, for cloning)
- Download from: https://git-scm.com/download/win

---

## Step 1: Download the Project

### Option A: Download from Replit
1. In Replit, click the three dots menu (⋮) at the top
2. Select "Download as zip"
3. Extract the zip file to your desired location (e.g., `C:\Projects\ai-browser-agent`)

### Option B: Clone from Git (if available)
```cmd
git clone <repository-url>
cd ai-browser-agent
```

---

## Step 2: Install Python Dependencies

Open **Command Prompt** or **PowerShell** in the project directory:

```cmd
cd C:\Projects\ai-browser-agent
```

Install Python packages:

```cmd
pip install flask openai requests sseclient-py
```

---

## Step 3: Install Node.js Dependencies

In the same directory, install the Playwright MCP server dependencies:

```cmd
npm install
```

This will install:
- `@modelcontextprotocol/sdk`
- `playwright`
- `@playwright/test`
- Other required packages

---

## Step 4: Install Playwright Browsers

Playwright needs to download browser binaries (Chromium):

```cmd
npx playwright install chromium
```

---

## Step 5: Set Up OpenAI API Key

You need an OpenAI API key to use the GPT-5 model.

### Get your API key:
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### Set the environment variable:

**Option A: Temporary (for current session only)**
```cmd
set OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Option B: Permanent (recommended)**
1. Open **System Properties** (search "environment variables" in Windows)
2. Click "Environment Variables"
3. Under "User variables", click "New"
4. Variable name: `OPENAI_API_KEY`
5. Variable value: `sk-your-actual-api-key-here`
6. Click OK

**Option C: Create a .env file** (if you modify the code to use python-dotenv)
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

---

## Step 6: Run the Application

Start the Flask web server:

```cmd
python main.py
```

You should see output like:
```
 * Serving Flask app 'app.web_app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

---

## Step 7: Access the Web Interface

Open your web browser and go to:

```
http://localhost:5000
```

You should see the AI Browser Automation Agent interface!

---

## Testing the Application

Try these example instructions:

1. **Simple navigation:**
   ```
   Go to example.com
   ```

2. **Search task:**
   ```
   Navigate to google.com and search for 'Playwright MCP'
   ```

3. **Page interaction:**
   ```
   Open github.com and find trending repositories
   ```

---

## Troubleshooting

### Issue: "Python is not recognized"
- Make sure Python is added to your PATH during installation
- Restart Command Prompt after installing Python
- Try using `py` instead of `python`

### Issue: "npm is not recognized"
- Make sure Node.js is installed correctly
- Restart Command Prompt after installing Node.js
- Check if Node.js is in PATH: `where node`

### Issue: "OPENAI_API_KEY not set"
- Make sure you set the environment variable
- Restart Command Prompt after setting permanent variables
- Verify it's set: `echo %OPENAI_API_KEY%`

### Issue: "Port 5000 already in use"
- Another application is using port 5000
- Edit `main.py` and change the port:
  ```python
  app.run(host='0.0.0.0', port=8000)
  ```
- Then access at: `http://localhost:8000`

### Issue: Browser automation fails
- Make sure Playwright browsers are installed: `npx playwright install chromium`
- Check if antivirus is blocking browser execution
- Try running as Administrator

### Issue: "Module not found" errors
- Make sure all Python packages are installed: `pip install flask openai requests sseclient-py`
- Make sure Node.js packages are installed: `npm install`

---

## Project Structure

```
ai-browser-agent/
├── app/                      # Python application
│   ├── __init__.py
│   ├── web_app.py           # Flask web server
│   ├── mcp_stdio_client.py  # MCP client (subprocess)
│   ├── browser_agent.py     # OpenAI agent
│   ├── templates/
│   │   └── index.html       # Web UI
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── main.py                  # Application entry point
├── cli.js                   # Playwright MCP server (Node.js)
├── package.json             # Node.js dependencies
├── pyproject.toml           # Python project config
└── SETUP.md                 # This file
```

---

## How It Works

1. **Flask Server**: Runs on port 5000, serves the web interface
2. **User Input**: You enter a natural language instruction in the browser
3. **OpenAI Processing**: GPT-5 interprets your instruction
4. **MCP Communication**: Python spawns Node.js subprocess running Playwright MCP
5. **Browser Automation**: Playwright executes browser actions (navigate, click, fill, etc.)
6. **Results**: Actions and results are displayed in real-time

---

## API Endpoints

- `GET /` - Web interface
- `POST /api/execute` - Execute an instruction
- `GET /api/tools` - List available browser tools
- `POST /api/reset` - Reset agent conversation
- `GET /health` - Health check

---

## Stopping the Application

Press `Ctrl + C` in the Command Prompt window to stop the server.

---

## Notes for Windows Users

1. **Firewall**: Windows may ask for firewall permission - allow it
2. **Antivirus**: Some antivirus software may block browser automation - add exception if needed
3. **PowerShell**: If using PowerShell, use `$env:OPENAI_API_KEY="sk-..."` to set variables
4. **Paths**: Use backslashes (`\`) for Windows paths, or forward slashes (`/`) work too
5. **Long Paths**: If you encounter path length issues, enable long paths in Windows

---

## Production Deployment

This setup is for **development/testing only**. For production:

1. **Use a production WSGI server** (not Flask development server):
   ```cmd
   pip install gunicorn
   gunicorn --bind 0.0.0.0:5000 app.web_app:app
   ```
   Note: Gunicorn doesn't work natively on Windows. Use `waitress` instead:
   ```cmd
   pip install waitress
   waitress-serve --host=0.0.0.0 --port=5000 app.web_app:app
   ```

2. **Use environment variables** for all secrets (never hardcode API keys)

3. **Add security headers** and CORS configuration

4. **Consider deploying to a cloud platform** (Replit, Heroku, AWS, Azure, etc.)

---

## Cost Considerations

- **OpenAI API**: You'll be charged based on GPT-5 usage (tokens processed)
- Each instruction execution calls OpenAI multiple times (typically 2-5 calls)
- Monitor your usage at: https://platform.openai.com/usage

---

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify all prerequisites are installed correctly
3. Make sure your OpenAI API key is valid and has credits
4. Check that port 5000 is not blocked by firewall

---

## License

See LICENSE file for details.

---

**Enjoy automating with AI!** 🤖
