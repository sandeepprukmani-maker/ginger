"""Simple code executor for VisionVault - executes user-provided code only."""
import asyncio
import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr


class ServerExecutor:
    """
    Simple executor that runs user-provided Playwright code.
    No AI code generation or healing - just execution.
    """
    
    def execute(self, code: str, browser: str = 'chromium', headless: bool = True) -> dict:
        """
        Execute the provided Playwright code.
        
        Args:
            code: The Playwright Python code to execute
            browser: Browser type (chromium, firefox, webkit)
            headless: Whether to run in headless mode
            
        Returns:
            dict with keys: success, logs, screenshot, current_step
        """
        result = {
            'success': False,
            'logs': [],
            'screenshot': None,
            'current_step': ''
        }
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            # Create execution namespace
            namespace = {
                '__builtins__': __builtins__,
                'browser_name': browser,
                'headless': headless
            }
            
            # Execute the code
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, namespace)
                
                # If there's a run_test function, execute it
                if 'run_test' in namespace and callable(namespace['run_test']):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            namespace['run_test'](browser, headless)
                        )
                    finally:
                        loop.close()
            
            # Capture any output
            stdout_content = stdout_capture.getvalue()
            stderr_content = stderr_capture.getvalue()
            
            if stdout_content:
                result['logs'].append(f"STDOUT: {stdout_content}")
            if stderr_content:
                result['logs'].append(f"STDERR: {stderr_content}")
            
            # If result is not a dict, assume success
            if not isinstance(result, dict):
                result = {
                    'success': True,
                    'logs': result['logs'] if 'logs' in locals() else [],
                    'screenshot': None,
                    'current_step': 'Execution completed'
                }
            
            return result
            
        except Exception as e:
            error_trace = traceback.format_exc()
            result['success'] = False
            result['logs'].append(f"ERROR: {str(e)}")
            result['logs'].append(error_trace)
            result['current_step'] = f'Failed: {str(e)}'
            
            # Capture any output before the error
            stdout_content = stdout_capture.getvalue()
            stderr_content = stderr_capture.getvalue()
            if stdout_content:
                result['logs'].insert(0, f"STDOUT: {stdout_content}")
            if stderr_content:
                result['logs'].insert(0, f"STDERR: {stderr_content}")
            
            return result
