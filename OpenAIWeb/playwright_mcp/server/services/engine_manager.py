"""
Engine Manager - Orchestrates automation engine selection and fallback
"""
from typing import Literal, Optional
from .automation_engine_interface import ExecutionResult
from .browser_use_engine import BrowserUseAutomationEngine
from .mcp_engine import MCPAutomationEngine


EngineMode = Literal["auto", "browser-use", "playwright-mcp"]


class EngineManager:
    """Manages automation engine selection and fallback logic"""
    
    def __init__(self):
        self.browser_use = BrowserUseAutomationEngine()
        self.mcp = MCPAutomationEngine()
        
    def execute(
        self, 
        instruction: str,
        engine_mode: EngineMode = "auto",
        headless: bool = True
    ) -> ExecutionResult:
        """
        Execute instruction with specified engine mode and fallback
        
        Args:
            instruction: Natural language instruction
            engine_mode: "auto" (browser-use with MCP fallback), "browser-use", or "playwright-mcp"
            headless: Run browser in headless mode
            
        Returns:
            ExecutionResult with execution details and metadata
        """
        if engine_mode == "playwright-mcp":
            return self._execute_with_mcp(instruction, headless)
        elif engine_mode == "browser-use":
            return self._execute_with_browser_use(instruction, headless)
        else:
            return self._execute_with_auto_fallback(instruction, headless)
    
    def _execute_with_browser_use(
        self, 
        instruction: str, 
        headless: bool
    ) -> ExecutionResult:
        """Execute with browser-use only"""
        result = self.browser_use.execute_instruction(instruction, headless)
        return result
    
    def _execute_with_mcp(
        self, 
        instruction: str, 
        headless: bool
    ) -> ExecutionResult:
        """Execute with Playwright MCP only"""
        result = self.mcp.execute_instruction(instruction, headless)
        return result
    
    def _execute_with_auto_fallback(
        self, 
        instruction: str, 
        headless: bool
    ) -> ExecutionResult:
        """
        Execute with browser-use first, fallback to MCP on failure
        Priority: browser-use > playwright-mcp
        """
        result = self.browser_use.execute_instruction(instruction, headless)
        
        if result.success:
            return result
        
        print(f"⚠️ Browser-use failed: {result.error}")
        print(f"🔄 Falling back to Playwright MCP...")
        
        fallback_result = self.mcp.execute_instruction(instruction, headless)
        fallback_result.fallback_occurred = True
        
        if fallback_result.success:
            fallback_result.message = f"Completed with fallback to {fallback_result.engine_used}. Original error: {result.error}"
        else:
            fallback_result.message = f"Both engines failed. Browser-use: {result.error}. MCP: {fallback_result.error}"
            fallback_result.error = f"browser-use: {result.error} | playwright-mcp: {fallback_result.error}"
        
        return fallback_result
    
    def reset(self, engine_mode: Optional[EngineMode] = None) -> None:
        """Reset conversation state for one or all engines"""
        if engine_mode == "browser-use" or engine_mode is None:
            self.browser_use.reset_conversation()
        if engine_mode == "playwright-mcp" or engine_mode is None:
            self.mcp.reset_conversation()
    
    def get_available_engines(self) -> dict:
        """Get list of available engines"""
        return {
            'engines': [
                {
                    'id': 'auto',
                    'name': 'Auto (browser-use → MCP fallback)',
                    'description': 'Uses browser-use first, falls back to Playwright MCP on failure'
                },
                {
                    'id': 'browser-use',
                    'name': 'Browser-use only',
                    'description': 'AI-powered automation with browser-use library'
                },
                {
                    'id': 'playwright-mcp',
                    'name': 'Playwright MCP only',
                    'description': 'Playwright Model Context Protocol server'
                }
            ]
        }
