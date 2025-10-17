#!/usr/bin/env python3
"""
Enhanced Natural Language Browser Automation using Playwright MCP Server
Features: Vision-based intelligence, smart error recovery, session memory, advanced web handling
"""

import asyncio
import json
import sys
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.automation.mcp_client import PlaywrightMCPClient
from src.automation.logger import get_logger
from src.automation.vision_analyzer import VisionAnalyzer
from src.automation.session_memory import SessionMemory
from openai import AsyncOpenAI

logger = get_logger()


class EnhancedMCPAutomation:
    """Enhanced natural language automation with vision, memory, and intelligent error recovery."""
    
    def __init__(self, api_key: str, enable_vision: bool = True, max_retries: int = 3, screenshots_dir: str = "screenshots"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.mcp = PlaywrightMCPClient()
        self.conversation_history = []
        self.enable_vision = enable_vision
        self.vision_analyzer = VisionAnalyzer(api_key) if enable_vision else None
        self.session_memory = SessionMemory()
        self.max_retries = max_retries
        self.screenshot_count = 0
        self.screenshots_dir = screenshots_dir
    
    async def initialize(self, browser: str = "chromium", headless: bool = True):
        """Initialize MCP connection."""
        # Create screenshots folder if it doesn't exist
        Path(self.screenshots_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created screenshots folder: {self.screenshots_dir}")
        
        await self.mcp.connect(browser=browser, headless=headless)
        logger.success("Enhanced MCP automation initialized with vision and memory!")
    
    async def _take_screenshot(self, context: str = "debug") -> Optional[str]:
        """Take a screenshot and return base64 encoded image."""
        try:
            self.screenshot_count += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"screenshots/mcp_{context}_{timestamp}_{self.screenshot_count}.png"
            
            result = await self.mcp.call_tool("browser_take_screenshot", {"path": screenshot_path})
            
            if Path(screenshot_path).exists():
                with open(screenshot_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            return None
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None
    
    async def _analyze_page_with_vision(self, instruction: str) -> Optional[Dict[str, Any]]:
        """Use vision to analyze the page and get better selectors."""
        if not self.vision_analyzer:
            return None
        
        try:
            screenshot_b64 = await self._take_screenshot("vision_analysis")
            if not screenshot_b64:
                return None
            
            analysis = await self.vision_analyzer.analyze_page(screenshot_b64, instruction)
            logger.info(f"Vision analysis: {analysis}")
            return analysis
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return None
    
    async def _get_page_context(self) -> str:
        """Get current page context for better decision making."""
        try:
            snapshot = await self.mcp.call_tool("browser_snapshot", {})
            if isinstance(snapshot, str):
                return snapshot[:2000]  # Smaller limit for speed
            return ""
        except Exception as e:
            logger.debug(f"Failed to get page context: {e}")
            return ""
    
    async def _get_page_elements_catalog(self) -> Dict[str, List[Dict[str, str]]]:
        """Get catalog of interactive elements on the page for smart retries."""
        try:
            js_code = """
            (function() {
                const elements = {
                    buttons: [],
                    links: [],
                    inputs: [],
                    selects: []
                };
                
                // Catalog buttons
                document.querySelectorAll('button, input[type="submit"], input[type="button"]').forEach(el => {
                    elements.buttons.push({
                        text: (el.innerText || el.value || '').trim().substring(0, 50),
                        id: el.id || '',
                        ariaLabel: el.getAttribute('aria-label') || '',
                        type: el.type || 'button'
                    });
                });
                
                // Catalog links
                document.querySelectorAll('a[href]').forEach(el => {
                    elements.links.push({
                        text: (el.innerText || '').trim().substring(0, 50),
                        href: el.href || '',
                        id: el.id || '',
                        ariaLabel: el.getAttribute('aria-label') || ''
                    });
                });
                
                // Catalog inputs
                document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="search"], textarea').forEach(el => {
                    elements.inputs.push({
                        type: el.type || 'text',
                        placeholder: el.placeholder || '',
                        name: el.name || '',
                        id: el.id || '',
                        ariaLabel: el.getAttribute('aria-label') || ''
                    });
                });
                
                // Catalog selects
                document.querySelectorAll('select').forEach(el => {
                    elements.selects.push({
                        name: el.name || '',
                        id: el.id || '',
                        ariaLabel: el.getAttribute('aria-label') || ''
                    });
                });
                
                return elements;
            })()
            """
            result = await self.mcp.evaluate(js_code)
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.debug(f"Could not get elements catalog: {e}")
            return {}
    
    async def _smart_retry_with_vision(self, tool_name: str, tool_args: Dict[str, Any], error: str, instruction: str, is_final_retry: bool = False) -> Any:
        """Retry failed action with vision-based correction and intelligent catalog matching."""
        logger.info(f"Attempting smart retry for {tool_name} using element catalog...")
        
        # Strategy 1: Vision-based selector correction (ONLY ON FINAL RETRY for speed)
        vision_analysis = None
        if is_final_retry and self.enable_vision:
            logger.info("Final retry - using vision analysis...")
            vision_analysis = await self._analyze_page_with_vision(instruction)
        
        if vision_analysis and vision_analysis.get("suggested_selector"):
            new_selector = vision_analysis["suggested_selector"]
            logger.info(f"Vision suggests selector: {new_selector}")
            
            if "selector" in tool_args:
                tool_args["selector"] = new_selector
                try:
                    return await self.mcp.call_tool(tool_name, tool_args)
                except Exception as e:
                    logger.debug(f"Vision selector failed: {e}")
        
        # Strategy 2: Use element catalog based on TOOL TYPE
        elements_catalog = await self._get_page_elements_catalog()
        original_selector = tool_args.get("selector", "")
        
        # Extract keywords from both instruction and original selector
        search_keywords = set(instruction.lower().split() + original_selector.lower().split())
        
        # Determine element type from tool name
        if tool_name in ["browser_click"]:
            # Try buttons first, then links
            logger.info("Retrying click action - searching buttons and links")
            
            for btn in elements_catalog.get("buttons", []):
                if btn.get("text") and any(word in btn["text"].lower() for word in search_keywords):
                    selectors = [f"text={btn['text']}", f"role=button[name=/{btn['text']}/i]"]
                    if btn.get("id"):
                        selectors.append(f"#{btn['id']}")
                    
                    for sel in selectors:
                        tool_args["selector"] = sel
                        try:
                            logger.info(f"Trying button selector: {sel}")
                            return await self.mcp.call_tool(tool_name, tool_args)
                        except:
                            continue
            
            for link in elements_catalog.get("links", []):
                if link.get("text") and any(word in link["text"].lower() for word in search_keywords):
                    selectors = [f"text={link['text']}", f"role=link[name=/{link['text']}/i]"]
                    if link.get("id"):
                        selectors.append(f"#{link['id']}")
                    
                    for sel in selectors:
                        tool_args["selector"] = sel
                        try:
                            logger.info(f"Trying link selector: {sel}")
                            return await self.mcp.call_tool(tool_name, tool_args)
                        except:
                            continue
        
        elif tool_name in ["browser_type", "browser_fill_form"]:
            # Looking for input fields
            logger.info("Retrying fill/type action - searching inputs")
            
            for inp in elements_catalog.get("inputs", []):
                selectors = []
                # Match by placeholder, name, or keywords
                if inp.get("placeholder") and any(word in inp["placeholder"].lower() for word in search_keywords):
                    selectors.append(f"[placeholder*='{inp['placeholder']}']")
                if inp.get("name"):
                    selectors.append(f"[name='{inp['name']}']")
                    # Also try text matching on name
                    if any(word in inp["name"].lower() for word in search_keywords):
                        selectors.insert(0, f"[name='{inp['name']}']")
                if inp.get("id"):
                    selectors.append(f"#{inp['id']}")
                if inp.get("ariaLabel") and any(word in inp["ariaLabel"].lower() for word in search_keywords):
                    selectors.insert(0, f"[aria-label='{inp['ariaLabel']}']")
                
                for sel in selectors:
                    tool_args["selector"] = sel
                    try:
                        logger.info(f"Trying input selector: {sel}")
                        return await self.mcp.call_tool(tool_name, tool_args)
                    except:
                        continue
        
        elif tool_name in ["browser_select_option"]:
            # Looking for select elements
            logger.info("Retrying select action - searching selects")
            
            for sel_elem in elements_catalog.get("selects", []):
                selectors = []
                if sel_elem.get("name"):
                    selectors.append(f"[name='{sel_elem['name']}']")
                if sel_elem.get("id"):
                    selectors.append(f"#{sel_elem['id']}")
                if sel_elem.get("ariaLabel"):
                    selectors.append(f"[aria-label='{sel_elem['ariaLabel']}']")
                
                for sel in selectors:
                    tool_args["selector"] = sel
                    try:
                        logger.info(f"Trying select selector: {sel}")
                        return await self.mcp.call_tool(tool_name, tool_args)
                    except:
                        continue
        
        else:
            # For other tools, try generic matching
            logger.info(f"Retrying {tool_name} - trying generic element matching")
            all_elements = (
                elements_catalog.get("buttons", []) + 
                elements_catalog.get("links", []) + 
                elements_catalog.get("inputs", [])
            )
            
            for elem in all_elements:
                if elem.get("id") and any(word in elem["id"].lower() for word in search_keywords):
                    tool_args["selector"] = f"#{elem['id']}"
                    try:
                        return await self.mcp.call_tool(tool_name, tool_args)
                    except:
                        continue
        
        raise Exception(f"All vision and element catalog strategies exhausted for {tool_name}")
    
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a natural language command using AI + MCP with enhanced capabilities.
        
        Args:
            command: Natural language instruction
            
        Returns:
            Dict with status, summary, and continuation info
        """
        logger.info(f"Processing command: {command}")
        
        # Check session memory for similar successful patterns
        similar_patterns = self.session_memory.get_similar_patterns(command)
        memory_context = self.session_memory.get_context_for_instruction(command)
        if similar_patterns:
            logger.info(f"Found {len(similar_patterns)} similar patterns from memory")
        
        # Get page context for better decisions
        page_context = await self._get_page_context()
        
        # Get available MCP tools
        tools = self.mcp.get_available_tools()
        
        # Format tools for OpenAI
        openai_tools: list = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            }
            for tool in tools
        ]
        
        # Enhanced system prompt with context
        system_prompt = f"""You are an advanced browser automation assistant using Playwright MCP tools.

CAPABILITIES:
- 21+ Playwright MCP tools for comprehensive browser control
- Vision-based page analysis for difficult elements
- Smart element detection with multiple fallback strategies
- Session memory to learn from past successes
- Handles complex scenarios: forms, tables, dynamic content, iframes, popups

STRATEGY:
1. Break complex tasks into logical steps
2. Use browser_snapshot first to understand page structure
3. For element interactions, try multiple selector strategies:
   - CSS selectors (.class, #id)
   - Text selectors (text=Login)
   - Role selectors (role=button)
   - Placeholder/label selectors
4. For data extraction, use browser_evaluate with JavaScript
5. Wait for elements with browser_wait_for when needed
6. Handle forms with browser_fill_form for efficiency
7. Screenshots are automatically saved to screenshots/ folder with unique timestamped names

CURRENT PAGE CONTEXT:
{page_context[:500] if page_context else 'No context available'}

MEMORY:
{memory_context if memory_context else 'No similar patterns found'}

Execute the user's command intelligently, adapting to any website structure."""

        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": command
        })
        
        # Call OpenAI to determine which tools to use
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *self.conversation_history
            ],
            tools=openai_tools,
            tool_choice="required",  # Force AI to use tools instead of returning text
            temperature=0.3  # Lower temperature for more consistent automation
        )
        
        message = response.choices[0].message
        results = []
        tool_execution_log = []
        
        # Check if AI returned tool calls (should always be true with tool_choice="required")
        if not message.tool_calls:
            error_msg = f"AI did not return tool calls. Response: {message.content}"
            logger.error(error_msg)
            self.session_memory.record_execution(
                instruction=command,
                success=False,
                steps=[],
                error=error_msg
            )
            return {
                "status": "error",
                "summary": "AI failed to generate tool calls",
                "should_continue": False
            }
        
        # Execute tool calls with smart retry
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if hasattr(tool_call, 'function'):
                    tool_name = tool_call.function.name  # type: ignore
                    try:
                        tool_args = json.loads(tool_call.function.arguments)  # type: ignore
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse tool arguments: {e}")
                        continue
                else:
                    continue
                
                logger.info(f"⚡ Executing: {tool_name}({tool_args})")
                
                # Ensure screenshots go to screenshots folder with unique names
                if tool_name == "browser_take_screenshot":
                    self.screenshot_count += 1
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = tool_args.get("filename", f"screenshot_{timestamp}_{self.screenshot_count}.png")
                    # Ensure it's saved in screenshots folder
                    if not filename.startswith(f"{self.screenshots_dir}/"):
                        filename = f"{self.screenshots_dir}/{filename}"
                    tool_args["path"] = filename
                    logger.info(f"Screenshot will be saved to: {filename}")
                
                # Try executing with retries
                retry_count = 0
                while retry_count < self.max_retries:
                    try:
                        result = await self.mcp.call_tool(tool_name, tool_args)
                        logger.success(f"✓ {tool_name} succeeded")
                        results.append(f"✓ {tool_name}: {result}")
                        
                        # Log successful execution
                        tool_execution_log.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "success": True
                        })
                        
                        # Add tool result to conversation
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [tool_call]
                        })
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result)
                        })
                        
                        # Auto-refresh DOM context after navigation
                        if tool_name in ["browser_navigate", "browser_navigate_back", "browser_navigate_forward"]:
                            await asyncio.sleep(0.3)  # Quick wait for page load
                            fresh_context = await self._get_page_context()
                            if fresh_context:
                                logger.info(f"📊 Refreshed DOM context after navigation")
                                # Update conversation with fresh context (smaller for speed)
                                self.conversation_history.append({
                                    "role": "system",
                                    "content": f"Page context updated: {fresh_context[:300]}"
                                })
                        
                        # Inform AI about screenshot location
                        if tool_name == "browser_take_screenshot":
                            screenshot_path = tool_args.get("path", "unknown")
                            self.conversation_history.append({
                                "role": "system",
                                "content": f"Screenshot saved to: {screenshot_path}"
                            })
                            logger.success(f"📸 Screenshot saved to: {screenshot_path}")
                        
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        retry_count += 1
                        error_msg = f"✗ {tool_name} failed (attempt {retry_count}/{self.max_retries}): {e}"
                        logger.warning(error_msg)
                        
                        if retry_count < self.max_retries:
                            # Try smart retry (vision only on final retry for speed)
                            try:
                                is_final = (retry_count == self.max_retries - 1)
                                result = await self._smart_retry_with_vision(tool_name, tool_args.copy(), str(e), command, is_final)
                                results.append(f"✓ {tool_name} (retry): {result}")
                                
                                # Log successful retry
                                tool_execution_log.append({
                                    "tool": tool_name,
                                    "args": tool_args,
                                    "success": True,
                                    "retry": True
                                })
                                
                                break
                            except Exception as retry_error:
                                if retry_count == self.max_retries - 1:
                                    results.append(error_msg)
                                    tool_execution_log.append({
                                        "tool": tool_name,
                                        "args": tool_args,
                                        "success": False,
                                        "error": str(retry_error)
                                    })
                        else:
                            results.append(error_msg)
                            tool_execution_log.append({
                                "tool": tool_name,
                                "args": tool_args,
                                "success": False,
                                "error": str(e)
                            })
        
        # Generate Playwright code from successful executions
        playwright_code = self._generate_playwright_code(tool_execution_log, command)
        
        # Save execution to memory
        success = any(log["success"] for log in tool_execution_log)
        error_msg = None
        if not success:
            failed_logs = [log for log in tool_execution_log if not log["success"]]
            if failed_logs:
                error_msg = failed_logs[0].get("error", "Unknown error")
        
        self.session_memory.record_execution(
            instruction=command,
            success=success,
            steps=tool_execution_log,
            error=error_msg
        )
        
        # Determine if we need to continue autonomously or ask user
        if results:
            # Ask AI if task is complete or needs more steps
            decision_response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Analyze the ORIGINAL user request against what has been accomplished so far.

