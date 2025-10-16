#!/usr/bin/env python3
"""
Browser Automation with Natural Language
Uses Playwright MCP server and LLM to automate browser tasks
"""

import asyncio
import sys
import os
from automation import AutomationEngine


async def main():
    """Main entry point for the automation system"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║   🤖 Browser Automation with Natural Language               ║
║   Powered by Playwright MCP + LLM                           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("\nTo use this automation system, you need an OpenAI API key:")
        print("1. Get your API key from: https://platform.openai.com/api-keys")
        print("2. Set it as an environment variable: export OPENAI_API_KEY='your-key'")
        print("3. Ensure your account has credits at: https://platform.openai.com/account/billing")
        sys.exit(1)
    
    engine = AutomationEngine()
    
    try:
        await engine.initialize()
        
        if len(sys.argv) > 1:
            command = " ".join(sys.argv[1:])
            await engine.execute_automation(command)
        else:
            print("\n💡 Usage Examples:")
            print("  python main.py 'navigate to google.com and search for Playwright'")
            print("  python main.py 'open github.com and click on sign in button'")
            print("  python main.py 'go to example.com and take a snapshot of the page'")
            
            print("\n🎯 Interactive Mode:")
            print("Enter your automation command (or 'quit' to exit):\n")
            
            while True:
                try:
                    command = input("➜ ").strip()
                    
                    if command.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break
                    
                    if not command:
                        continue
                    
                    await engine.execute_automation(command)
                    print("\n" + "─" * 60 + "\n")
                    
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
    
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
