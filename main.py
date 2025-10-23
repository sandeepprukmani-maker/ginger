"""
Main entry point for the AI Browser Automation web application
"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from app import create_app

# Force unbuffered output for Windows console (ensures logs appear immediately)
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
        print("\n❌ ERROR: OPENAI_API_KEY environment variable is not set.\n")
        print("📋 WINDOWS SETUP INSTRUCTIONS:")
        print("   1. Create a .env file in the project root directory")
        print("   2. Add this line to the .env file:")
        print("      OPENAI_API_KEY=sk-your-actual-api-key-here")
        print("   3. Save the file and restart the application\n")
        print("📖 See PLEASE_READ_WINDOWS.md for complete setup guide")
        print("🧪 Run test_engines.py to verify your setup")
        print("="*80)
        sys.exit(1)
    
    print(f"✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
    sys.stdout.flush()

    # Create OpenAI client (reads API key from env)
    client = OpenAI()

    # Quick API test
    try:
        print("\n🧪 Testing OpenAI API connection...")
        sys.stdout.flush()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}]
        )

        # Print assistant message if available
        if getattr(response, 'choices', None) and len(response.choices) > 0:
            msg = getattr(response.choices[0], 'message', None)
            if msg is not None:
                print(f"✅ API Test Response: {msg.content}")
                sys.stdout.flush()
    except Exception as e:
        print(f"⚠️  Warning: OpenAI API test failed: {e}")
        sys.stdout.flush()

    print("\n🌐 Starting Flask web server...")
    print("📍 Open your browser to: http://localhost:5782")
    print("="*80)
    print("\n💡 TIP: Keep this console window open to see automation logs\n")
    sys.stdout.flush()

    # Start the web app with debug mode for better console output
    app.run(host='0.0.0.0', port=5782, debug=True, use_reloader=False)
