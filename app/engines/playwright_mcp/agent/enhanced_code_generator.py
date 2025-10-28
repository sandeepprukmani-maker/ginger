"""
Enhanced Code Generator
Combines direct execution with Generator agent's sophisticated selector validation
Produces high-quality Playwright code with rich, reusable locators
"""
import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class EnhancedCodeGenerator:
    """
    Enhanced code generator that validates selectors live and creates rich locators
    
    This combines:
    - Direct execution to capture steps
    - Generator agent's live selector validation
    - Sophisticated locator extraction and optimization
    """
    
    def __init__(self, mcp_client, llm_client: OpenAI, model: str):
        """
        Initialize the enhanced code generator
        
        Args:
            mcp_client: MCP client for browser automation and validation
            llm_client: OpenAI client instance
            model: Model name to use
        """
        self.mcp_client = mcp_client
        self.client = llm_client
        self.model = model
        self.max_iterations = 15
        
    def generate_validated_code(
        self,
        execution_steps: List[Dict[str, Any]],
        instruction: str
    ) -> Dict[str, Any]:
        """
        Generate Playwright code with live selector validation
        
        This method:
        1. Takes execution steps from direct mode
        2. Navigates to the application to validate selectors
        3. Finds optimal selectors using Generator agent's approach
        4. Generates production-ready Playwright code
        
        Args:
            execution_steps: Steps captured from direct execution
            instruction: Original user instruction
            
        Returns:
            Dictionary with validated code and metadata
        """
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_schema()
        
        # Create a summary of execution steps for context
        steps_summary = self._create_steps_summary(execution_steps)
        
        # System prompt that combines Generator's validation with direct execution
        system_prompt = """You are an expert Playwright code generator with live validation capabilities.

Your task is to convert browser automation steps into production-ready Playwright Python code.

**Your Process:**
1. **Review Execution Steps**: Understand what actions were performed
2. **Navigate and Validate**: Use browser tools to navigate to the application and validate selectors
3. **Find Optimal Selectors**: For each interaction, find the best selector using this priority:
   - get_by_role() with name (e.g., get_by_role("button", name="Submit"))
   - get_by_label() for form inputs
   - get_by_placeholder() for inputs with placeholders
   - get_by_text() for text elements (keep text short)
   - get_by_test_id() if available
   - Avoid CSS selectors and XPath unless absolutely necessary
4. **Generate Clean Code**: Create maintainable Playwright Python code

**Code Quality Standards:**
- Use semantic locators (role-based, label-based)
- Add explicit waits (page.wait_for_load_state(), expect().to_be_visible())
- Include meaningful comments
- Use pytest structure with proper type hints
- Add assertions where appropriate
- Extract reusable locators

**Code Template:**
```python
from playwright.sync_api import Page, expect
import pytest


def test_automation(page: Page):
    \"\"\"
    [Description of what this automation does]
    \"\"\"
    # Step 1: Navigate to the application
    page.goto("https://example.com", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    
    # Step 2: Interact with elements using semantic locators
    submit_button = page.get_by_role("button", name="Submit")
    expect(submit_button).to_be_visible()
    submit_button.click()
    
    # Step 3: Verify expected outcome
    expect(page.get_by_text("Success")).to_be_visible()
```

**Validation Process:**
- Use browser tools to navigate and inspect elements
- Verify each selector exists before adding to code
- Test interactions work as expected
- Ensure code will be reliable in CI/CD

When validation is complete, provide the final Playwright Python code."""

        # User message with execution steps
        user_message = f"""**Task:** {instruction}

**Execution Steps Captured:**
{steps_summary}

**Your Task:**
1. Navigate to the application using browser tools
2. Validate and find optimal selectors for each action
3. Generate clean, production-ready Playwright Python code
4. Use semantic locators (get_by_role, get_by_label, etc.)
5. Include proper waits and assertions

Please explore the application and generate the validated code."""

        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        validation_steps = []
        iteration = 0
        generated_code = ""
        
        logger.info("🔍 Starting enhanced code generation with live validation...")
        
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
                        
                        logger.debug(f"🔍 Validating: {tool_name}")
                        
                        try:
                            result = self.mcp_client.call_tool(tool_name, tool_args)
                            
                            validation_steps.append({
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": True
                            })
                            
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result, indent=2)
                            })
                            
                        except Exception as e:
                            error_msg = str(e)
                            logger.warning(f"⚠️ Validation warning: {error_msg}")
                            
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
                    
                    logger.info(f"✅ Enhanced code generated ({len(generated_code)} chars, {iteration} iterations)")
                    
                    return {
                        "success": True,
                        "generated_code": generated_code,
                        "validation_steps": validation_steps,
                        "iterations": iteration,
                        "message": "Code generated with live selector validation"
                    }
                    
            except Exception as e:
                logger.error(f"❌ Enhanced generation error: {str(e)}")
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
    
    def _create_steps_summary(self, steps: List[Dict[str, Any]]) -> str:
        """
        Create a human-readable summary of execution steps
        
        Args:
            steps: Execution steps from direct mode
            
        Returns:
            Formatted summary string
        """
        summary_lines = []
        
        for i, step in enumerate(steps, 1):
            tool_name = step.get('tool', 'unknown')
            arguments = step.get('arguments', {})
            success = step.get('success', False)
            
            if not success:
                summary_lines.append(f"{i}. ❌ {tool_name} - Failed")
                continue
            
            if 'navigate' in tool_name.lower():
                url = arguments.get('url', '')
                summary_lines.append(f"{i}. Navigate to: {url}")
            elif 'click' in tool_name.lower():
                ref = arguments.get('ref', '')
                selector = arguments.get('selector', '')
                summary_lines.append(f"{i}. Click element (ref={ref}, selector={selector})")
            elif 'fill' in tool_name.lower() or 'type' in tool_name.lower():
                ref = arguments.get('ref', '')
                value = arguments.get('value', arguments.get('text', ''))
                summary_lines.append(f"{i}. Fill '{value}' (ref={ref})")
            elif 'snapshot' in tool_name.lower():
                summary_lines.append(f"{i}. Inspect page")
            else:
                summary_lines.append(f"{i}. {tool_name}")
        
        return '\n'.join(summary_lines) if summary_lines else "No steps captured"
    
    def _extract_code_from_markdown(self, content: str) -> str:
        """Extract code from markdown code blocks"""
        import re
        
        # Look for ```python or ``` code blocks
        pattern = r'```(?:python)?\s*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            # Return the largest code block (usually the main code)
            return max(matches, key=len).strip()
        
        return ""
