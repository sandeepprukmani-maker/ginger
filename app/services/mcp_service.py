import subprocess
import json
import os
import time
import logging
from typing import Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)

class MCPServerService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.process = None
        self.browser_context = None
        self.page_url = None
        self.lock = threading.Lock()
        
    def start_server(self) -> bool:
        """Start the Microsoft Playwright MCP server"""
        try:
            with self.lock:
                if self.process and self.process.poll() is None:
                    logger.info("MCP server already running")
                    return True
                
                mcp_command = ["npx", "-y", "@playwright/mcp@latest"]
                
                browser = self.config.get('browser', 'chromium')
                if browser != 'chromium':
                    mcp_command.extend(['--browser', browser])
                
                mcp_command.append('--headless')
                
                logger.info(f"Starting MCP server with command: {' '.join(mcp_command)}")
                
                self.process = subprocess.Popen(
                    mcp_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                time.sleep(self.config.get('server_startup_timeout', 10))
                
                if self.process.poll() is not None:
                    stderr = self.process.stderr.read()
                    logger.error(f"MCP server failed to start: {stderr}")
                    return False
                
                logger.info("MCP server started successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error starting MCP server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server"""
        try:
            with self.lock:
                if self.process:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                    self.process = None
                    logger.info("MCP server stopped")
        except Exception as e:
            logger.error(f"Error stopping MCP server: {e}")
    
    def send_command(self, tool: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a command to the MCP server"""
        try:
            if not self.process or self.process.poll() is not None:
                logger.error("MCP server not running")
                return None
            
            command = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": arguments
                }
            }
            
            with self.lock:
                self.process.stdin.write(json.dumps(command) + '\n')
                self.process.stdin.flush()
                
                response_line = self.process.stdout.readline()
                if response_line:
                    response = json.loads(response_line)
                    return response
                    
            return None
            
        except Exception as e:
            logger.error(f"Error sending MCP command: {e}")
            return None
    
    def navigate(self, url: str) -> bool:
        """Navigate to a URL using MCP"""
        try:
            logger.info(f"MCP navigating to: {url}")
            result = self.send_command("browser_navigate", {"url": url})
            
            if result and not result.get('error'):
                self.page_url = url
                logger.info(f"Successfully navigated to {url}")
                return True
            else:
                error = result.get('error', {}).get('message', 'Unknown error') if result else 'No response'
                logger.error(f"Failed to navigate: {error}")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating with MCP: {e}")
            return False
    
    def click_element(self, selector: str) -> bool:
        """Click an element using MCP"""
        try:
            logger.info(f"MCP clicking element: {selector}")
            
            js_code = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.click();
                return true;
            }}
            return false;
            """
            
            result = self.send_command("browser_evaluate", {"script": js_code})
            
            if result and not result.get('error'):
                success = result.get('result', {}).get('content', [{}])[0].get('text', 'false') == 'true'
                if success:
                    logger.info(f"Successfully clicked element: {selector}")
                    return True
                else:
                    logger.warning(f"Element not found: {selector}")
                    return False
            else:
                error = result.get('error', {}).get('message', 'Unknown error') if result else 'No response'
                logger.error(f"Failed to click: {error}")
                return False
                
        except Exception as e:
            logger.error(f"Error clicking element with MCP: {e}")
            return False
    
    def fill_input(self, selector: str, value: str) -> bool:
        """Fill an input field using MCP"""
        try:
            logger.info(f"MCP filling input: {selector} with value: {value}")
            
            js_code = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.value = '{value}';
                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
            """
            
            result = self.send_command("browser_evaluate", {"script": js_code})
            
            if result and not result.get('error'):
                success = result.get('result', {}).get('content', [{}])[0].get('text', 'false') == 'true'
                if success:
                    logger.info(f"Successfully filled input: {selector}")
                    return True
                else:
                    logger.warning(f"Input element not found: {selector}")
                    return False
            else:
                error = result.get('error', {}).get('message', 'Unknown error') if result else 'No response'
                logger.error(f"Failed to fill input: {error}")
                return False
                
        except Exception as e:
            logger.error(f"Error filling input with MCP: {e}")
            return False
    
    def get_element_locator(self, description: str, page_content: str = None) -> Optional[str]:
        """Generate a CSS selector for an element based on description using MCP"""
        try:
            logger.info(f"MCP generating locator for: {description}")
            
            js_code = f"""
            // Try to find element by common patterns
            let selector = null;
            const desc = '{description}'.toLowerCase();
            
            // Try by text content
            const elements = Array.from(document.querySelectorAll('button, a, input, label, h1, h2, h3, h4, h5, h6, span, div'));
            for (const el of elements) {{
                const text = el.textContent.toLowerCase().trim();
                if (text.includes(desc) || desc.includes(text)) {{
                    // Generate unique selector
                    if (el.id) {{
                        selector = '#' + el.id;
                        break;
                    }}
                    if (el.className) {{
                        const classes = Array.from(el.classList).join('.');
                        selector = el.tagName.toLowerCase() + '.' + classes;
                        if (document.querySelectorAll(selector).length === 1) {{
                            break;
                        }}
                    }}
                    selector = el.tagName.toLowerCase();
                }}
            }}
            
            // Try by placeholder
            if (!selector) {{
                const input = document.querySelector(`input[placeholder*="${{desc}}"]`);
                if (input) {{
                    if (input.id) selector = '#' + input.id;
                    else if (input.name) selector = `input[name="${{input.name}}"]`;
                    else selector = `input[placeholder="${{input.placeholder}}"]`;
                }}
            }}
            
            // Try by aria-label
            if (!selector) {{
                const ariaEl = document.querySelector(`[aria-label*="${{desc}}"]`);
                if (ariaEl && ariaEl.id) selector = '#' + ariaEl.id;
            }}
            
            selector || 'NONE';
            """
            
            result = self.send_command("browser_evaluate", {"script": js_code})
            
            if result and not result.get('error'):
                selector = result.get('result', {}).get('content', [{}])[0].get('text', 'NONE')
                if selector != 'NONE':
                    logger.info(f"Generated locator: {selector} for description: {description}")
                    return selector
                else:
                    logger.warning(f"Could not generate locator for: {description}")
                    return None
            else:
                error = result.get('error', {}).get('message', 'Unknown error') if result else 'No response'
                logger.error(f"Failed to generate locator: {error}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating locator with MCP: {e}")
            return None
    
    def wait_for_element(self, selector: str, timeout: int = 30) -> bool:
        """Wait for an element to appear"""
        try:
            logger.info(f"MCP waiting for element: {selector}")
            
            js_code = f"""
            new Promise((resolve) => {{
                const checkExist = setInterval(() => {{
                    if (document.querySelector('{selector}')) {{
                        clearInterval(checkExist);
                        resolve(true);
                    }}
                }}, 100);
                
                setTimeout(() => {{
                    clearInterval(checkExist);
                    resolve(false);
                }}, {timeout * 1000});
            }});
            """
            
            result = self.send_command("browser_evaluate", {"script": js_code})
            
            if result and not result.get('error'):
                success = result.get('result', {}).get('content', [{}])[0].get('text', 'false') == 'true'
                if success:
                    logger.info(f"Element appeared: {selector}")
                    return True
                else:
                    logger.warning(f"Element did not appear within timeout: {selector}")
                    return False
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error waiting for element with MCP: {e}")
            return False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_server()
