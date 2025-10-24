# Windows Troubleshooting Guide

## Problem: API Key from Wrong Source

### Symptom
When you run `python main.py`, it prints an API key, but it's not the one from your `.env` file.

### Cause
You likely set `OPENAI_API_KEY` as a **system environment variable** on Windows at some point (maybe when testing earlier). Windows system environment variables take priority over `.env` files.

### Solution: Clear the System Environment Variable

**Option 1: Temporary Fix (Current Terminal Only)**
```cmd
set OPENAI_API_KEY=
```
Then close and reopen your terminal, and run the app again.

**Option 2: Permanent Fix (Remove from System)**

1. Press `Windows Key + R`
2. Type `sysdm.cpl` and press Enter
3. Click "Advanced" tab
4. Click "Environment Variables" button
5. Look in both sections:
   - "User variables for [your username]"
   - "System variables"
6. Find `OPENAI_API_KEY` if it exists
7. Select it and click "Delete"
8. Click OK on all windows
9. **Close ALL Command Prompt/PowerShell windows**
10. Open a fresh terminal

**Option 3: Just Use the .env File (Current Fix)**

Good news! I've updated the code to use `load_dotenv(override=True)`, which means your `.env` file will now **override** any system environment variables. Just make sure you have the correct API key in your `.env` file.

### Verify Your Setup

Run this diagnostic script:
```bash
python check_env.py
```

This will show you:
- ✅ What's in your `.env` file
- ⚠️  If you have a system environment variable set
- ✅ Which one is actually being used

## Problem: Still Getting "API Key Not Set" Error

### Check These Things:

1. **File is named correctly**
   - Must be `.env` (not `.env.txt` or `env`)
   - Run: `dir .env` in the project folder
   - You should see: `.env`

2. **File is in the right location**
   - Must be in the same folder as `main.py`
   - Run: `dir` and verify both `.env` and `main.py` are listed

3. **File has correct content**
   - Run: `type .env` to see contents
   - Should show: `OPENAI_API_KEY=sk-...`
   - Make sure there are NO spaces around the `=` sign
   - Make sure there are NO quotes around the key

4. **Dependencies are installed**
   - Run: `pip install python-dotenv`
   - Then: `pip install -r requirements.txt`

## Common Mistakes

### ❌ WRONG: .env.txt
Windows often adds `.txt` extension automatically when you save in Notepad.

**Fix**: In Notepad, choose "All Files (*.*)" when saving, not "Text Documents (*.txt)"

### ❌ WRONG: Quotes around the key
```
OPENAI_API_KEY="sk-your-key-here"
```

**Fix**: Remove the quotes:
```
OPENAI_API_KEY=sk-your-key-here
```

### ❌ WRONG: Spaces around equals
```
OPENAI_API_KEY = sk-your-key-here
```

**Fix**: Remove spaces:
```
OPENAI_API_KEY=sk-your-key-here
```

### ❌ WRONG: Missing the `sk-` prefix
Your OpenAI API key should start with `sk-` or `sk-proj-`

## Still Not Working?

Run the diagnostic and send me the output:
```bash
python check_env.py
```

This will help me see exactly what's wrong!
