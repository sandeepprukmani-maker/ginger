"""
Test LLM connection with custom gateway for browser-use
"""
import os
import asyncio
from dotenv import load_dotenv
from browser_use.llm import ChatOpenAI
from browser_use.llm.messages import BaseMessage
from pydantic import BaseModel
from auth.oauth_handler import get_oauth_token_with_retry

load_dotenv()

class TestOutput(BaseModel):
    """Simple test schema"""
    message: str
    success: bool

async def test_basic_chat():
    """Test basic chat without structured output"""
    print("=" * 80)
    print("TEST 1: Basic Chat (No Structured Output)")
    print("=" * 80)
    
    gateway_base_url = os.environ.get('GW_BASE_URL')
    oauth_token = get_oauth_token_with_retry(max_retries=3)
    
    llm = ChatOpenAI(
        model="gpt-4.1-2025-04-14-eastus-dz",
        base_url=gateway_base_url,
        api_key=oauth_token,
        default_headers={
            "Authorization": f"Bearer {oauth_token}"
        },
        timeout=60
    )
    
    messages = [BaseMessage(role="user", content="Say 'Hello, World!' and nothing else.")]
    
    try:
        response = await llm.ainvoke(messages)
        print(f"✅ Success! Response: {response.completion}")
        print(f"📊 Usage: {response.usage}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_structured_output():
    """Test structured output (what browser-use actually uses)"""
    print("\n" + "=" * 80)
    print("TEST 2: Structured Output (Browser-Use Style)")
    print("=" * 80)
    
    gateway_base_url = os.environ.get('GW_BASE_URL')
    oauth_token = get_oauth_token_with_retry(max_retries=3)
    
    llm = ChatOpenAI(
        model="gpt-4.1-2025-04-14-eastus-dz",
        base_url=gateway_base_url,
        api_key=oauth_token,
        default_headers={
            "Authorization": f"Bearer {oauth_token}"
        },
        timeout=60
    )
    
    messages = [BaseMessage(
        role="user", 
        content='Respond with JSON: {"message": "Hello from structured output", "success": true}'
    )]
    
    try:
        response = await llm.ainvoke(messages, output_format=TestOutput)
        print(f"✅ Success! Structured response: {response.completion}")
        print(f"  - Message: {response.completion.message}")
        print(f"  - Success: {response.completion.success}")
        print(f"📊 Usage: {response.usage}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_openai_client():
    """Test direct OpenAI client call"""
    print("\n" + "=" * 80)
    print("TEST 3: Direct OpenAI AsyncClient")
    print("=" * 80)
    
    from openai import AsyncOpenAI
    
    gateway_base_url = os.environ.get('GW_BASE_URL')
    oauth_token = get_oauth_token_with_retry(max_retries=3)
    
    client = AsyncOpenAI(
        base_url=gateway_base_url,
        api_key=oauth_token,
        default_headers={
            "Authorization": f"Bearer {oauth_token}"
        },
        timeout=60
    )
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4.1-2025-04-14-eastus-dz",
            messages=[{"role": "user", "content": "Say 'Direct client works!' and nothing else."}],
            temperature=0.7
        )
        print(f"✅ Success! Response: {response.choices[0].message.content}")
        print(f"📊 Usage: {response.usage}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n🔍 TESTING LLM CONNECTION WITH CUSTOM GATEWAY\n")
    
    results = []
    
    # Test 1: Basic chat
    results.append(("Basic Chat", await test_basic_chat()))
    
    # Test 2: Structured output
    results.append(("Structured Output", await test_structured_output()))
    
    # Test 3: Direct client
    results.append(("Direct OpenAI Client", await test_direct_openai_client()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n🎉 All tests passed! Browser-use should work.")
    else:
        print("\n⚠️  Some tests failed. See errors above.")

if __name__ == "__main__":
    asyncio.run(main())
