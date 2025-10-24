"""
Browser-Use Codebase
AI-powered browser automation using browser-use library with LLM reasoning
"""
from app.engines.browser_use.engine import BrowserUseEngine
from app.engines.browser_use.engine_optimized import OptimizedBrowserUseEngine


def create_engine(headless: bool = False, use_optimized: bool = True):
    """
    Factory function to create a Browser-Use engine instance
    
    Args:
        headless: Run browser in headless mode
        use_optimized: Use optimized engine with advanced features (default: True)
        
    Returns:
        BrowserUseEngine or OptimizedBrowserUseEngine instance
    """
    if use_optimized:
        return OptimizedBrowserUseEngine(headless=headless, enable_advanced_features=True)
    else:
        return BrowserUseEngine(headless=headless)


__all__ = ['BrowserUseEngine', 'OptimizedBrowserUseEngine', 'create_engine']
