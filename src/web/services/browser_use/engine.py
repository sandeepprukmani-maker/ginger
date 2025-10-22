"""
BrowserUse automation engine adapter
"""
import os
import asyncio
from typing import Dict, Any
from browser_use import Agent, Browser, BrowserProfile
from langchain_openai import ChatOpenAI
from ..automation_engine_interface import AutomationEngine, ExecutionResult


class BrowserUseAutomationEngine:
    """Adapter for browser-use automation engine"""
    
    def __init__(self):
        self._api_key = os.getenv('OPENAI_API_KEY')
        
    @property
    def name(self) -> str:
        return "browser-use"
    
    def execute_instruction(
        self, 
        instruction: str, 
        headless: bool = True
    ) -> ExecutionResult:
        """Execute instruction using browser-use"""
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=self._api_key
            )
            
            profile = BrowserProfile(headless=headless)
            browser = Browser(browser_profile=profile)
            
            task_instruction = (
                f"{instruction}\n\n"
                "IMPORTANT INSTRUCTIONS:\n"
                "1. You may do necessary auxiliary actions (wait for page loads, dismiss popups, etc.) to complete those steps.\n"
                "2. After completing the user's specified steps, STOP IMMEDIATELY.\n"
                "3. Do NOT continue to what seems like the 'next logical step' or try to complete an entire workflow.\n"
                "4. When you finish the last step specified by the user, call 'done' immediately."
            )
            
            agent = Agent(
                task=task_instruction,
                llm=llm,
                browser=browser
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                history = loop.run_until_complete(agent.run())
                
                steps = self._extract_steps_from_history(history)
                result_message = self._extract_result(history) or 'Task completed successfully'
                
                return ExecutionResult(
                    success=True,
                    message=result_message,
                    steps=steps,
                    engine_used=self.name,
                    fallback_occurred=False
                )
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = str(e)
            return ExecutionResult(
                success=False,
                message=f"Browser-use execution failed: {error_msg}",
                steps=[],
                error=error_msg,
                engine_used=self.name,
                fallback_occurred=False
            )
    
    def _extract_result(self, history) -> str:
        """Extract final result from history"""
        if not history:
            return None
        
        if hasattr(history, 'final_result') and history.final_result():
            return str(history.final_result())
        
        if hasattr(history, 'history') and history.history:
            last_item = history.history[-1]
            if hasattr(last_item, 'result') and hasattr(last_item.result, 'extracted_content'):
                return last_item.result.extracted_content
        
        return None
    
    def _extract_steps_from_history(self, history) -> list:
        """Extract execution steps from browser-use history"""
        steps = []
        
        if not history:
            return steps
        
        if hasattr(history, 'history'):
            for i, item in enumerate(history.history, 1):
                step = {
                    'step_number': i,
                    'success': True,
                    'tool': 'browser-use action',
                    'arguments': {},
                    'result': {}
                }
                
                if hasattr(item, 'model_output') and item.model_output:
                    step['result']['thought'] = str(item.model_output.current_state.thought) if hasattr(item.model_output.current_state, 'thought') else ''
                    
                    if hasattr(item.model_output, 'action'):
                        action = item.model_output.action
                        if hasattr(action, '__class__'):
                            step['tool'] = action.__class__.__name__
                        if hasattr(action, '__dict__'):
                            step['arguments'] = {k: str(v) for k, v in action.__dict__.items() if not k.startswith('_')}
                
                if hasattr(item, 'result'):
                    if hasattr(item.result, 'extracted_content'):
                        step['result']['content'] = item.result.extracted_content
                    elif hasattr(item.result, '__dict__'):
                        step['result'].update({k: str(v) for k, v in item.result.__dict__.items() if not k.startswith('_')})
                
                steps.append(step)
        
        return steps
    
    def reset_conversation(self) -> None:
        """Reset conversation state"""
        pass
