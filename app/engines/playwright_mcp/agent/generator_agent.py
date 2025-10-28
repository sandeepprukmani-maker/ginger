"""
Playwright Generator Agent
Converts test plans into executable Playwright test code
Based on Microsoft's Playwright Test Agents specification
"""
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from ..file_manager import AgentFileManager

logger = logging.getLogger(__name__)


class GeneratorAgent:
    """
    🎭 Generator Agent - Transforms Markdown plans into executable Playwright tests
    
    Following Microsoft's Playwright Test Agents conventions:
    - Reads test plans from specs/ directory
    - Validates selectors live during generation
    - Generates clean, production-ready Playwright Python code
    - Saves tests to tests/ directory
    - References seed tests for patterns and setup
    """
    
    def __init__(self, mcp_client, llm_client: OpenAI, model: str, file_manager: Optional[AgentFileManager] = None):
        """
        Initialize the Generator Agent
        
        Args:
            mcp_client: MCP client for browser automation and selector validation
            llm_client: OpenAI client instance
            model: Model name to use
            file_manager: Optional file manager for reading specs and saving tests
        """
        self.mcp_client = mcp_client
        self.client = llm_client
        self.model = model
        self.file_manager = file_manager or AgentFileManager()
        self.max_iterations = 20
        
    def generate_test_code(self, test_plan: str, instruction: str, seed_test: Optional[str] = None,
                          spec_file: Optional[str] = None, save_to_file: bool = True) -> Dict[str, Any]:
        """
        Generate executable Playwright test code from a test plan
        
        Based on Microsoft's 🎭 Generator specification:
        - Reads Markdown test plan
        - Validates selectors live using browser tools
        - Generates production-ready Playwright Python code
        - Saves to tests/ directory with spec references
        
        Args:
            test_plan: Markdown test plan from Planner Agent (or spec file content)
            instruction: Original user instruction for context
            seed_test: Optional seed test for patterns and context
            spec_file: Optional path to spec file (for reference in generated test)
            save_to_file: Whether to save the test to tests/ directory
            
        Returns:
            Dictionary with generated code, file path, and validation steps
        """
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_schema()
        
        # Microsoft's exact Generator prompt
        system_prompt = """You are the 🎭 Generator Agent from Microsoft's Playwright Test Agents.

Your role is to transform Markdown test plans into executable, high-quality Playwright Python test code.

**Input:**
- Markdown test plan from the Planner Agent
- Seed test for patterns and setup examples
- Original instruction for context

**Your Process:**
1. Read and understand the complete test plan structure
2. Navigate to the application using browser tools
3. For each scenario in the plan:
   - Validate that selectors and elements exist
   - Test interactions work as described
   - Verify expected outcomes are achievable
4. Generate clean, production-ready code with:
   - Robust selectors (prioritize: get_by_role > get_by_label > get_by_text > get_by_placeholder)
   - Comprehensive assertions for all expected results
   - Proper waits (expect().to_be_visible(), page.wait_for_load_state())
   - Clear comments mapping to plan steps
   - pytest structure and conventions

**Code Generation Standards:**

```python
# spec: specs/feature-name.md
# seed: tests/seed.spec.py

from playwright.sync_api import Page, expect
import pytest


def test_scenario_name(page: Page):
    \"\"\"
    Clear description of what this test validates
    Maps to: Test Plan Section X.Y
    \"\"\"
    # Step 1: Navigate to application
    page.goto("https://app.example.com")
    page.wait_for_load_state("networkidle")
    
    # Step 2: Click the input field
    input_field = page.get_by_role("textbox", name="What needs to be done?")
    input_field.click()
    
    # Step 3: Type text
    input_field.fill("Buy groceries")
    
    # Step 4: Press Enter
    input_field.press("Enter")
    
    # Expected Result: Todo appears in list
    expect(page.get_by_text("Buy groceries")).to_be_visible()
    
    # Expected Result: Checkbox is unchecked
    todo_checkbox = page.get_by_role("checkbox", name="Toggle Todo")
    expect(todo_checkbox).to_be_visible()
    expect(todo_checkbox).not_to_be_checked()
    
    # Expected Result: Counter shows "1 item left"
    expect(page.get_by_text("1 item left")).to_be_visible()
    
    # Expected Result: Input is cleared
    expect(input_field).to_have_value("")
```

**Quality Standards:**
- Use semantic selectors that match user intent
- Add assertions for EVERY expected result in the plan
- Include wait conditions to handle async behavior
- Structure tests to be maintainable and readable
- Match the seed test's coding style and patterns

**Browser Tools:**
Use browser tools during generation to:
- Navigate and verify pages load correctly
- Find and validate selectors before adding to code
- Test that interactions work as expected
- Confirm assertions will pass

When selector validation is complete, provide the final Python test code."""

        # Build user message with all context
        user_message_parts = [
            f"**Instruction:** {instruction}",
            f"\n**Test Plan:**\n{test_plan}"
        ]
        
        if seed_test:
            user_message_parts.append(f"\n**Seed Test (use as pattern):**\n```python\n{seed_test}\n```")
        
        user_message_parts.append("\n**Task:**\nExplore the application to validate selectors, then generate complete, executable Playwright Python test code that implements all scenarios from the test plan.")
        
        user_message = "\n".join(user_message_parts)
        
        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
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
                    
                    # Save to file if requested
                    test_file_path = None
                    if save_to_file and generated_code:
                        # Extract test name from code or plan
                        test_name = self._extract_test_name(generated_code, instruction)
                        test_file_path = self.file_manager.save_test(
                            test_name, 
                            generated_code,
                            spec_ref=spec_file,
                            seed_ref="tests/seed.spec.py" if seed_test else None
                        )
                    
                    return {
                        "success": True,
                        "generated_code": generated_code,
                        "test_file": test_file_path,
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
    
    def _extract_test_name(self, test_code: str, instruction: str) -> str:
        """
        Extract a suitable test name from the generated code or instruction
        
        Args:
            test_code: The generated test code
            instruction: Original user instruction
            
        Returns:
            Test name for the file
        """
        import re
        
        # Try to extract from def test_xxx
        match = re.search(r'def (test_\w+)\(', test_code)
        if match:
            return match.group(1)
        
        # Fallback to instruction-based name
        safe_name = instruction.lower().replace(' ', '_')
        safe_name = re.sub(r'[^a-z0-9_]', '', safe_name)
        return f"test_{safe_name}"[:50]
