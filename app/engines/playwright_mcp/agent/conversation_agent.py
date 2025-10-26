"""
OpenAI-powered Browser Agent
Interprets natural language instructions and executes browser actions
"""
import json
import os
import logging
import time
import configparser
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from auth.oauth_handler import get_oauth_token_with_retry
from app.utils.logging_config import (
    should_log_llm_requests, 
    should_log_llm_responses,
    should_log_browser_actions,
    should_log_page_state,
    should_log_performance
)

# Load .env file from project root with explicit path
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)


class BrowserAgent:
    """AI agent that performs browser automation based on natural language instructions"""
    
    def __init__(self, mcp_client: Any):
        """
        Initialize the Browser Agent
        
        Args:
            mcp_client: MCP client for browser automation
        """
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        
        self.mcp_client = mcp_client
        
        gateway_base_url = os.environ.get('GW_BASE_URL')
        if not gateway_base_url:
            raise ValueError("GW_BASE_URL must be set as environment variable to connect to the gateway endpoint.")
        
        try:
            oauth_token = get_oauth_token_with_retry(max_retries=3)
        except Exception as e:
            raise ValueError(f"Failed to obtain OAuth token: {str(e)}. Please check your OAuth configuration.")
        
        self.client = OpenAI(
            base_url=gateway_base_url,
            api_key=oauth_token,
            default_headers={
                "Authorization": f"Bearer {oauth_token}"
            }
        )
        self.model = config.get('openai', 'model', fallback='gpt-4.1-2025-04-14-eastus-dz')
        self.conversation_history = []
        self.max_iterations = 10
        
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.log_llm_requests = should_log_llm_requests()
        self.log_llm_responses = should_log_llm_responses()
        self.log_browser_actions = should_log_browser_actions()
        self.log_page_state = should_log_page_state()
        self.log_performance = should_log_performance()
        
        # Store gateway URL for logging
        self.gateway_base_url = gateway_base_url
        
    def execute_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Execute a natural language instruction
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with execution results and steps taken
        """
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_schema()
        
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are an intelligent browser automation assistant. 
You help users automate web browsing tasks using natural language instructions.

When given an instruction:
1. Break it down into browser automation steps
2. Use the available browser tools to accomplish the task
3. Navigate to websites, click elements, fill forms, and extract information as needed
4. Always check the page state after navigation to understand what's available
5. Use element references (ref) from the page snapshot when clicking or filling forms
6. Be precise and follow the user's intent carefully

Important: When you see page snapshots in YAML format, look for element references like [ref=e1], [ref=e2], etc. 
Use these references when calling browser_click or browser_fill tools.

Respond with tool calls to accomplish the task."""
            },
            {
                "role": "user",
                "content": instruction
            }
        ]
        
        steps = []
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            try:
                # Log LLM request details
                if self.log_llm_requests:
                    self.logger.debug("=" * 80)
                    self.logger.debug(f"📤 LLM REQUEST (Iteration {iteration}/{self.max_iterations})")
                    self.logger.debug(f"Model: {self.model}")
                    self.logger.debug(f"Gateway: {self.gateway_base_url}")
                    self.logger.debug(f"Messages count: {len(self.conversation_history)}")
                    self.logger.debug(f"Tools available: {len(tools)}")
                    self.logger.debug("=" * 80)
                
                if self.log_performance:
                    start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,  # type: ignore
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096
                )
                
                if self.log_performance:
                    elapsed = time.time() - start_time
                    self.logger.debug(f"⏱️  LLM response received in {elapsed:.2f}s")
                
                # Log LLM response details
                if self.log_llm_responses:
                    self.logger.debug("=" * 80)
                    self.logger.debug(f"📥 LLM RESPONSE (Iteration {iteration})")
                    self.logger.debug(f"Finish reason: {response.choices[0].finish_reason}")
                    if response.usage:
                        self.logger.debug(f"Tokens - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
                    self.logger.debug("=" * 80)
                
                message = response.choices[0].message
                self.conversation_history.append(message.model_dump())
                
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name  # type: ignore
                        tool_args = json.loads(tool_call.function.arguments)  # type: ignore
                        
                        # Log browser action
                        if self.log_browser_actions:
                            self.logger.debug("=" * 80)
                            self.logger.debug(f"🎬 BROWSER ACTION: {tool_name}")
                            self.logger.debug(f"Arguments: {json.dumps(tool_args, indent=2)}")
                            self.logger.debug("=" * 80)
                        
                        try:
                            if self.log_performance:
                                action_start = time.time()
                            
                            result = self.mcp_client.call_tool(tool_name, tool_args)
                            
                            if self.log_performance:
                                action_elapsed = time.time() - action_start
                                self.logger.debug(f"⏱️  Action '{tool_name}' completed in {action_elapsed:.2f}s")
                            
                            # Log action result
                            if self.log_browser_actions:
                                self.logger.debug(f"✅ Action '{tool_name}' succeeded")
                                if self.log_page_state and result:
                                    self.logger.debug(f"Result preview: {str(result)[:200]}...")
                            
                            step_info = {
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": True,
                                "result": result
                            }
                            steps.append(step_info)
                            
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result, indent=2)
                            })
                            
                        except Exception as e:
                            error_msg = str(e)
                            
                            # Log action failure
                            if self.log_browser_actions:
                                self.logger.error("=" * 80)
                                self.logger.error(f"❌ Action '{tool_name}' FAILED")
                                self.logger.error(f"Error: {error_msg}")
                                self.logger.error("=" * 80)
                            
                            steps.append({
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": False,
                                "error": error_msg
                            })
                            
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: {error_msg}"
                            })
                else:
                    final_response = message.content or "Task completed"
                    
                    # Generate Playwright code from MCP steps
                    playwright_code = None
                    try:
                        from app.engines.playwright_mcp.mcp_code_generator import generate_playwright_code_from_mcp_steps
                        playwright_code = generate_playwright_code_from_mcp_steps(
                            steps,
                            task_description=instruction
                        )
                    except Exception as e:
                        # Code generation is optional, don't fail the task
                        pass
                    
                    result = {
                        "success": True,
                        "message": final_response,
                        "steps": steps,
                        "iterations": iteration
                    }
                    
                    if playwright_code:
                        result["playwright_code"] = playwright_code
                    
                    return result
                    
            except Exception as e:
                self.logger.error("=" * 80)
                self.logger.error("❌ LLM CALL FAILED")
                self.logger.error(f"Error Type: {type(e).__name__}")
                self.logger.error(f"Error Message: {str(e)}")
                self.logger.error(f"Iteration: {iteration}/{self.max_iterations}")
                self.logger.error("=" * 80)
                import traceback
                self.logger.error(traceback.format_exc())
                
                return {
                    "success": False,
                    "error": str(e),
                    "steps": steps,
                    "iterations": iteration
                }
        
        # Generate Playwright code even if max iterations reached
        playwright_code = None
        try:
            from app.engines.playwright_mcp.mcp_code_generator import generate_playwright_code_from_mcp_steps
            playwright_code = generate_playwright_code_from_mcp_steps(
                steps,
                task_description=instruction
            )
        except Exception:
            pass
        
        result = {
            "success": False,
            "error": "Max iterations reached",
            "steps": steps,
            "iterations": iteration
        }
        
        if playwright_code:
            result["playwright_code"] = playwright_code
        
        return result
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
