#!/usr/bin/env python3
import argparse
import asyncio
import sys
import os
from dotenv import load_dotenv
from automation_engine import BrowserAutomationEngine

def print_header():
    print("\n" + "="*60)
    print("  AI Browser Automation CLI")
    print("  Powered by OpenAI & browser-use")
    print("="*60 + "\n")

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="AI-powered browser automation using natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "search for Python tutorials on Google"
  python main.py "scrape top 10 Hacker News posts with titles and URLs"
  python main.py --no-headless "go to GitHub and find trending Python repos"
        """
    )
    
    parser.add_argument(
        "task",
        type=str,
        help="Natural language description of the task to perform"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (default: True)"
    )
    
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Show browser window during automation"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed logs during execution"
    )
    
    return parser.parse_args()

async def main():
    load_dotenv()
    
    api_key = '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'
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("\nPlease set your OpenAI API key:")
        print("1. Copy .env.example to .env")
        print("2. Add your OpenAI API key to the .env file")
        print("\nGet your API key from: https://platform.openai.com/api-keys")
        sys.exit(1)
    
    args = parse_arguments()
    
    headless = args.headless and not args.no_headless
    
    print_header()
    print(f"📋 Task: {args.task}")
    print(f"🤖 Model: {args.model}")
    print(f"🌐 Headless Mode: {'Yes' if headless else 'No'}")
    print(f"📊 Verbose: {'Yes' if args.verbose else 'No'}")
    print("\n" + "-"*60 + "\n")
    
    engine = BrowserAutomationEngine(
        api_key=api_key,
        model=args.model,
        headless=headless,
        verbose=args.verbose
    )
    
    try:
        print("🚀 Starting browser automation...\n")
        result = await engine.run_task(args.task)
        
        print("\n" + "-"*60)
        print("✅ Task completed successfully!")
        print("-"*60 + "\n")
        
        if result:
            print("📄 Result:")
            print(result)
            print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Task interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
