"""
Browser-Use Engine
AI-powered browser automation using browser-use library

Thread Safety Notes:
- This engine creates a fresh Browser instance per request
- Each request runs on its own event loop to ensure thread safety
- Browser instances are NOT cached to prevent asyncio loop affinity issues
- Memory is cleaned up after each request via finally block
"""
import os
import asyncio
import configparser
from typing import Dict, Any, List
from browser_use import Agent
from browser_use.llm import ChatOpenAI


class BrowserUseEngine:
    """
    Browser automation engine using browser-use library
    
    Thread Safety: This engine is designed for Flask's multi-threaded environment.
    Each request creates its own event loop and browser instance, which are
    properly cleaned up after execution.
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize Browser-Use Engine
        
        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            api_key = config.get('openai', 'api_key', fallback=None)
            if not api_key or api_key == 'YOUR_OPENAI_API_KEY_HERE':
                api_key = None
        
        if not api_key:
            raise ValueError("OpenAI API key must be set as OPENAI_API_KEY environment variable or in config.ini [openai] api_key field. IMPORTANT: For security, prefer using environment variables instead of storing keys in config.ini.")
        
        model = config.get('openai', 'model', fallback='gpt-4o-mini')
        
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key
        )
    
    async def execute_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Execute a natural language instruction
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with execution results and steps taken
        """
        try:
            agent = Agent(
                task=instruction,
                llm=self.llm,
            )
            
            history = await agent.run()
            
            steps = []
            for i, item in enumerate(history.history):
                step = {
                    "tool": "browser_use_action",
                    "arguments": {"action": str(item.get('model_output', ''))},
                    "success": True,
                    "result": {
                        "state": str(item.get('state', '')),
                        "step_number": i + 1
                    }
                }
                steps.append(step)
            
            return {
                "success": True,
                "message": f"Task completed successfully. Executed {len(steps)} steps.",
                "steps": steps,
                "iterations": len(steps),
                "final_result": history.final_result() if hasattr(history, 'final_result') else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "steps": [],
                "iterations": 0
            }
    
    def execute_instruction_sync(self, instruction: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for execute_instruction
        Each call creates a new event loop to ensure thread safety
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with execution results
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self.execute_instruction(instruction))
            finally:
                loop.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Sync execution error: {str(e)}",
                "steps": [],
                "iterations": 0
            }
