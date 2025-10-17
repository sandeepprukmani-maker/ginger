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
    
    def __init__(self, api_key: str, enable_vision: bool = True):
        self.client = AsyncOpenAI(api_key=api_key)
        self.mcp = PlaywrightMCPClient()
        self.conversation_history = []
        self.enable_vision = enable_vision
        self.vision_analyzer = VisionAnalyzer(api_key) if enable_vision else None
        self.session_memory = SessionMemory()
        self.max_retries = 3
        self.screenshot_count = 0
    
    async def initialize(self, browser: str = "chromium", headless: bool = True):
        """Initialize MCP connection."""
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
                return snapshot[:5000]  # Limit size
            return ""
        except Exception as e:
            logger.error(f"Failed to get page context: {e}")
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
    
    async def _smart_retry_with_vision(self, tool_name: str, tool_args: Dict[str, Any], error: str, instruction: str) -> Any:
        """Retry failed action with vision-based correction and intelligent catalog matching."""
        logger.info(f"Attempting smart retry for {tool_name} using vision and element catalog...")
        
        # Strategy 1: Vision-based selector correction (PRIMARY)
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
    
    async def execute_command(self, command: str) -> str:
        """
        Execute a natural language command using AI + MCP with enhanced capabilities.
        
        Args:
            command: Natural language instruction
            
        Returns:
            Result description
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

CURRENT PAGE CONTEXT:
{page_context[:1000] if page_context else 'No context available'}

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
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                *self.conversation_history
            ],
            tools=openai_tools,
            tool_choice="auto",
            temperature=0.3  # Lower temperature for more consistent automation
        )
        
        message = response.choices[0].message
        results = []
        tool_execution_log = []
        
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
                
                logger.info(f"Executing: {tool_name}({tool_args})")
                
                # Try executing with retries
                retry_count = 0
                while retry_count < self.max_retries:
                    try:
                        result = await self.mcp.call_tool(tool_name, tool_args)
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
                        
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        retry_count += 1
                        error_msg = f"✗ {tool_name} failed (attempt {retry_count}/{self.max_retries}): {e}"
                        logger.warning(error_msg)
                        
                        if retry_count < self.max_retries:
                            # Try smart retry with vision
                            try:
                                result = await self._smart_retry_with_vision(tool_name, tool_args.copy(), str(e), command)
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
        
        # Get final response with enhanced context
        if results:
            final_response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize what was accomplished in a friendly, clear way. Mention any retries or alternative strategies used."
                    },
                    *self.conversation_history
                ]
            )
            summary = final_response.choices[0].message.content or "Task completed"
            logger.success(summary)
            return summary
        else:
            return message.content or "Command executed"
    
    async def cleanup(self):
        """Clean up resources."""
        await self.mcp.close()
        logger.info("MCP automation cleaned up successfully")


async def main():
    """Main entry point for enhanced MCP automation."""
    import os
    
    # Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set!")
        sys.exit(1)
    
    # Ask user for vision mode
    print("\n" + "="*70)
    print("🚀 ENHANCED Playwright MCP Natural Language Automation")
    print("="*70)
    print("\nFeatures:")
    print("  ✓ Vision-based intelligent page analysis")
    print("  ✓ Smart error recovery with automatic retries")
    print("  ✓ Session memory learns from successful patterns")
    print("  ✓ Advanced web handling (forms, tables, iframes, dynamic content)")
    print("  ✓ Multi-strategy element detection")
    print("="*70)
    
    enable_vision = input("\nEnable vision mode for complex pages? (y/n, default=y): ").strip().lower() != 'n'
    
    # Create automation instance
    automation = EnhancedMCPAutomation(api_key, enable_vision=enable_vision)
    
    try:
        # Initialize MCP
        logger.info("Initializing Enhanced Playwright MCP server...")
        await automation.initialize(browser="chromium", headless=False)
        
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
        
        # Interactive mode
        while True:
            try:
                command = input("💬 Command: ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if not command:
                    continue
                
                result = await automation.execute_command(command)
                print(f"\n✅ {result}\n")
                
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
