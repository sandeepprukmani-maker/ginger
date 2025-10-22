"""
OpenAI-powered Browser Agent
Interprets natural language instructions and executes browser actions
"""
import json
from typing import List, Dict, Any
from llm_client import get_playwright_mcp_client, get_playwright_mcp_model


class BrowserAgent:
    """AI agent that performs browser automation based on natural language instructions"""
    
    def __init__(self, mcp_client: Any):
        """
        Initialize the Browser Agent
        
        Args:
            mcp_client: MCP client for browser automation
        """
        self.mcp_client = mcp_client
        self.client = get_playwright_mcp_client()
        self.model = get_playwright_mcp_model()
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
        # Initialize MCP connection and get available tools
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_schema()
        
        # Start conversation
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
                # Call OpenAI with function calling
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,  # type: ignore
                    tools=tools,  # type: ignore
                    tool_choice="auto",
                    max_tokens=4096
                )
                
                message = response.choices[0].message
                self.conversation_history.append(message.model_dump())
                
                # Check if assistant wants to call tools
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name  # type: ignore
                        tool_args = json.loads(tool_call.function.arguments)  # type: ignore
                        
                        # Execute the tool
                        try:
                            result = self.mcp_client.call_tool(tool_name, tool_args)
                            
                            # Extract useful information from result
                            step_info = {
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": True,
                                "result": result
                            }
                            steps.append(step_info)
                            
                            # Add tool result to conversation
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
                            
                            # Add error to conversation
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: {error_msg}"
                            })
                else:
                    # Assistant has finished
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
