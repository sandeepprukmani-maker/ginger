#!/usr/bin/env python3
"""Debug script to understand browser-use history structure"""
import asyncio
import os
from dotenv import load_dotenv
from src.automation_engine import BrowserAutomationEngine

async def main():
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    engine = BrowserAutomationEngine(
        api_key=api_key,
        model="gpt-4o-mini",
        headless=True,
        verbose=True,
        generate_code=False
    )
    
    print("Running simple test task...\n")
    response = await engine.run_task("go to example.com", output_file=None)
    
    history = response['history']
    print("\n" + "="*60)
    print("HISTORY STRUCTURE ANALYSIS")
    print("="*60)
    print(f"History type: {type(history)}")
    print(f"History class name: {history.__class__.__name__}")
    print(f"\nAvailable attributes:")
    attrs = [a for a in dir(history) if not a.startswith('_')]
    for attr in attrs[:20]:
        print(f"  - {attr}")
    
    # Try different access methods
    print(f"\nhasattr(history, 'history'): {hasattr(history, 'history')}")
    print(f"hasattr(history, 'model_actions'): {hasattr(history, 'model_actions')}")
    print(f"hasattr(history, 'items'): {hasattr(history, 'items')}")
    print(f"hasattr(history, '__iter__'): {hasattr(history, '__iter__')}")
    
    # Try to iterate
    print("\nAttempting to iterate over history:")
    try:
        for i, item in enumerate(history):
            print(f"  Item {i}: type={type(item)}, value={item}")
            if i >= 2:  # Just show first 3
                break
    except Exception as e:
        print(f"  Error iterating: {e}")
    
    # Try history.history
    if hasattr(history, 'history'):
        print("\nAccessing history.history:")
        try:
            hist_items = history.history
            print(f"  Type: {type(hist_items)}")
            print(f"  Length: {len(hist_items) if hasattr(hist_items, '__len__') else 'N/A'}")
            if hist_items:
                print(f"  First item type: {type(hist_items[0])}")
                print(f"  First item attributes: {[a for a in dir(hist_items[0]) if not a.startswith('_')][:15]}")
                if hasattr(hist_items[0], '__dict__'):
                    print(f"  First item dict keys: {list(hist_items[0].__dict__.keys())}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Try model_actions
    if hasattr(history, 'model_actions'):
        print("\nCalling history.model_actions():")
        try:
            actions = history.model_actions()
            print(f"  Type: {type(actions)}")
            print(f"  Length: {len(actions) if hasattr(actions, '__len__') else 'N/A'}")
            if actions:
                print(f"  First action type: {type(actions[0])}")
                if hasattr(actions[0], '__dict__'):
                    print(f"  First action dict keys: {list(actions[0].__dict__.keys())}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
