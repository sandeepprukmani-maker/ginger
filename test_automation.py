#!/usr/bin/env python3
"""
Quick test script to verify the automation system works
"""

import asyncio
import sys
from automation import AutomationEngine


async def test_basic_automation():
    """Test basic automation functionality"""
    
    print("🧪 Testing Browser Automation System...")
    print("-" * 60)
    
    engine = AutomationEngine()
    
    try:
        print("\n1. Initializing engine...")
        await engine.initialize()
        print("✅ Engine initialized successfully")
        
        print("\n2. Testing simple navigation...")
        result = await engine.execute_automation("navigate to example.com")
        
        if result.get("success"):
            print("\n✅ Test passed!")
            print(f"   - Results saved to: {result['files']['results']}")
            print(f"   - Code saved to: {result['files']['code']}")
            return True
        else:
            print("\n❌ Test failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.close()


if __name__ == "__main__":
    success = asyncio.run(test_basic_automation())
    sys.exit(0 if success else 1)
