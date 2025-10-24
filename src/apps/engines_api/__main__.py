"""
Main entry point for the AI Browser Automation web application
"""
import os
import sys
from dotenv import load_dotenv
from .app import create_app

# Force unbuffered output for better logging
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore
os.environ['PYTHONUNBUFFERED'] = '1'

# Load .env file and override any existing environment variables
load_dotenv(override=True)

app = create_app()

if __name__ == '__main__':
    # IMPORTANT: Do not hardcode API keys in source files. Read from environment.
    api_key = os.environ.get("OPENAI_API_KEY")
    
    print("="*80)
    print("🚀 AI BROWSER AUTOMATION - STARTING UP")
    print("="*80)
    
    if not api_key:
        print("\n⚠️  WARNING: OPENAI_API_KEY environment variable is not set.")
        print("   The application will start but AI features will not work.")
        print("   Please set the OPENAI_API_KEY in your Replit Secrets.\n")
    else:
        print(f"✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
    
    sys.stdout.flush()

    print("\n🌐 Starting Engines API on internal port 5001...")
    print("   (Proxied by VisionVault UI on port 5000)")
    print("="*80)
    print("\n💡 TIP: Keep this console window open to see automation logs\n")
    sys.stdout.flush()

    # Start the engines API on internal port (proxied by VisionVault)
    app.run(host='127.0.0.1', port=5001, debug=True, use_reloader=False)
