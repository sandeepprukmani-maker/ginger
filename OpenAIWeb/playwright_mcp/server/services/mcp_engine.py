"""
Playwright MCP automation engine adapter
"""
from typing import Dict, Any
from .mcp_client import MCPStdioClient
from .automation_engine_interface import AutomationEngine, ExecutionResult
from .browser_agent import BrowserAgent


class MCPAutomationEngine:
    """Adapter for Playwright MCP automation engine"""
    
    def __init__(self):
        self.mcp_client = None
        self._browser_agent = None
        
    @property
    def name(self) -> str:
        return "playwright-mcp"
    
    def _ensure_initialized(self):
        """Ensure MCP client and browser agent are initialized"""
        if self.mcp_client is None:
            self.mcp_client = MCPStdioClient()
            if not self.mcp_client.initialized:
                self.mcp_client.initialize()
        
        if self._browser_agent is None:
            self._browser_agent = BrowserAgent(self.mcp_client)
    
    def execute_instruction(
        self, 
        instruction: str, 
        headless: bool = True
    ) -> ExecutionResult:
        """Execute instruction using Playwright MCP"""
        try:
            self._ensure_initialized()
            
            # Execute the instruction via BrowserAgent
            result = self._browser_agent.execute_instruction(instruction)
            
            # Transform BrowserAgent result to ExecutionResult format
            if result.get('success', False):
                return ExecutionResult(
                    success=True,
                    message=result.get('message', 'Task completed successfully'),
                    steps=self._format_steps(result.get('steps', [])),
                    engine_used=self.name,
                    fallback_occurred=False
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                return ExecutionResult(
                    success=False,
                    message=f"Playwright MCP execution failed: {error_msg}",
                    steps=self._format_steps(result.get('steps', [])),
                    error=error_msg,
                    engine_used=self.name,
                    fallback_occurred=False
                )
                
        except Exception as e:
            error_msg = str(e)
            return ExecutionResult(
                success=False,
                message=f"Playwright MCP execution failed: {error_msg}",
                steps=[],
                error=error_msg,
                engine_used=self.name,
                fallback_occurred=False
            )
    
    def _format_steps(self, steps: list) -> list:
        """Format BrowserAgent steps to match expected format"""
        formatted_steps = []
        for i, step in enumerate(steps, 1):
            formatted_step = {
                'step_number': i,
                'success': step.get('success', True),
                'tool': step.get('tool', ''),
                'arguments': step.get('arguments', {}),
                'result': step.get('result', {})
            }
            
            if 'error' in step:
                formatted_step['error'] = step['error']
            
            formatted_steps.append(formatted_step)
        
        return formatted_steps
    
    def reset_conversation(self) -> None:
        """Reset conversation state"""
        if self._browser_agent:
            self._browser_agent.reset_conversation()
        
        if self.mcp_client:
            try:
                self.mcp_client.call_tool('browser_close', {})
            except:
                pass
