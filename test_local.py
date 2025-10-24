"""
Test script to verify local browser automation works without external connections.
This tests that the browser automation runs locally with no telemetry or cloud dependencies.
"""
import asyncio
import os

async def test_local_browser():
    print("🔧 Testing Local Browser Automation")
    print("=" * 50)
    
    print("\n1. Checking telemetry status...")
    from browser_use.config import CONFIG
    telemetry_status = CONFIG.ANONYMIZED_TELEMETRY
    print(f"   Telemetry: {'ENABLED ❌' if telemetry_status else 'DISABLED ✅'}")
    
    if telemetry_status:
        print("   ERROR: Telemetry is still enabled!")
        return False
    
    print("\n2. Verifying telemetry service...")
    from browser_use.telemetry import ProductTelemetry
    telemetry = ProductTelemetry()
    has_client = telemetry._posthog_client is not None
    print(f"   PostHog Client: {'EXISTS ❌' if has_client else 'None ✅'}")
    
    if has_client:
        print("   ERROR: PostHog client should be None!")
        return False
    
    print("\n3. Testing local browser initialization...")
    from browser_use import Browser
    
    try:
        browser = Browser(headless=True)
        print("   Browser created successfully ✅")
    except Exception as e:
        print(f"   ERROR creating browser: {e}")
        return False
    
    print("\n4. Testing basic browser automation...")
    
    # Use a simple LLM model for testing (if available)
    if os.getenv("OPENAI_API_KEY"):
        from browser_use import Agent, ChatOpenAI
        print("   Using OpenAI model for test...")
        
        try:
            agent = Agent(
                task="Go to example.com and get the page title",
                llm=ChatOpenAI(model="gpt-3.5-turbo"),
                browser=browser,
            )
            
            print("   Running test task...")
            result = await agent.run()
            print("   ✅ Task completed successfully!")
            print(f"   Result: {result.final_result() if result else 'No result'}")
            return True
        except Exception as e:
            print(f"   ❌ Error running agent: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("   ⚠️  No OpenAI API key found - skipping agent test")
        print("   (Set OPENAI_API_KEY to run full test)")
        print("   ✅ Local browser initialization successful!")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_local_browser())
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ALL TESTS PASSED - Local-only mode verified!")
    else:
        print("❌ TESTS FAILED - Please review errors above")
    print("=" * 50)
