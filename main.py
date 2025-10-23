"""
Main entry point for the AI Browser Automation web application
"""
import os
import sys
from openai import OpenAI
from app import create_app

app = create_app()

if __name__ == '__main__':
    # IMPORTANT: Do not hardcode API keys in source files. Read from environment.
    api_key = os.environ.get("OPENAI_API_KEY")
    print(api_key)
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Set it in your shell before running this app. Example (Windows cmd.exe):")
        print('    set OPENAI_API_KEY=sk-your-actual-api-key-here')
        print("Or follow the README instructions to configure environment variables securely.")
        sys.exit(1)

    # Create OpenAI client (reads API key from env)
    client = OpenAI()

    # Example usage with the new API (only run when API key is present)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}]
        )

        # Print assistant message if available
        if getattr(response, 'choices', None) and len(response.choices) > 0:
            msg = getattr(response.choices[0], 'message', None)
            if msg is not None:
                print(msg.content)
    except Exception as e:
        # Don't expose sensitive details; just log enough to debug.
        print(f"Warning: example OpenAI call failed: {e}")

    # Start the web app
    app.run(host='0.0.0.0', port=5782, debug=False)
