#!/usr/bin/env python3
import argparse
import asyncio
import sys
import os
from dotenv import load_dotenv
from src.automation_engine import BrowserAutomationEngine

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
  # Run automation and see results
  python main.py "search for Python tutorials on Google"
  
  # Generate reusable Playwright code
  python main.py "go to example.com and click login" --generate-code --output login.py
  
  # Execute generated code with self-healing
  python main.py --execute-code login.py
  
  # Run with visible browser
  python main.py "scrape Hacker News" --no-headless
        """
    )
    
    parser.add_argument(
        "task",
        type=str,
        nargs="?",
        help="Natural language description of the task to perform"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (default: False)"
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
    
    parser.add_argument(
        "--generate-code",
        action="store_true",
        help="Generate reusable Playwright Python code from the automation"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="generated_automation.py",
        help="Output file for generated code (default: generated_automation.py)"
    )
    
    parser.add_argument(
        "--execute-code",
        type=str,
        metavar="FILE",
        help="Execute a previously generated automation script with self-healing"
    )
    
    return parser.parse_args()

async def execute_generated_code(code_file: str, api_key: str, model: str, verbose: bool):
    """Execute a previously generated automation script with self-healing"""
    from src.self_healing_executor import SelfHealingExecutor
    import importlib.util
    
    if not os.path.exists(code_file):
        print(f"❌ Error: File not found: {code_file}")
        sys.exit(1)
    
    print(f"🔧 Loading automation script: {code_file}")
    print(f"🤖 Self-healing enabled with model: {model}")
    print("\n" + "-"*60 + "\n")
    
    executor = SelfHealingExecutor(
        api_key=api_key,
        model=model,
        verbose=verbose
    )
    
    spec = importlib.util.spec_from_file_location("automation_module", code_file)
    if spec is None or spec.loader is None:
        print(f"❌ Error: Could not load module from {code_file}")
        sys.exit(1)
    
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
        
        if hasattr(module, 'automated_task'):
            automation_func = module.automated_task
        else:
            func_names = [name for name in dir(module) if not name.startswith('_') and callable(getattr(module, name))]
            if func_names:
                automation_func = getattr(module, func_names[0])
            else:
                print("❌ Error: No automation function found in script")
                sys.exit(1)
        
        print("🚀 Starting self-healing execution...\n")
        await executor.execute_with_healing(automation_func)
        
        print("\n" + "-"*60)
        print("✅ Automation completed successfully!")
        print("-"*60)
        
    except Exception as e:
        print(f"\n❌ Execution failed: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


async def main():
    load_dotenv()
    
    api_key = "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"
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("\nPlease set your OpenAI API key:")
        print("1. Copy .env.example to .env")
        print("2. Add your OpenAI API key to the .env file")
        print("\nGet your API key from: https://platform.openai.com/api-keys")
        sys.exit(1)
    
    args = parse_arguments()
    
    print_header()
    
    if args.execute_code:
        await execute_generated_code(
            code_file=args.execute_code,
            api_key=api_key,
            model=args.model,
            verbose=args.verbose
        )
        return
    
    if not args.task:
        print("❌ Error: Task description required")
        print("Use --help for usage information")
        sys.exit(1)
    
    headless = args.headless and not args.no_headless
    
    print(f"📋 Task: {args.task}")
    print(f"🤖 Model: {args.model}")
    print(f"🌐 Headless Mode: {'Yes' if headless else 'No'}")
    print(f"📊 Verbose: {'Yes' if args.verbose else 'No'}")
    if args.generate_code:
        print(f"📝 Code Generation: Enabled (output: {args.output})")
    print("\n" + "-"*60 + "\n")
    
    engine = BrowserAutomationEngine(
        api_key=api_key,
        model=args.model,
        headless=headless,
        verbose=args.verbose,
        generate_code=args.generate_code
    )
    
    try:
        print("🚀 Starting browser automation...\n")
        response = await engine.run_task(
            args.task,
            output_file=args.output if args.generate_code else None
        )
        
        print("\n" + "-"*60)
        print("✅ Task completed successfully!")
        print("-"*60 + "\n")
        
        if response.get('result'):
            print("📄 Result:")
            print(response['result'])
            print()
        
        if response.get('code_file'):
            print(f"📝 Generated code saved to: {response['code_file']}")
            print(f"\nTo execute with self-healing:")
            print(f"  python main.py --execute-code {response['code_file']}")
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
