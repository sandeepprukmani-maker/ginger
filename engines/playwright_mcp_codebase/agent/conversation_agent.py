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
        self.max_iterations = 30
        
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
                "content": """You are an advanced browser automation agent with powerful reasoning and execution capabilities.

CORE COMPETENCIES:
1. **Web Navigation**: Navigate to URLs, follow links, use browser back/forward
2. **Element Interaction**: Click buttons, links, images using element references from page snapshots
3. **Form Handling**: Fill text inputs, textareas, select dropdowns, check boxes using [ref=XX] references
4. **Data Extraction**: Extract text content, page titles, HTML, structured data from pages
5. **Page Analysis**: Take snapshots to understand page structure, find elements, verify state
6. **Multi-Step Flows**: Chain actions together for complex workflows

ADVANCED AUTOMATION PATTERNS:
- **Authentication**: Navigate to login, fill credentials, submit, verify login success
- **Search & Filter**: Enter search terms, apply filters, navigate results
- **Form Submission**: Fill all required fields, validate, submit, check confirmation
- **Data Collection**: Navigate pages, extract data, compile results
- **Shopping/E-commerce**: Browse products, add to cart, proceed to checkout
- **Account Management**: Update profiles, change settings, manage preferences

ELEMENT REFERENCE USAGE:
- ALWAYS check page snapshot first using browser_snapshot tool
- Look for element markers like [ref=e1], [ref=e2], [ref=e3] in snapshots
- Use these exact reference numbers when calling browser_click or browser_fill
- Example: If you see "Login Button [ref=e5]", use ref="e5" in browser_click

WORKFLOW STRATEGY:
1. Take a snapshot to understand current page state
2. Identify target elements and their reference numbers
3. Execute actions using the correct element references
4. Verify action succeeded by taking another snapshot
5. Proceed to next step or conclude task

ERROR HANDLING:
- If an action fails, take another snapshot to see current state
- Try alternative selectors or approaches
- Provide clear feedback on what went wrong
- Suggest next steps if task cannot be completed

COMPLETION CRITERIA:
- Execute ALL steps mentioned in the instruction
- Verify final state matches expected outcome
- Extract and return any requested data
- Provide summary of what was accomplished

Be thorough, precise, and adaptive. Use your tools effectively to accomplish any automation task."""
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
                    messages=self.conversation_history,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096
                )
                
                message = response.choices[0].message
                self.conversation_history.append(message.model_dump())
                
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
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
                    return {
                        "success": True,
                        "message": final_response,
                        "steps": steps,
                        "iterations": iteration
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "steps": steps,
                    "iterations": iteration
                }
        
        return {
            "success": False,
            "error": "Max iterations reached",
            "steps": steps,
            "iterations": iteration
        }
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
