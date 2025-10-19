"""
Hybrid Code Generator
Converts MCP execution traces into reliable Playwright code.
Uses actual working selectors discovered by MCP instead of LLM guessing.
"""

from typing import List, Dict, Any, Optional
import re


class HybridCodeGenerator:
    """
    Generates Playwright code from MCP execution traces.
    Uses proven selectors that actually worked during MCP execution.
    """
    
    def __init__(self):
        self.indentation = "    "
        
    def generate_code(self, traces: List[Dict[str, Any]], browser: str = 'chromium', 
                     headless: bool = True) -> str:
        """
        Generate Playwright code from execution traces.
        
        Args:
            traces: List of execution trace dictionaries
            browser: Browser type
            headless: Whether to run headless
            
        Returns:
            Complete Playwright Python code
        """
        code_lines = self._generate_header(browser, headless)
        
        # Filter successful traces only
        successful_traces = [t for t in traces if t.get('success', False)]
        
        if not successful_traces:
            return self._generate_empty_code()
        
        # Generate code for each action
        for trace in successful_traces:
            action_code = self._generate_action_code(trace)
            if action_code:
                code_lines.extend(action_code)
        
        # Add screenshot at the end
        code_lines.append(f"{self.indentation}# Take final screenshot")
        code_lines.append(f"{self.indentation}page.screenshot(path='final_result.png')")
        code_lines.append("")
        
        # Add footer
        code_lines.extend(self._generate_footer())
        
        return "\n".join(code_lines)
    
    def _generate_header(self, browser: str, headless: bool) -> List[str]:
        """Generate code header with imports and setup"""
        return [
            "from playwright.sync_api import sync_playwright, expect",
            "import time",
            "",
            "def run():",
            f"{self.indentation}with sync_playwright() as p:",
            f"{self.indentation}{self.indentation}# Launch browser",
            f"{self.indentation}{self.indentation}browser = p.{browser}.launch(headless={headless})",
            f"{self.indentation}{self.indentation}context = browser.new_context()",
            f"{self.indentation}{self.indentation}page = context.new_page()",
            f"{self.indentation}{self.indentation}",
            f"{self.indentation}{self.indentation}try:",
        ]
    
    def _generate_footer(self) -> List[str]:
        """Generate code footer with cleanup"""
        return [
            f"{self.indentation}{self.indentation}except Exception as e:",
            f"{self.indentation}{self.indentation}{self.indentation}print(f'Error: {{e}}')",
            f"{self.indentation}{self.indentation}{self.indentation}page.screenshot(path='error.png')",
            f"{self.indentation}{self.indentation}{self.indentation}raise",
            f"{self.indentation}{self.indentation}finally:",
            f"{self.indentation}{self.indentation}{self.indentation}# Cleanup",
            f"{self.indentation}{self.indentation}{self.indentation}context.close()",
            f"{self.indentation}{self.indentation}{self.indentation}browser.close()",
            "",
            "if __name__ == '__main__':",
            f"{self.indentation}run()",
        ]
    
    def _generate_empty_code(self) -> str:
        """Generate placeholder code when no successful traces"""
        return "# No successful actions to generate code from\npass"
    
    def _generate_action_code(self, trace: Dict[str, Any]) -> List[str]:
        """Generate code for a single action based on trace"""
        action_type = trace.get('action_type', '')
        tool_name = trace.get('tool_name', '')
        args = trace.get('arguments', {})
        indent = f"{self.indentation}{self.indentation}{self.indentation}"
        
        lines = []
        
        # Navigate
        if action_type == 'navigate':
            url = args.get('url', '')
            lines.append(f"{indent}# Navigate to {url}")
            lines.append(f"{indent}page.goto('{url}')")
            lines.append(f"{indent}page.wait_for_load_state('networkidle')")
            lines.append("")
        
        # Click
        elif action_type == 'click':
            selector = self._escape_selector(args.get('selector', ''))
            comment = self._generate_comment_from_selector(selector, 'click')
            lines.append(f"{indent}# {comment}")
            lines.append(f"{indent}page.locator(\"{selector}\").click()")
            lines.append(f"{indent}time.sleep(0.5)  # Wait for action to complete")
            lines.append("")
        
        # Fill form
        elif action_type == 'fill':
            selector = self._escape_selector(args.get('selector', ''))
            value = args.get('value', '')
            comment = self._generate_comment_from_selector(selector, f'fill with "{value}"')
            lines.append(f"{indent}# {comment}")
            lines.append(f"{indent}page.locator(\"{selector}\").fill('{value}')")
            lines.append("")
        
        # Type text
        elif action_type == 'type':
            selector = self._escape_selector(args.get('selector', ''))
            text = args.get('text', '')
            delay = args.get('delay', 50)
            comment = self._generate_comment_from_selector(selector, f'type "{text}"')
            lines.append(f"{indent}# {comment}")
            lines.append(f"{indent}page.locator(\"{selector}\").type('{text}', delay={delay})")
            lines.append("")
        
        # Select dropdown
        elif action_type == 'select':
            selector = self._escape_selector(args.get('selector', ''))
            value = args.get('value', '')
            comment = self._generate_comment_from_selector(selector, f'select "{value}"')
            lines.append(f"{indent}# {comment}")
            lines.append(f"{indent}page.locator(\"{selector}\").select_option('{value}')")
            lines.append("")
        
        # Wait for element
        elif action_type == 'wait':
            selector = self._escape_selector(args.get('selector', ''))
            timeout = args.get('timeout', 30000)
            comment = self._generate_comment_from_selector(selector, 'wait for')
            lines.append(f"{indent}# {comment}")
            lines.append(f"{indent}page.wait_for_selector(\"{selector}\", timeout={timeout})")
            lines.append("")
        
        # Assertions
        elif action_type == 'assert':
            assertion_code = self._generate_assertion_code(trace, indent)
            if assertion_code:
                lines.extend(assertion_code)
        
        return lines
    
    def _generate_assertion_code(self, trace: Dict[str, Any], indent: str) -> List[str]:
        """Generate assertion code from trace"""
        details = trace.get('arguments', {})
        assertion_type = trace.get('tool_name', '').replace('assertion_', '')
        
        lines = []
        
        # URL assertion
        if assertion_type == 'url_contains':
            expected = details.get('expected', '')
            lines.append(f"{indent}# Verify URL contains '{expected}'")
            lines.append(f"{indent}assert '{expected}' in page.url, f'Expected URL to contain {{expected}}, got {{page.url}}'")
            lines.append("")
        
        # Text assertion
        elif assertion_type == 'text_visible':
            text = details.get('text', '')
            lines.append(f"{indent}# Verify text '{text}' is visible")
            lines.append(f"{indent}expect(page.get_by_text('{text}')).to_be_visible()")
            lines.append("")
        
        # Element visible
        elif assertion_type == 'element_visible':
            selector = self._escape_selector(details.get('selector', ''))
            lines.append(f"{indent}# Verify element is visible")
            lines.append(f"{indent}expect(page.locator(\"{selector}\")).to_be_visible()")
            lines.append("")
        
        return lines
    
    def _escape_selector(self, selector: str) -> str:
        """Escape selector for Python string"""
        # Handle double quotes in selector
        return selector.replace('"', '\\"')
    
    def _generate_comment_from_selector(self, selector: str, action: str) -> str:
        """Generate human-readable comment from selector"""
        # Extract meaningful parts from selector
        if 'get_by_role' in selector:
            return f"Action: {action} on element (role-based)"
        elif 'get_by_text' in selector:
            match = re.search(r"get_by_text\(['\"]([^'\"]+)['\"]\)", selector)
            if match:
                return f"Action: {action} on '{match.group(1)}'"
        elif 'get_by_placeholder' in selector:
            match = re.search(r"get_by_placeholder\(['\"]([^'\"]+)['\"]\)", selector)
            if match:
                return f"Action: {action} on field with placeholder '{match.group(1)}'"
        elif '#' in selector:
            match = re.search(r'#([\w-]+)', selector)
            if match:
                return f"Action: {action} on element with id '{match.group(1)}'"
        
        return f"Action: {action}"
    
    def generate_from_summary(self, trace_summary: Dict[str, Any], browser: str = 'chromium',
                              headless: bool = True) -> str:
        """
        Generate code from trace summary dictionary.
        This is a convenience method that extracts traces from the summary.
        """
        traces = trace_summary.get('traces', [])
        return self.generate_code(traces, browser, headless)
