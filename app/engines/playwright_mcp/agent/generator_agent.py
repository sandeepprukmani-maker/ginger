"""
Playwright Generator Agent
Converts test plans into executable Playwright test code
"""
import json
import logging
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class GeneratorAgent:
    """
    AI agent that generates executable Playwright test code from test plans
    """
    
    def __init__(self, mcp_client, llm_client: OpenAI, model: str):
        """
        Initialize the Generator Agent
        
        Args:
            mcp_client: MCP client for browser automation and selector validation
            llm_client: OpenAI client instance
            model: Model name to use
        """
        self.mcp_client = mcp_client
        self.client = llm_client
        self.model = model
        self.max_iterations = 20
        
    def generate_test_code(self, test_plan: str, instruction: str) -> Dict[str, Any]:
        """
        Generate executable Playwright test code from a test plan
        
        Args:
            test_plan: Markdown test plan from Planner Agent
            instruction: Original user instruction for context
            
        Returns:
            Dictionary with generated code and validation steps
        """
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_schema()
        
        system_prompt = """You are a Playwright Code Generator Agent.

Your role is to convert test plans into high-quality, executable Playwright Python test code.

When given a test plan:
1. Read through the entire plan to understand all scenarios
2. Use browser tools to validate selectors and interactions work correctly
3. Generate clean, maintainable Playwright code with proper:
   - Robust selectors (prefer get_by_role, get_by_label, get_by_text)
   - Comprehensive assertions
   - Error handling
   - Clear comments explaining each step
4. Use the page object pattern where appropriate
5. Include proper waits and assertions

Generate code using this template:

```python
from playwright.sync_api import Page, expect
import pytest


def test_scenario_name(page: Page):
    \"\"\"
    Test description from plan
    \"\"\"
    # Step 1: [Description]
    page.goto("https://example.com")
    
    # Step 2: [Description]
    page.get_by_role("button", name="Submit").click()
    
    # Assertion: [Expected result]
    expect(page.get_by_text("Success")).to_be_visible()
```

Use browser tools to:
- Navigate and verify pages load correctly  
- Validate selectors exist before adding them to code
- Test interactions work as expected

When exploration is complete, respond with the final generated code (no tool calls)."""

        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Generate Playwright test code for this instruction:
{instruction}

Based on this test plan:
{test_plan}

Explore the application to validate selectors, then generate the complete test code."""}
        ]
        
        validation_steps = []
        iteration = 0
        generated_code = ""
        
        while iteration < self.max_iterations:
            iteration += 1
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=conversation_history,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096
                )
                
                message = response.choices[0].message
                conversation_history.append(message.model_dump())
                
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"🎨 Generator validating: {tool_name}")
                        
                        try:
                            result = self.mcp_client.call_tool(tool_name, tool_args)
                            
                            step_info = {
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": True
                            }
                            validation_steps.append(step_info)
                            
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result, indent=2)
                            })
                            
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"❌ Generator validation failed: {error_msg}")
                            
                            validation_steps.append({
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": False,
                                "error": error_msg
                            })
                            
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: {error_msg}"
                            })
                else:
                    # LLM finished - extract generated code
                    raw_content = message.content or ""
                    
                    # Extract code from markdown code blocks
                    generated_code = self._extract_code_from_markdown(raw_content)
                    
                    if not generated_code:
                        generated_code = raw_content
                    
                    logger.info(f"✅ Test code generated ({len(generated_code)} chars)")
                    
                    return {
                        "success": True,
                        "generated_code": generated_code,
                        "validation_steps": validation_steps,
                        "iterations": iteration
                    }
                    
            except Exception as e:
                logger.error(f"❌ Generator error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "validation_steps": validation_steps,
                    "iterations": iteration
                }
        
        return {
            "success": False,
            "error": "Max iterations reached",
            "generated_code": generated_code,
            "validation_steps": validation_steps,
            "iterations": iteration
        }
    
    def _extract_code_from_markdown(self, content: str) -> str:
        """Extract code from markdown code blocks"""
        import re
        
        # Look for ```python or ``` code blocks
        pattern = r'```(?:python)?\s*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            # Return the largest code block (usually the main test code)
            return max(matches, key=len).strip()
        
        return ""
