# Configuration Guide

VisionVault uses a centralized configuration system through `config.ini` at the root level.

## Quick Setup

### Step 1: Copy the Example Configuration

```bash
cp config.ini.example config.ini
```

### Step 2: Add Your API Keys

Edit `config.ini` and replace the placeholder values:

```ini
[API_KEYS]
OPENAI_API_KEY = sk-your-actual-openai-key-here
GEMINI_API_KEY = your-actual-gemini-key-here
```

### Step 3: Customize Other Settings (Optional)

You can modify server settings, browser defaults, automation behavior, and more.

---

## Configuration Sections

### 🔑 API_KEYS

**Required for AI features**

```ini
[API_KEYS]
OPENAI_API_KEY = your_openai_api_key_here
GEMINI_API_KEY = your_gemini_api_key_here
```

- **OPENAI_API_KEY**: Required for MCP Direct, Code Generation, and HYBRID modes
  - Get it from: https://platform.openai.com/api-keys
  
- **GEMINI_API_KEY**: Optional, enables semantic search
  - Get it from: https://ai.google.dev/

---

### 🖥️ SERVER

**Server configuration**

```ini
[SERVER]
HOST = 0.0.0.0
PORT = 5000
DEBUG = false
```

- **HOST**: Server host address (0.0.0.0 = all interfaces)
- **PORT**: Server port (default: 5000)
- **DEBUG**: Enable Flask debug mode (true/false)

---

### 🌐 BROWSER

**Default browser settings**

```ini
[BROWSER]
DEFAULT_BROWSER = chromium
HEADLESS = true
TIMEOUT = 30000
```

- **DEFAULT_BROWSER**: chromium, firefox, or webkit
- **HEADLESS**: Run browser in headless mode (true/false)
- **TIMEOUT**: Default timeout in milliseconds

---

### 🤖 AUTOMATION

**Automation engine settings**

```ini
[AUTOMATION]
MAX_RETRIES = 3
ENABLE_TRACING = true
ENABLE_HEALING = true
```

- **MAX_RETRIES**: Maximum retry attempts for failed operations
- **ENABLE_TRACING**: Enable execution tracing for HYBRID mode
- **ENABLE_HEALING**: Enable auto-healing for failed scripts

---

### 💾 DATABASE

**Database configuration**

```ini
[DATABASE]
DATABASE_URL = sqlite:///data/database/visionvault.db
```

For SQLite (default):
```ini
DATABASE_URL = sqlite:///data/database/visionvault.db
```

For PostgreSQL:
```ini
DATABASE_URL = postgresql://user:password@localhost:5432/visionvault
```

---

### 📁 PATHS

**Directory paths**

```ini
[PATHS]
SCREENSHOTS_DIR = data/uploads/screenshots
LOGS_DIR = data/logs
UPLOADS_DIR = data/uploads
```

All paths are relative to the project root.

---

### ⚡ FEATURES

**Feature flags**

```ini
[FEATURES]
ENABLE_MCP = true
ENABLE_CODE_GEN = true
ENABLE_HYBRID = true
ENABLE_SELF_LEARNING = true
```

- **ENABLE_MCP**: Enable MCP Direct automation mode
- **ENABLE_CODE_GEN**: Enable AI code generation mode
- **ENABLE_HYBRID**: Enable HYBRID mode (MCP + Code Gen)
- **ENABLE_SELF_LEARNING**: Enable self-learning engine

---

## How Configuration Works

### Priority Order

The configuration system loads values in this priority order:

1. **config.ini** (highest priority)
2. **Environment variables**
3. **Default fallback values** (lowest priority)

### Example

If you have:
- `OPENAI_API_KEY` in `config.ini` = `sk-config-key`
- `OPENAI_API_KEY` in environment = `sk-env-key`
- Default fallback = `None`

The system will use: `sk-config-key` from config.ini

### Using in Code

```python
from visionvault.core.config import config

# Get API key
api_key = config.openai_api_key

# Get server settings
host = config.host
port = config.port

# Get feature flags
if config.enable_hybrid:
    # HYBRID mode enabled
    pass
```

---

## Security Best Practices

### ✅ DO:

1. **Keep config.ini private**: Never commit it to version control
2. **Use config.ini.example**: Provide a template without real credentials
3. **Rotate API keys regularly**: Change keys periodically
4. **Use environment variables in production**: For deployment platforms

### ❌ DON'T:

1. **Commit config.ini**: It contains sensitive API keys
2. **Share config.ini**: Keep your credentials private
3. **Hardcode API keys**: Always use configuration

---

## .gitignore Protection

`config.ini` is automatically excluded from git by `.gitignore`:

```gitignore
# Configuration with sensitive data
config.ini
```

This prevents accidentally committing your API keys.

---

## Environment Variables (Alternative)

You can also use environment variables instead of config.ini:

### Linux/macOS

```bash
export OPENAI_API_KEY="sk-your-key-here"
export GEMINI_API_KEY="your-gemini-key-here"
python run_server.py
```

### Windows (CMD)

```cmd
set OPENAI_API_KEY=sk-your-key-here
set GEMINI_API_KEY=your-gemini-key-here
python run_server.py
```

### Windows (PowerShell)

```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
$env:GEMINI_API_KEY="your-gemini-key-here"
python run_server.py
```

---

## Troubleshooting

### "Configuration loaded from: ..." not showing

**Issue**: Config file not found

**Solution**: 
```bash
# Make sure config.ini exists in project root
cp config.ini.example config.ini
```

### API key not working

**Issue**: Still seeing "OPENAI_API_KEY is not set"

**Solution**: 
1. Check config.ini has real API key (not placeholder)
2. Verify no typos in the key
3. Restart the server after updating config.ini

### Features still disabled

**Issue**: HYBRID mode disabled despite having API key

**Solution**:
1. Make sure `OPENAI_API_KEY` is set in config.ini
2. Check feature flags in `[FEATURES]` section
3. Restart the application

---

## Complete Example

Here's a complete working configuration:

```ini
[API_KEYS]
OPENAI_API_KEY = sk-proj-abc123xyz789...
GEMINI_API_KEY = AIzaSyABC123...

[SERVER]
HOST = 0.0.0.0
PORT = 5000
DEBUG = false

[BROWSER]
DEFAULT_BROWSER = chromium
HEADLESS = true
TIMEOUT = 30000

[AUTOMATION]
MAX_RETRIES = 3
ENABLE_TRACING = true
ENABLE_HEALING = true

[DATABASE]
DATABASE_URL = sqlite:///data/database/visionvault.db

[PATHS]
SCREENSHOTS_DIR = data/uploads/screenshots
LOGS_DIR = data/logs
UPLOADS_DIR = data/uploads

[FEATURES]
ENABLE_MCP = true
ENABLE_CODE_GEN = true
ENABLE_HYBRID = true
ENABLE_SELF_LEARNING = true
```

---

## Questions?

- Check SETUP.md for installation instructions
- Review the example configuration in config.ini.example
- API keys are obtained from OpenAI and Google AI platforms

**Happy Configuring! 🚀**
