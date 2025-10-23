"""
Hybrid Engine
Intelligent browser automation that uses Browser-Use by default with Playwright MCP fallback
"""
from hybrid_engine.engine import HybridEngine


def create_engine(headless: bool = False):
    """
    Factory function to create a Hybrid engine instance
    
    Args:
        headless: Run browser in headless mode
        
    Returns:
        HybridEngine instance
    """
    return HybridEngine(headless=headless)


__all__ = ['HybridEngine', 'create_engine']
