"""
Engine Orchestrator
Manages and coordinates all browser automation engines
"""
from typing import Dict, Any, Tuple, Optional
import logging
import playwright_mcp_codebase
import browser_use_codebase
import hybrid_engine
from app.middleware.security import sanitize_error_message

logger = logging.getLogger(__name__)


class EngineOrchestrator:
    """
    Orchestrates browser automation engines (Hybrid, Playwright MCP, and Browser-Use)
    Handles engine instantiation, caching, and execution delegation
    """
    
    def __init__(self):
        """Initialize the orchestrator with empty engine caches"""
        self.playwright_engines = {}
        self.browser_use_engines = {}
        self.hybrid_engines = {}
    
    def get_playwright_engine(self, headless: bool) -> Tuple[Any, Any]:
        """
        Get or create Playwright MCP engine instance
        
        Args:
            headless: Run in headless mode
            
        Returns:
            Tuple of (mcp_client, browser_agent)
        """
        if headless not in self.playwright_engines:
            mcp_client, browser_agent = playwright_mcp_codebase.create_engine(headless=headless)
            self.playwright_engines[headless] = (mcp_client, browser_agent)
        
        return self.playwright_engines[headless]
    
    def get_browser_use_engine(self, headless: bool):
        """
        Get or create Browser-Use engine instance
        Caches instances per headless mode for better performance
        
        Args:
            headless: Run in headless mode
            
        Returns:
            BrowserUseEngine instance
        """
        if headless not in self.browser_use_engines:
            self.browser_use_engines[headless] = browser_use_codebase.create_engine(headless=headless)
        
        return self.browser_use_engines[headless]
    
    def get_hybrid_engine(self, headless: bool):
        """
        Get or create Hybrid engine instance
        
        Args:
            headless: Run in headless mode
            
        Returns:
            HybridEngine instance
        """
        if headless not in self.hybrid_engines:
            self.hybrid_engines[headless] = hybrid_engine.create_engine(headless=headless)
        
        return self.hybrid_engines[headless]
    
    def execute_instruction(self, instruction: str, engine_type: str, headless: bool) -> Dict[str, Any]:
        """
        Execute an instruction using the specified engine
        
        Args:
            instruction: Natural language instruction
            engine_type: 'hybrid', 'playwright_mcp', or 'browser_use'
            headless: Run in headless mode
            
        Returns:
            Execution result dictionary
        """
        valid_engines = ['hybrid', 'playwright_mcp', 'browser_use']
        if engine_type not in valid_engines:
            logger.error(f"Invalid engine type: {engine_type}")
            return {
                'success': False,
                'error': f"Invalid engine type: {engine_type}. Must be one of: {', '.join(valid_engines)}",
                'steps': [],
                'iterations': 0,
                'engine': engine_type,
                'headless': headless
            }
        
        result = None
        try:
            if engine_type == 'hybrid':
                engine = self.get_hybrid_engine(headless)
                result = engine.execute_instruction_sync(instruction)
                
            elif engine_type == 'playwright_mcp':
                client, agent = self.get_playwright_engine(headless)
                
                try:
                    if not client.initialized:
                        logger.info("Initializing Playwright MCP client...")
                        client.initialize()
                    
                    result = agent.execute_instruction(instruction)
                except Exception as e:
                    logger.error(f"Playwright MCP error: {str(e)}, attempting to reinitialize")
                    self._reset_playwright_engine(headless)
                    raise
                
            elif engine_type == 'browser_use':
                engine = self.get_browser_use_engine(headless)
                result = engine.execute_instruction_sync(instruction)
            
            if result is not None:
                result['engine'] = engine_type
                result['headless'] = headless
                return result
            else:
                raise ValueError("Engine returned no result")
            
        except Exception as e:
            logger.error(f"Engine execution error ({engine_type}): {str(e)}", exc_info=True)
            user_message = sanitize_error_message(e)
            return {
                'success': False,
                'error': 'Execution failed',
                'message': user_message,
                'steps': [],
                'iterations': 0,
                'engine': engine_type,
                'headless': headless
            }
    
    def _reset_playwright_engine(self, headless: bool):
        """
        Reset Playwright engine if it crashes or becomes unresponsive
        
        Args:
            headless: Headless mode setting
        """
        if headless in self.playwright_engines:
            logger.warning(f"Resetting Playwright engine (headless={headless})")
            try:
                client, _ = self.playwright_engines[headless]
                if hasattr(client, 'cleanup'):
                    client.cleanup()
            except Exception as e:
                logger.error(f"Error during Playwright cleanup: {str(e)}")
            finally:
                del self.playwright_engines[headless]
    
    def get_tools(self, engine_type: str) -> list:
        """
        Get available tools for the specified engine
        
        Args:
            engine_type: 'hybrid', 'playwright_mcp', or 'browser_use'
            
        Returns:
            List of available tools
        """
        if engine_type == 'playwright_mcp':
            client, _ = self.get_playwright_engine(headless=True)
            
            if not client.initialized:
                client.initialize()
            
            return client.list_tools()
        elif engine_type == 'hybrid':
            return [
                {'name': 'hybrid_agent', 'description': 'Intelligent hybrid automation (Browser-Use + Playwright MCP fallback)'}
            ]
        else:
            return [
                {'name': 'browser_use_agent', 'description': 'AI-powered browser automation'}
            ]
    
    def cleanup_after_timeout(self, engine_type: str, headless: bool):
        """
        Clean up resources after a timed-out execution
        
        Args:
            engine_type: Engine that was executing when timeout occurred
            headless: Headless mode setting
        """
        logger.warning(f"Cleaning up after timeout for {engine_type} (headless={headless})")
        
        try:
            if engine_type == 'playwright_mcp' or engine_type == 'hybrid':
                self._reset_playwright_engine(headless)
            
            if engine_type == 'hybrid' and headless in self.hybrid_engines:
                del self.hybrid_engines[headless]
        except Exception as e:
            logger.error(f"Error during timeout cleanup: {str(e)}")
    
    def reset_agent(self, engine_type: str, headless: bool = True):
        """
        Reset the conversation history for the specified engine
        
        Args:
            engine_type: 'hybrid', 'playwright_mcp', or 'browser_use'
            headless: Headless mode (for Playwright MCP and Hybrid)
        """
        if engine_type == 'hybrid':
            engine = self.get_hybrid_engine(headless)
            engine.reset()
        elif engine_type == 'playwright_mcp':
            _, agent = self.get_playwright_engine(headless)
            agent.reset_conversation()
