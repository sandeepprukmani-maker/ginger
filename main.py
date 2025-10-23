"""
Main entry point for the AI Browser Automation web application
"""
import os
from openai import OpenAI
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Set API key temporarily
    os.environ["OPENAI_API_KEY"] = "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"

    # Create OpenAI client (reads API key from env)
    client = OpenAI()

    # Example usage with the new API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}]
    )

    print(response.choices[0].message.content)

    # Start the web app
    app.run(host='0.0.0.0', port=5782, debug=False)
