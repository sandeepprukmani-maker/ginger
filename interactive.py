#!/usr/bin/env python3
"""
🎮 Interactive Browser Automation - Quick Launcher
Launch the interactive REPL mode with a single command
"""

import asyncio
import sys
from src.automation.interactive_mode import start_interactive_mode


def print_usage():
    """Print usage information."""
    print("""
🎮 Interactive Browser Automation

Usage:
  python interactive.py [options]

Options:
  --gpt4o, -4          Use GPT-4o for maximum intelligence (slower, more accurate)
  --no-vision          Disable vision-based element detection
  --visible, -v        Show browser window (non-headless mode)
  --help, -h           Show this help message

Examples:
  python interactive.py                    # Start with default settings
  python interactive.py --gpt4o            # Use GPT-4o for better accuracy
  python interactive.py --visible          # Show browser window
  python interactive.py --gpt4o --visible  # Max intelligence + visible browser

Once started, type 'help' for interactive commands.
    """)


async def main():
    """Main entry point."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print_usage()
        return
    
    use_gpt4o = "--gpt4o" in sys.argv or "-4" in sys.argv
    no_vision = "--no-vision" in sys.argv
    visible = "--visible" in sys.argv or "-v" in sys.argv
    
    await start_interactive_mode(
        use_gpt4o=use_gpt4o,
        enable_vision=not no_vision,
        headless=not visible
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
