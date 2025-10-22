"""Simple example of using NL2Playwright."""
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from converter import NL2PlaywrightConverter


async def example():
    """Run a simple example."""
    # Get LLM (requires API key in .env)
    if os.getenv('GEMINI_API_KEY'):
        from browser_use import ChatGoogle
        llm = ChatGoogle(model='gemini-2.0-flash-exp', temperature=0.0)
        print("Using Google Gemini")
    elif os.getenv('OPENAI_API_KEY'):
        from browser_use import ChatOpenAI
        llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.0)
        print("Using OpenAI")
    else:
        print("ERROR: Please set GEMINI_API_KEY or OPENAI_API_KEY in .env file")
        return
    
    # Create converter
    converter = NL2PlaywrightConverter(
        llm=llm,
        headless=False,
        output_dir="generated_scripts"
    )
    
    # Example task
    task = "go to google.com and search for cute dogs"
    
    print(f"\nTask: {task}\n")
    print("Converting to Playwright script...\n")
    
    try:
        script, path = await converter.convert(task)
        print(f"\n✅ Success! Script saved to: {path}\n")
        print("="*80)
        print(script)
        print("="*80)
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(example())
