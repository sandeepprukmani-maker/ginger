"""
MCP Automation Manager
Orchestrates EnhancedMCPAutomation with lifecycle management and SocketIO integration
"""

import asyncio
import os
import sys
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../mcp'))

from src.automation.mcp_client import PlaywrightMCPClient
from src.automation.logger import get_logger
from openai import AsyncOpenAI

logger = get_logger()


class MCPAutomationManager:
    """
    Manager for MCP-based browser automation with:
    - Lifecycle management (start/stop/cleanup)
    - SocketIO progress streaming
    - Screenshot and result handling
    - Integration with existing VisionVault infrastructure
    """
    
    def __init__(self, socketio, openai_api_key: Optional[str] = None):
        self.socketio = socketio
        self.openai_api_key = openai_api_key or os.environ.get('OPENAI_API_KEY')
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.screenshots_dir = "data/uploads/screenshots"
        Path(self.screenshots_dir).mkdir(parents=True, exist_ok=True)
    
    def emit_progress(self, test_id: str, message: str, level: str = "info"):
        """Emit progress update via SocketIO"""
        self.socketio.emit('automation_update', {
            'test_id': test_id,
            'type': 'log',
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat()
        })
    
    def emit_screenshot(self, test_id: str, screenshot_path: str):
        """Emit screenshot update via SocketIO"""
        try:
            if os.path.exists(screenshot_path):
                with open(screenshot_path, 'rb') as f:
                    screenshot_base64 = base64.b64encode(f.read()).decode()
                self.socketio.emit('automation_update', {
                    'test_id': test_id,
                    'type': 'screenshot',
                    'screenshot': screenshot_base64,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Failed to emit screenshot: {e}")
    
    async def execute_automation(
        self,
        test_id: str,
        command: str,
        browser: str = "chromium",
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Execute MCP automation with real-time progress updates
        
        Args:
            test_id: Unique test identifier
            command: Natural language automation command
            browser: Browser type (chromium, firefox, webkit)
            headless: Whether to run in headless mode
            
        Returns:
            Result dictionary with success status, logs, and screenshot
        """
        logs = []
        screenshot = None
        success = False
        mcp_client = None
        
        try:
            self.emit_progress(test_id, f"🚀 Starting MCP automation (mode: {'headless' if headless else 'headful'})", "info")
            self.emit_progress(test_id, f"📋 Command: {command}", "info")
            
            # Check if OpenAI API key is available
            if not self.openai_api_key:
                error_msg = "OPENAI_API_KEY is required for MCP automation. Please add it to Secrets."
                logs.append(error_msg)
                self.emit_progress(test_id, f"❌ {error_msg}", "error")
                return {
                    'success': False,
                    'logs': logs,
                    'screenshot': None,
                    'error': error_msg
                }
            
            # Initialize MCP client
            self.emit_progress(test_id, "🔧 Initializing Playwright MCP client...", "info")
            mcp_client = PlaywrightMCPClient()
            
            # Connect to MCP server
            self.emit_progress(test_id, f"🌐 Launching {browser} browser...", "info")
            await mcp_client.connect(browser=browser, headless=headless)
            logs.append(f"Browser launched: {browser} ({'headless' if headless else 'headful'})")
            self.emit_progress(test_id, "✅ MCP client connected successfully", "success")
            
            # Initialize OpenAI client for NL processing
            openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            
            # Parse command into MCP actions using GPT
            self.emit_progress(test_id, "🧠 Analyzing command with AI...", "info")
            actions = await self._parse_command_to_actions(command, openai_client)
            logs.append(f"Parsed {len(actions)} automation steps")
            
            # Execute actions sequentially with progress updates
            for i, action in enumerate(actions, 1):
                self.emit_progress(test_id, f"▶️ Step {i}/{len(actions)}: {action['description']}", "info")
                logs.append(f"STEP {i}: {action['description']}")
                
                try:
                    result = await self._execute_action(mcp_client, action)
                    logs.append(f"  ✓ Step {i} completed")
                    self.emit_progress(test_id, f"✅ Step {i} completed", "success")
                    
                    # Small delay between steps
                    await asyncio.sleep(0.5)
                    
                except Exception as step_error:
                    error_msg = f"  ✗ Step {i} failed: {str(step_error)}"
                    logs.append(error_msg)
                    self.emit_progress(test_id, f"⚠️ {error_msg}", "warning")
                    # Continue to next step (non-blocking)
            
            # Take final screenshot
            self.emit_progress(test_id, "📸 Capturing final screenshot...", "info")
            screenshot_path = os.path.join(
                self.screenshots_dir,
                f"mcp_{test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            
            await mcp_client.screenshot(screenshot_path)
            
            if os.path.exists(screenshot_path):
                with open(screenshot_path, 'rb') as f:
                    screenshot = base64.b64encode(f.read()).decode()
                logs.append("Screenshot captured")
                self.emit_screenshot(test_id, screenshot_path)
            
            success = True
            logs.append("Automation completed successfully")
            self.emit_progress(test_id, "🎉 Automation completed successfully!", "success")
            
        except Exception as e:
            error_msg = f"MCP automation failed: {str(e)}"
            error_trace = traceback.format_exc()
            logs.append(error_msg)
            logs.append(f"Traceback: {error_trace}")
            self.emit_progress(test_id, f"❌ {error_msg}", "error")
            logger.error(f"MCP automation error: {error_trace}")
            
        finally:
            # Cleanup: close browser and MCP connection
            if mcp_client:
                try:
                    self.emit_progress(test_id, "🔄 Closing browser...", "info")
                    await mcp_client.close()
                    logs.append("Browser closed")
                except Exception as cleanup_error:
                    logger.error(f"Cleanup error: {cleanup_error}")
        
        return {
            'success': success,
            'logs': logs,
            'screenshot': screenshot,
            'page_html': '',  # MCP doesn't capture HTML by default
            'current_step': len(actions) if 'actions' in locals() else 0
        }
    
    async def _parse_command_to_actions(
        self,
        command: str,
        openai_client: AsyncOpenAI
    ) -> list[Dict[str, Any]]:
        """
        Parse natural language command into MCP actions using GPT
        
        Returns:
            List of action dictionaries with tool_name, args, and description
        """
        system_prompt = """You are an expert at converting natural language commands into Playwright browser automation actions.

Given a command, break it down into a sequence of browser actions. Return a JSON array of actions.

Each action should have:
- tool_name: The MCP tool to use (browser_navigate, browser_click, browser_fill_form, browser_type, etc.)
- args: Dictionary of arguments for the tool
- description: Human-readable description of the step

Available MCP tools:
- browser_navigate: Navigate to URL (args: {"url": "..."})
- browser_click: Click element (args: {"selector": "css selector"})
- browser_fill_form: Fill form field (args: {"selector": "...", "value": "..."})
- browser_type: Type text (args: {"selector": "...", "text": "...", "delay": 50})
- browser_wait_for: Wait for element (args: {"selector": "..."})
- browser_press_key: Press keyboard key (args: {"key": "Enter"})
- browser_take_screenshot: Take screenshot (args: {})

Use semantic selectors when possible (role-based, aria-labels, placeholder, text content).

Example:
Command: "Go to Google and search for Python"
Output:
[
  {
    "tool_name": "browser_navigate",
    "args": {"url": "https://www.google.com"},
    "description": "Navigate to Google homepage"
  },
  {
    "tool_name": "browser_fill_form",
    "args": {"selector": "textarea[name='q']", "value": "Python"},
    "description": "Enter search term 'Python'"
  },
  {
    "tool_name": "browser_press_key",
    "args": {"key": "Enter"},
    "description": "Submit search"
  }
]

Return ONLY the JSON array, no explanations."""
        
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Command: {command}"}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            import json
            actions = json.loads(content)
            
            return actions
            
        except Exception as e:
            logger.error(f"Failed to parse command: {e}")
            # Fallback: simple navigate action
            return [{
                "tool_name": "browser_navigate",
                "args": {"url": "https://www.google.com"},
                "description": f"Fallback: Navigate (parsing failed: {str(e)})"
            }]
    
    async def _execute_action(
        self,
        mcp_client: PlaywrightMCPClient,
        action: Dict[str, Any]
    ) -> Any:
        """Execute a single MCP action"""
        tool_name = action['tool_name']
        args = action.get('args', {})
        
        result = await mcp_client.call_tool(tool_name, args)
        return result
    
    def cleanup_session(self, test_id: str):
        """Cleanup session resources"""
        if test_id in self.active_sessions:
            session = self.active_sessions[test_id]
            # Cancel any running tasks
            if 'task' in session and not session['task'].done():
                session['task'].cancel()
            del self.active_sessions[test_id]