ORIGINAL REQUEST: "{command}"

Compare this against the conversation history to determine if ALL parts of the request are complete.

Respond with JSON:
{{
  "status": "complete" | "continue",
  "summary": "brief summary of current progress",
  "next_action": "specific next command to execute (required if status is continue)"
}}

Rules:
- Use "continue" if ANY part of the original request is incomplete
- Use "complete" ONLY when every part of the request is fully done
- When continuing, next_action must be a specific command, not a description
- Execute ALL steps of the request autonomously without asking user

Examples:
- Request: "open google and search for dogs" → Opened Google → status: "continue", next_action: "search for dogs"
- Request: "navigate to github.com and take screenshot" → Navigated → status: "continue", next_action: "take screenshot"  
- Request: "search for cars" → Already searched and on results → status: "complete"

DO NOT ask the user to continue - execute next steps autonomously."""
                    },
                    *self.conversation_history
                ],
                response_format={"type": "json_object"}
            )
            
            try:
                decision = json.loads(decision_response.choices[0].message.content or "{}")
                status = decision.get("status", "complete")
                summary = decision.get("summary", "Task completed")
                next_action = decision.get("next_action")
                
                logger.success(f"Status: {status} - {summary}")
                
                # Return result with continuation info and Playwright code
                return {
                    "status": status,
                    "summary": summary,
                    "next_action": next_action,
                    "should_continue": status == "continue",
                    "playwright_code": playwright_code
                }
            except:
                # Fallback to simple summary
                return {
                    "status": "complete",
                    "summary": "Task completed",
                    "should_continue": False,
                    "playwright_code": playwright_code
                }
        else:
            # This should never happen with tool_choice="required"
            logger.warning("No tool calls executed (should not happen)")
            return {
                "status": "error", 
                "summary": "No actions executed",
                "should_continue": False,
                "playwright_code": None
            }
    
    def _generate_playwright_code(self, tool_execution_log: List[Dict[str, Any]], instruction: str) -> Optional[str]:
        """Generate Playwright Python code from successful tool executions."""
        successful_steps = [step for step in tool_execution_log if step.get("success")]
        
        if not successful_steps:
            return None
        
        code_lines = [
            "# Generated Playwright code",
            f"# Original instruction: {instruction}",
            "",
            "from playwright.async_api import async_playwright",
            "",
            "async def run():",
            "    async with async_playwright() as p:",
            "        browser = await p.chromium.launch(headless=True)",
            "        page = await browser.new_page()",
            ""
        ]
        
        for step in successful_steps:
            tool = step.get("tool", "")
            args = step.get("args", {})
            
            if tool == "browser_navigate":
                url = args.get("url", "")
                code_lines.append(f"        # Navigate to {url}")
                code_lines.append(f"        await page.goto('{url}')")
                
            elif tool == "browser_click":
                selector = args.get("selector", "")
                code_lines.append(f"        # Click element")
                code_lines.append(f"        await page.locator('{selector}').click()")
                
            elif tool == "browser_type":
                selector = args.get("selector", "")
                text = args.get("text", "")
                code_lines.append(f"        # Type text into element")
                code_lines.append(f"        await page.locator('{selector}').fill('{text}')")
                
            elif tool == "browser_fill_form":
                form_data = args.get("formData", {})
                code_lines.append(f"        # Fill form")
                for field_selector, value in form_data.items():
                    code_lines.append(f"        await page.locator('{field_selector}').fill('{value}')")
                    
            elif tool == "browser_press_key":
                key = args.get("key", "")
                code_lines.append(f"        # Press key: {key}")
                code_lines.append(f"        await page.keyboard.press('{key}')")
                
            elif tool == "browser_take_screenshot":
                path = args.get("path", "screenshot.png")
                code_lines.append(f"        # Take screenshot")
                code_lines.append(f"        await page.screenshot(path='{path}')")
                
            elif tool == "browser_evaluate":
                script = args.get("script", "")
                code_lines.append(f"        # Execute JavaScript")
                code_lines.append(f"        result = await page.evaluate('''{script}''')")
                
            elif tool == "browser_wait_for":
                selector = args.get("selector", "")
                code_lines.append(f"        # Wait for element")
                code_lines.append(f"        await page.locator('{selector}').wait_for()")
                
            elif tool == "browser_select_option":
                selector = args.get("selector", "")
                value = args.get("value", "")
                code_lines.append(f"        # Select dropdown option")
                code_lines.append(f"        await page.locator('{selector}').select_option('{value}')")
                
            elif tool == "browser_hover":
                selector = args.get("selector", "")
                code_lines.append(f"        # Hover over element")
                code_lines.append(f"        await page.locator('{selector}').hover()")
            
            code_lines.append("")
        
        code_lines.extend([
            "        await browser.close()",
            "",
            "if __name__ == '__main__':",
            "    import asyncio",
            "    asyncio.run(run())"
        ])
        
        return "\n".join(code_lines)
    
    async def cleanup(self):
        """Clean up resources."""
        await self.mcp.close()
        logger.info("MCP automation cleaned up successfully")


async def main():
    """Main entry point for enhanced MCP automation."""
    from src.automation.config_loader import get_config
    
    # Load configuration from config.ini
    config = get_config()
    
    # Get OpenAI API key from config
    api_key = config.openai_api_key
    if not api_key:
        logger.error("OPENAI_API_KEY not set in config.ini or environment!")
        logger.error("Please set it in config.ini or as an environment variable")
        sys.exit(1)
    
    # Display configuration banner
    print("\n" + "="*70)
    print("🚀 ENHANCED Playwright MCP Natural Language Automation")
    print("="*70)
    print("\nConfiguration:")
    print(f"  • Config file: config.ini")
    print(f"  • AI Model: {config.openai_model}")
    print(f"  • Browser: {config.browser_type} (headless: {config.browser_headless})")
    print(f"  • Vision: {'Enabled' if config.enable_vision else 'Disabled'}")
    print(f"  • Screenshots: {config.screenshots_dir}/")
    print(f"  • Max Retries: {config.max_retries}")
    print("\nFeatures:")
    print("  ✓ Vision-based intelligent page analysis")
    print("  ✓ Smart error recovery with automatic retries")
    print("  ✓ Session memory learns from successful patterns")
    print("  ✓ Advanced web handling (forms, tables, iframes, dynamic content)")
    print("  ✓ Multi-strategy element detection")
    print("  ✓ Auto-refresh DOM context after navigation")
    print("  ✓ Autonomous multi-step execution without interruptions")
    print(f"  ✓ Screenshots automatically saved to {config.screenshots_dir}/ folder")
    print("="*70)
    
    # Create automation instance with config settings
    automation = EnhancedMCPAutomation(
        api_key=api_key,
        enable_vision=config.enable_vision,
        max_retries=config.max_retries,
        screenshots_dir=config.screenshots_dir
    )
    
    try:
        # Initialize MCP
        logger.info("Initializing Enhanced Playwright MCP server...")
        await automation.initialize(
            browser=config.browser_type,
            headless=config.browser_headless
        )
        
        print("\n" + "="*70)
        print("💡 POWERFUL AUTOMATION EXAMPLES:")
        print("="*70)
        print("\n🌐 Navigation & Search:")
        print("  • Go to google.com and search for Python tutorials")
        print("  • Navigate to news.ycombinator.com and get top 5 stories")
        print("  • Visit github.com and click on the trending repositories")
        
        print("\n📝 Forms & Data Entry:")
        print("  • Fill out the contact form with name John and email john@example.com")
        print("  • Search for apartments in New York on realtor.com")
        print("  • Login with username testuser and password testpass")
        
        print("\n📊 Data Extraction:")
        print("  • Extract all product names and prices from this page")
        print("  • Get all the article headlines from this news site")
        print("  • Scrape the table data and export it")
        
        print("\n🔧 Complex Tasks:")
        print("  • Take a screenshot of the current page")
        print("  • Click all 'Accept' buttons on this page")
        print("  • Navigate through the pagination and collect all items")
        
        print("\n" + "="*70)
        print("Type 'quit', 'exit', or 'q' to stop.\n")
        
        # Interactive mode with autonomous continuation
        while True:
            try:
                command = input("💬 Command: ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if not command:
                    continue
                
                # Execute command and check if we should continue autonomously
                while True:
                    result = await automation.execute_command(command)
                    
                    # Handle result (could be string or dict)
                    if isinstance(result, dict):
                        summary = result.get("summary", "")
                        should_continue = result.get("should_continue", False)
                        next_action = result.get("next_action")
                        playwright_code = result.get("playwright_code")
                        
                        # Show progress without interrupting
                        if should_continue and next_action:
                            print(f"  ⚡ {summary}")
                            command = next_action  # Continue with next action
                            await asyncio.sleep(0.5)  # Brief pause
                        else:
                            print(f"\n✅ {summary}\n")
                            
                            # Display generated Playwright code
                            if playwright_code:
                                print("=" * 70)
                                print("📝 GENERATED PLAYWRIGHT CODE (with working locators):")
                                print("=" * 70)
                                print(playwright_code)
                                print("=" * 70)
                                print()
                            
                            break
                    else:
                        print(f"\n✅ {result}\n")
                        break
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\n❌ Error: {e}\n")
    
    finally:
        await automation.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
