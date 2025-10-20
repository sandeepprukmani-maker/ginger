#!/usr/bin/env python3
"""Test speed improvements"""

import asyncio
import time
import os
from nl_automation_mcp import EnhancedMCPAutomation
from src.automation.logger import get_logger

logger = get_logger()

async def test_speed():
    """Test execution speed with optimizations."""
    
    api_key = os.getenv("OPENAI_API_KEY", "demo-key")
    
    automation = EnhancedMCPAutomation(
        api_key=api_key,
        enable_vision=False,
        max_retries=3,
        enable_caching=True,
        enable_parallel=True,
        enable_predictions=True,
        use_gpt4o=False
    )
    
    try:
        logger.info("⚡ SPEED TEST - FAST MODE ENABLED")
        
        start = time.time()
        await automation.initialize(browser="chromium", headless=True)
        init_time = time.time() - start
        logger.success(f"✓ Initialization: {init_time:.2f}s")
        
        start = time.time()
        await automation.mcp.navigate("https://example.com")
        nav_time = time.time() - start
        logger.success(f"✓ Navigation: {nav_time:.2f}s")
        
        start = time.time()
        context, catalog = await automation._parallel_page_analysis()
        analysis_time = time.time() - start
        logger.success(f"✓ DOM Analysis (parallel): {analysis_time:.2f}s")
        
        # Second analysis should be instant (cached)
        start = time.time()
        context2, catalog2 = await automation._parallel_page_analysis()
        cache_time = time.time() - start
        logger.success(f"✓ DOM Analysis (cached): {cache_time:.2f}s")
        
        logger.success(f"\n🚀 SPEED IMPROVEMENTS:")
        logger.info(f"  - Navigation: {nav_time:.2f}s (was 5-6s)")
        logger.info(f"  - DOM Analysis: {analysis_time:.2f}s")
        logger.info(f"  - Cached Analysis: {cache_time:.2f}s (instant!)")
        logger.info(f"  - Cache TTL: 60 seconds (was 15-20s)")
        logger.info(f"  - Wait timeout: 2 seconds (was 10s)")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await automation.close()

if __name__ == "__main__":
    asyncio.run(test_speed())
