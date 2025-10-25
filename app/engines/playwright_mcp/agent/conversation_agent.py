"""
OpenAI-powered Browser Agent
Interprets natural language instructions and executes browser actions
"""
import json
import os
import configparser
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

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
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key must be set as OPENAI_API_KEY environment variable. Never store API keys in config files for security reasons.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = config.get('openai', 'model', fallback='gpt-4o-mini')
        self.conversation_history = []
        self.max_iterations = 10
        
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
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,  # type: ignore
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096
                )
                
                message = response.choices[0].message
                self.conversation_history.append(message.model_dump())
                
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name  # type: ignore
                        tool_args = json.loads(tool_call.function.arguments)  # type: ignore
                        
                        try:
                            result = self.mcp_client.call_tool(tool_name, tool_args)
                            
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
