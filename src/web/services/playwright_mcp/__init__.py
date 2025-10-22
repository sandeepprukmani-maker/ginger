"""
Playwright MCP Engine Module
Model Context Protocol-based browser automation using Playwright
"""
from .engine import MCPAutomationEngine
from .client import MCPStdioClient
from .browser_agent import BrowserAgent

__all__ = ['MCPAutomationEngine', 'MCPStdioClient', 'BrowserAgent']
