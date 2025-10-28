"""
Playwright MCP Codebase
Tool-based browser automation using Playwright's Model Context Protocol
"""
from app.engines.playwright_mcp.client.stdio_client import MCPStdioClient
from app.engines.playwright_mcp.agent.conversation_agent import BrowserAgent


def create_engine(headless: bool = False):
    """
    Factory function to create a Playwright MCP engine instance
    
    Args:
        headless: Run browser in headless mode
        
    Returns:
        Tuple of (mcp_client, browser_agent)
    """
    mcp_client = MCPStdioClient(headless=headless)
    browser_agent = BrowserAgent(mcp_client)
    return mcp_client, browser_agent


__all__ = ['MCPStdioClient', 'BrowserAgent', 'create_engine']
