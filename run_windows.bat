@echo off
REM Windows launcher for AI Browser Automation
REM This ensures console logs appear properly in Windows

echo ================================================================================
echo    AI BROWSER AUTOMATION - WINDOWS LAUNCHER
echo ================================================================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo.
    echo SETUP REQUIRED:
    echo   1. Copy .env.example to .env
    echo   2. Edit .env and add your OPENAI_API_KEY
    echo   3. Run this script again
    echo.
    echo See PLEASE_READ_WINDOWS.md for detailed instructions
    echo.
    pause
    exit /b 1
)

REM Set Python to unbuffered mode for immediate console output
set PYTHONUNBUFFERED=1

echo [*] Starting Flask application with console logging enabled...
echo [*] Logs will appear below. Keep this window open!
echo ================================================================================
echo.

REM Run the application
python main.py

pause
