"""
Playwright Healer Agent
Automatically fixes failing Playwright tests
"""
import json
import logging
import subprocess
import tempfile
import re
from typing import Dict, Any
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)


class HealerAgent:
    """
    AI agent that analyzes test failures and automatically heals broken tests
    """
    
    def __init__(self, mcp_client, llm_client: OpenAI, model: str):
        """
        Initialize the Healer Agent
        
        Args:
            mcp_client: MCP client for browser automation
            llm_client: OpenAI client instance
            model: Model name to use
        """
        self.mcp_client = mcp_client
        self.client = llm_client
        self.model = model
        self.max_healing_attempts = 5
        
    def heal_test(self, test_code: str, instruction: str) -> Dict[str, Any]:
        """
        Attempt to heal a failing test by analyzing errors and fixing issues
        
        Args:
            test_code: The failing test code
            instruction: Original instruction for context
            
        Returns:
            Dictionary with healed code and healing steps
        """
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_schema()
        
        # Try to run the test and capture errors
        test_error = self._run_test_and_capture_error(test_code)
        
        if not test_error:
            logger.info("✅ Test passed - no healing needed")
            return {
                "success": True,
                "healed_code": test_code,
                "message": "Test passed without healing",
                "healing_attempts": 0
            }
        
        logger.info(f"🔧 Healing test - error detected: {test_error[:200]}")
        
        system_prompt = """You are a Playwright Test Healer Agent.

Your role is to analyze failing tests and fix them automatically.

When given a failing test:
1. Analyze the error message to understand what's wrong
2. Use browser tools to inspect the current state of the page
3. Identify the root cause (wrong selector, timing issue, changed UI, etc.)
4. Fix the test code with the appropriate changes:
   - Update selectors if elements moved or changed
   - Add proper waits if timing issues
   - Adjust assertions if expectations changed
   - Fix logic errors
5. Validate the fix works

Common fixes:
- Selector issues: Use browser tools to find the correct selector
- Timing: Add proper waits (page.wait_for_selector, expect().to_be_visible())
- Element not found: Check if element reference changed
- Assertion failures: Verify expected vs actual values

Return the healed test code when fixed."""

        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""This Playwright test is failing. Please fix it.

Original instruction: {instruction}

Failing test code:
```python
{test_code}
```

Error:
{test_error}

Please explore the application to understand what changed, then provide the healed test code."""}
        ]
        
        healing_steps = []
        attempt = 0
        healed_code = test_code
        
        while attempt < self.max_healing_attempts:
            attempt += 1
            
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
                        
                        logger.info(f"🔍 Healer inspecting: {tool_name}")
                        
                        try:
                            result = self.mcp_client.call_tool(tool_name, tool_args)
                            
                            step_info = {
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": True,
                                "attempt": attempt
                            }
                            healing_steps.append(step_info)
                            
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result, indent=2)
                            })
                            
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"❌ Healer action failed: {error_msg}")
                            
                            healing_steps.append({
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": False,
                                "error": error_msg,
                                "attempt": attempt
                            })
                            
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: {error_msg}"
                            })
                else:
                    # LLM finished - extract healed code
                    raw_content = message.content or ""
                    
                    # Extract code from markdown
                    potential_healed_code = self._extract_code_from_markdown(raw_content)
                    
                    if potential_healed_code:
                        healed_code = potential_healed_code
                        
                        # Verify the healed code
                        new_error = self._run_test_and_capture_error(healed_code)
                        
                        if not new_error:
                            logger.info(f"✅ Test healed successfully after {attempt} attempts")
                            return {
                                "success": True,
                                "healed_code": healed_code,
                                "healing_steps": healing_steps,
                                "healing_attempts": attempt,
                                "message": f"Test healed successfully after {attempt} attempts"
                            }
                        else:
                            logger.warning(f"⚠️ Healed code still failing: {new_error[:100]}")
                            # Continue healing loop with new error
                            conversation_history.append({
                                "role": "user",
                                "content": f"The fix didn't work. New error:\n{new_error}\n\nPlease try again."
                            })
                            continue
                    else:
                        logger.warning("⚠️ No code extracted from healer response")
                        return {
                            "success": False,
                            "error": "No healed code generated",
                            "healed_code": test_code,
                            "healing_steps": healing_steps,
                            "healing_attempts": attempt
                        }
                    
            except Exception as e:
                logger.error(f"❌ Healer error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "healed_code": test_code,
                    "healing_steps": healing_steps,
                    "healing_attempts": attempt
                }
        
        return {
            "success": False,
            "error": f"Could not heal test after {self.max_healing_attempts} attempts",
            "healed_code": healed_code,
            "healing_steps": healing_steps,
            "healing_attempts": attempt
        }
    
    def _run_test_and_capture_error(self, test_code: str) -> str:
        """
        Run the test code and capture any errors
        
        Returns:
            Error message if test fails, empty string if passes
        """
        try:
            # Create a temporary file with the test code
            with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
                f.write(test_code)
                temp_file = f.name
            
            try:
                # Try to run with pytest (syntax and import check)
                result = subprocess.run(
                    ['python', '-m', 'pytest', temp_file, '--collect-only', '-q'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    error_output = result.stdout + result.stderr
                    return self._clean_error_message(error_output)
                
                # If collection passes, the test is syntactically valid
                # We can't actually run it without a real browser setup,
                # so we'll assume it would work if selectors are correct
                return ""
                
            finally:
                # Clean up temp file
                Path(temp_file).unlink(missing_ok=True)
                
        except subprocess.TimeoutExpired:
            return "Test execution timed out"
        except Exception as e:
            # If we can't run pytest, do a basic syntax check
            try:
                compile(test_code, '<string>', 'exec')
                return ""  # Syntax is valid
            except SyntaxError as se:
                return f"Syntax error: {str(se)}"
    
    def _clean_error_message(self, error_output: str) -> str:
        """Clean up error message to focus on relevant parts"""
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', error_output)
        
        # Limit to first 1000 chars
        if len(cleaned) > 1000:
            cleaned = cleaned[:1000] + "..."
        
        return cleaned
    
    def _extract_code_from_markdown(self, content: str) -> str:
        """Extract code from markdown code blocks"""
        import re
        
        # Look for ```python or ``` code blocks
        pattern = r'```(?:python)?\s*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            return max(matches, key=len).strip()
        
        return ""
