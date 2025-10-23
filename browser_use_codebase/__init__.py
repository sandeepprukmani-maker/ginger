"""
Browser-Use Codebase
AI-powered browser automation using browser-use library with LLM reasoning
"""
from browser_use_codebase.engine import BrowserUseEngine


def create_engine(headless: bool = False):
    """
    Factory function to create a Browser-Use engine instance
    
    Args:
        headless: Run browser in headless mode
        
    Returns:
        BrowserUseEngine instance
    """
    return BrowserUseEngine(headless=headless)


__all__ = ['BrowserUseEngine', 'create_engine']
