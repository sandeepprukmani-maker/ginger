# Windows Setup Guide

## Quick Start for Windows

### Step 1: Create a `.env` file

**IMPORTANT**: The file MUST be named `.env` exactly (no `.txt` extension!)

1. Open Notepad or any text editor
2. Copy this template and paste it:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   SESSION_SECRET=my-secret-key-123
   CORS_ALLOWED_ORIGINS=*
   ```
3. Replace `your-openai-api-key-here` with your actual OpenAI API key
4. Click "File" → "Save As"
5. **Important**: In the "Save as type" dropdown, select "All Files (*.*)"
6. Name the file exactly: `.env` (with the dot at the beginning)
7. Save it in the project root directory (same folder as `main.py`)

**Common Mistake**: Windows often hides file extensions. If your file shows as `.env.txt`, you need to:
- Open File Explorer
- Click "View" → Check "File name extensions"
- Rename the file to remove the `.txt` part

### Step 2: Verify Your Setup

**Run this command to check if your .env file is configured correctly:**

```bash
python check_env.py
```

If you see all green checkmarks (✅), you're good to go!

If you see red X marks (❌), follow the error messages to fix the issues.

### Step 3: Install Python Dependencies

Open Command Prompt or PowerShell in the project directory and run:

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python main.py
```

The application will:
- Load your `.env` file automatically
- Start the web server on http://localhost:5782
- Open your browser to that address

## Troubleshooting

### Error: "OPENAI_API_KEY environment variable is not set"

**Solution**: Make sure you created the `.env` file (not `.env.txt`) in the project root directory with your actual API key.

### Error: "No module named 'dotenv'"

**Solution**: Install python-dotenv:
```bash
pip install python-dotenv
```

### Browser doesn't open automatically

**Solution**: Manually open your browser and go to:
```
http://localhost:5782
```

## Getting Your OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign in or create an account
3. Navigate to API Keys section
4. Click "Create new secret key"
5. Copy the key (it starts with `sk-`)
6. Paste it into your `.env` file

## Security Note

**IMPORTANT**: Never commit your `.env` file to Git! It's already listed in `.gitignore` to prevent accidental commits.
