"""
Hybrid Engine Implementation
Uses Browser-Use (AI-powered) as primary engine with Playwright MCP (tool-based) as fallback
"""
from typing import Dict, Any
import browser_use_codebase
import playwright_mcp_codebase


class HybridEngine:
    """
    Hybrid browser automation engine
    
    Strategy:
    1. Attempt execution with Browser-Use (AI-powered, autonomous)
    2. If Browser-Use fails, fallback to Playwright MCP (tool-based, reliable)
    3. Track and report which engine was actually used
    
    This provides the best of both worlds:
    - Browser-Use's intelligent autonomous behavior for complex tasks
    - Playwright MCP's reliability and discrete control as safety net
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize Hybrid Engine
        
        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        self.browser_use_engine = None
        self.playwright_client = None
        self.playwright_agent = None
    
    def _ensure_browser_use_engine(self):
        """Lazily create Browser-Use engine"""
        if self.browser_use_engine is None:
            self.browser_use_engine = browser_use_codebase.create_engine(headless=self.headless)
        return self.browser_use_engine
    
    def _ensure_playwright_engine(self):
        """Lazily create Playwright MCP engine"""
        if self.playwright_client is None or self.playwright_agent is None:
            self.playwright_client, self.playwright_agent = playwright_mcp_codebase.create_engine(
                headless=self.headless
            )
        return self.playwright_client, self.playwright_agent
    
    def execute_instruction_sync(self, instruction: str) -> Dict[str, Any]:
        """
        Execute instruction with hybrid approach
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with execution results and engine metadata
        """
        # First attempt: Browser-Use (AI-powered)
        try:
            engine = self._ensure_browser_use_engine()
            result = engine.execute_instruction_sync(instruction)
            
            if result.get('success', False):
                result['engine_used'] = 'browser_use'
                result['fallback_triggered'] = False
                result['hybrid_mode'] = True
                return result
            else:
                # Browser-Use returned failure, try fallback
                browser_use_error = result.get('error', 'Unknown error')
                return self._fallback_to_playwright(instruction, browser_use_error)
                
        except Exception as e:
            # Browser-Use threw exception, try fallback
            return self._fallback_to_playwright(instruction, str(e))
    
    def _fallback_to_playwright(self, instruction: str, browser_use_error: str) -> Dict[str, Any]:
        """
        Fallback to Playwright MCP engine
        
        Args:
            instruction: User's natural language instruction
            browser_use_error: Error message from Browser-Use attempt
            
        Returns:
            Dictionary with execution results and fallback metadata
        """
        try:
            client, agent = self._ensure_playwright_engine()
            
            # Initialize if needed
            if not client.initialized:
                client.initialize()
            
            # Execute with Playwright MCP
            result = agent.execute_instruction(instruction)
            
            # Add hybrid metadata
            result['engine_used'] = 'playwright_mcp'
            result['fallback_triggered'] = True
            result['hybrid_mode'] = True
            result['browser_use_error'] = browser_use_error
            
            return result
            
        except Exception as e:
            # Both engines failed
            return {
                'success': False,
                'error': f'Both engines failed. Browser-Use: {browser_use_error}. Playwright MCP: {str(e)}',
                'engine_used': 'none',
                'fallback_triggered': True,
                'hybrid_mode': True,
                'browser_use_error': browser_use_error,
                'playwright_error': str(e),
                'steps': [],
                'iterations': 0
            }
    
    def reset(self):
        """Reset both engines"""
        # Browser-Use doesn't maintain state, so nothing to reset
        
        # Reset Playwright agent if it exists
        if self.playwright_agent is not None:
            self.playwright_agent.reset_conversation()
