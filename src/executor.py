import tempfile
import traceback
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from rich.console import Console

console = Console()

class PlaywrightExecutor:
    def __init__(self, headless: bool = True):
        self.headless = headless
    
    def execute(self, code: str) -> tuple[bool, dict | None]:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context()
                page = context.new_page()
                
                local_scope = {'page': page}
                
                exec(code, local_scope)
                
                if 'run_automation' in local_scope:
                    run_fn = local_scope['run_automation']
                    if callable(run_fn):
                        run_fn(page)
                else:
                    raise ValueError("Generated code must contain a 'run_automation(page)' function")
                
                page.wait_for_timeout(2000)
                
                browser.close()
                
                return True, None
                
        except PlaywrightTimeoutError as e:
            error_msg = str(e)
            failed_locator = self._extract_failed_locator(error_msg)
            
            return False, {
                'type': 'timeout',
                'message': error_msg,
                'failed_locator': failed_locator,
                'traceback': traceback.format_exc()
            }
            
        except Exception as e:
            error_msg = str(e)
            
            return False, {
                'type': 'execution_error',
                'message': error_msg,
                'failed_locator': None,
                'traceback': traceback.format_exc()
            }
    
    def _extract_failed_locator(self, error_message: str) -> str:
        lines = error_message.split('\n')
        for line in lines:
            if 'locator(' in line or 'get_by_' in line:
                return line.strip()
        
        return error_message[:200]
