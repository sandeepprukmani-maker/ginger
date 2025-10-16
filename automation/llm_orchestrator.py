import json
import os
from typing import Dict, List, Any, Optional
from openai import OpenAI


class LLMOrchestrator:
    """Orchestrates browser automation using LLM to interpret natural language"""
    
    def __init__(self):
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-5"
        self.available_tools = []
        
    def set_available_tools(self, tools: List[Dict[str, Any]]):
        """Set the available MCP tools"""
        self.available_tools = tools
        
    def generate_automation_plan(self, natural_language_command: str) -> Dict[str, Any]:
        """Convert natural language to automation steps"""
        
        tools_description = self._format_tools_for_prompt()
        
        system_prompt = f"""You are a browser automation expert. Convert natural language commands into precise browser automation steps using Playwright MCP tools.

Available MCP Tools:
{tools_description}

Your task:
1. Analyze the user's natural language command
2. Break it down into specific automation steps
3. Map each step to the appropriate MCP tool with exact parameters
4. Return a JSON plan with steps array

Return JSON in this exact format:
{{
    "description": "Brief description of what will be automated",
    "steps": [
        {{
            "tool": "tool_name",
            "arguments": {{}},
            "description": "What this step does"
        }}
    ]
}}

Important guidelines:
- For navigation, use browser_navigate with url parameter
- For clicking, use browser_click with element description and ref
- For typing, use browser_type with element, ref, and text
- For getting page content, use browser_snapshot
- Always start with browser_navigate if a URL is needed
- Be specific with element selectors and descriptions
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": natural_language_command}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
            
            plan = json.loads(content)
            return plan
            
        except Exception as e:
            error_msg = str(e)
            
            if "insufficient_quota" in error_msg or "quota" in error_msg.lower():
                detailed_error = (
                    "OpenAI API quota exceeded. Please add credits to your account:\n"
                    "1. Visit: https://platform.openai.com/account/billing\n"
                    "2. Add a payment method and purchase credits\n"
                    "3. Try again once credits are available"
                )
            elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                detailed_error = (
                    "OpenAI API authentication failed. Please check your API key:\n"
                    "1. Ensure OPENAI_API_KEY environment variable is set\n"
                    "2. Verify the API key is valid at https://platform.openai.com/api-keys\n"
                    "3. Make sure the key has not been revoked"
                )
            else:
                detailed_error = f"Failed to generate plan: {error_msg}"
            
            return {
                "error": detailed_error,
                "description": "Error occurred",
                "steps": []
            }
    
    def generate_reusable_code(self, 
                               command: str, 
                               plan: Dict[str, Any], 
                               results: List[Dict[str, Any]]) -> str:
        """Generate reusable Python code based on the automation"""
        
        system_prompt = """You are a code generation expert. Create clean, reusable Python code for browser automation.

Generate a complete Python script that:
1. Uses the Playwright MCP client
2. Implements the automation steps clearly
3. Includes error handling
4. Has proper comments and documentation
5. Can be easily reused and modified

Return only the Python code, no explanations."""

        user_prompt = f"""Generate reusable Python code for this automation:

Original Command: {command}

Automation Plan:
{json.dumps(plan, indent=2)}

Execution Results:
{json.dumps(results, indent=2)}

Create a complete, working Python script that can be reused."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=4096
            )
            
            content = response.choices[0].message.content
            return content or f"# Error: Empty response from LLM"
            
        except Exception as e:
            return f"# Error generating code: {str(e)}"
    
    def _format_tools_for_prompt(self) -> str:
        """Format available tools for LLM prompt"""
        if not self.available_tools:
            return "No tools available"
        
        formatted = []
        for tool in self.available_tools[:20]:
            tool_info = f"- {tool.get('name', 'unknown')}: {tool.get('description', '')}"
            if 'inputSchema' in tool:
                params = tool['inputSchema'].get('properties', {})
                tool_info += f"\n  Parameters: {list(params.keys())}"
            formatted.append(tool_info)
        
        return "\n".join(formatted)
