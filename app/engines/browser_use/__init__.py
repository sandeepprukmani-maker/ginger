"""
Browser-Use Codebase
AI-powered browser automation using browser-use library with LLM reasoning
"""
from app.engines.browser_use.engine import BrowserUseEngine
from app.engines.browser_use.engine_optimized import OptimizedBrowserUseEngine


def create_engine(headless: bool = False, use_optimized: bool = True):
    """
    Factory function to create a Browser-Use engine instance
    
    The engine will automatically select the appropriate LLM model based on config.ini:
    - If use_chat_browser_use=true, uses ChatBrowserUse (3-5x faster)
    - Otherwise uses standard OpenAI models
    
    Args:
        headless: Run browser in headless mode
        use_optimized: Use optimized engine with advanced features (default: True)
        
    Returns:
        BrowserUseEngine or OptimizedBrowserUseEngine instance
    """
    # Engines handle LLM selection internally based on config
    if use_optimized:
        return OptimizedBrowserUseEngine(headless=headless, enable_advanced_features=True)
    else:
        return BrowserUseEngine(headless=headless)


__all__ = ['BrowserUseEngine', 'OptimizedBrowserUseEngine', 'create_engine']
