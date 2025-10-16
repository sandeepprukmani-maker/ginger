import subprocess
import json
import logging
import time
from typing import Dict, Any, Optional, List
from config import Config

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, browser: str = "chrome", headless: bool = False, device: str = ""):
        self.browser = browser
        self.headless = headless
        self.device = device
        self.process = None
        self.session_id = None
        
    def start_server(self) -> bool:
        try:
            cmd = ["npx", "@playwright/mcp@latest"]
            
            if self.browser:
                cmd.extend(["--browser", self.browser])
            
            if self.headless:
                cmd.append("--headless")
            
            if self.device:
                cmd.extend(["--device", self.device])
            
            logger.info(f"Starting MCP server with command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            time.sleep(3)
            
            if self.process.poll() is None:
                logger.info("MCP server started successfully")
                return True
            else:
                stderr = self.process.stderr.read() if self.process.stderr else ""
                logger.error(f"MCP server failed to start: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting MCP server: {str(e)}")
            return False
    
    def send_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("MCP server is not running")
        
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params
        }
        
        try:
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            response_line = self.process.stdout.readline()
            if response_line:
                response = json.loads(response_line)
                return response
            else:
                raise RuntimeError("No response from MCP server")
                
        except Exception as e:
            logger.error(f"MCP request failed: {str(e)}")
            raise
    
    def navigate(self, url: str) -> Dict[str, Any]:
        logger.info(f"MCP: Navigating to {url}")
        return self.send_mcp_request("tools/call", {
            "name": "browser_navigate",
            "arguments": {"url": url}
        })
    
    def click(self, locator: str) -> Dict[str, Any]:
        logger.info(f"MCP: Clicking element: {locator}")
        return self.send_mcp_request("tools/call", {
            "name": "page_click",
            "arguments": {"locator": locator}
        })
    
    def type_text(self, locator: str, text: str) -> Dict[str, Any]:
        logger.info(f"MCP: Typing into element: {locator}")
        return self.send_mcp_request("tools/call", {
            "name": "page_type",
            "arguments": {"locator": locator, "text": text}
        })
    
    def get_accessibility_snapshot(self) -> Dict[str, Any]:
        logger.info("MCP: Capturing accessibility snapshot")
        return self.send_mcp_request("tools/call", {
            "name": "page_snapshot",
            "arguments": {}
        })
    
    def take_screenshot(self, path: str) -> Dict[str, Any]:
        logger.info(f"MCP: Taking screenshot: {path}")
        return self.send_mcp_request("tools/call", {
            "name": "page_screenshot",
            "arguments": {"path": path}
        })
    
    def handle_alert(self, action: str = "accept", prompt_text: str = "") -> Dict[str, Any]:
        logger.info(f"MCP: Handling alert - {action}")
        params = {"action": action}
        if prompt_text:
            params["promptText"] = prompt_text
        return self.send_mcp_request("tools/call", {
            "name": "page_handle_dialog",
            "arguments": params
        })
    
    def get_alert_text(self) -> Dict[str, Any]:
        logger.info("MCP: Getting alert text")
        return self.send_mcp_request("tools/call", {
            "name": "page_dialog_message",
            "arguments": {}
        })
    
    def wait_for_new_tab(self) -> Dict[str, Any]:
        logger.info("MCP: Waiting for new tab/page")
        return self.send_mcp_request("tools/call", {
            "name": "context_wait_for_page",
            "arguments": {}
        })
    
    def switch_tab(self, index: int) -> Dict[str, Any]:
        logger.info(f"MCP: Switching to tab {index}")
        return self.send_mcp_request("tools/call", {
            "name": "page_bring_to_front",
            "arguments": {"index": index}
        })
    
    def close_tab(self, index: Optional[int] = None) -> Dict[str, Any]:
        logger.info(f"MCP: Closing tab {index if index else 'current'}")
        params = {}
        if index is not None:
            params["index"] = index
        return self.send_mcp_request("tools/call", {
            "name": "page_close",
            "arguments": params
        })
    
    def list_tabs(self) -> Dict[str, Any]:
        logger.info("MCP: Listing all tabs")
        return self.send_mcp_request("tools/call", {
            "name": "context_pages",
            "arguments": {}
        })
    
    def stop_server(self):
        if self.process:
            logger.info("Stopping MCP server")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
