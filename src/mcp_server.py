#!/usr/bin/env python3
"""
Simple Playwright MCP Server
Provides browser automation tools via MCP
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from playwright.async_api import async_playwright, Browser, Page
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightMCPServer:
    def __init__(self):
        self.server = Server("playwright-mcp-server")
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.playwright_context = None
        
        self.setup_tools()
    
    def setup_tools(self):
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="playwright_navigate",
                    description="Navigate to a URL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to navigate to"}
                        },
                        "required": ["url"]
                    }
                ),
                Tool(
                    name="playwright_click",
                    description="Click an element using various locator strategies",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "Element selector or text content"},
                            "role": {"type": "string", "description": "ARIA role (button, link, etc.)"},
                            "text": {"type": "string", "description": "Text content to find"}
                        }
                    }
                ),
                Tool(
                    name="playwright_fill",
                    description="Fill an input field",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "Input selector or label"},
                            "label": {"type": "string", "description": "Input label text"},
                            "value": {"type": "string", "description": "Value to fill"}
                        },
                        "required": ["value"]
                    }
                ),
                Tool(
                    name="playwright_get_text",
                    description="Get visible text content from the page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "Optional selector to get text from"}
                        }
                    }
                ),
                Tool(
                    name="playwright_screenshot",
                    description="Take a screenshot",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Screenshot file path"}
                        },
                        "required": ["path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            if not self.page:
                await self._init_browser()
            
            if name == "playwright_navigate":
                return await self._navigate(arguments["url"])
            elif name == "playwright_click":
                return await self._click(arguments)
            elif name == "playwright_fill":
                return await self._fill(arguments)
            elif name == "playwright_get_text":
                return await self._get_text(arguments.get("selector"))
            elif name == "playwright_screenshot":
                return await self._screenshot(arguments["path"])
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    async def _init_browser(self):
        if not self.playwright_context:
            self.playwright_context = await async_playwright().start()
        
        if not self.browser:
            self.browser = await self.playwright_context.chromium.launch(headless=True)
            context = await self.browser.new_context()
            self.page = await context.new_page()
            logger.info("Browser initialized")
    
    async def _navigate(self, url: str) -> list[TextContent]:
        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            locator = f'page.goto("{url}")'
            return [TextContent(
                type="text",
                text=f"Navigated to {url}\nLocator: {locator}"
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"Navigation error: {str(e)}")]
    
    async def _click(self, args: dict) -> list[TextContent]:
        """Try multiple locator strategies to find and click element"""
        text_hint = args.get("text", args.get("selector", ""))
        role_hint = args.get("role")
        
        strategies = []
        
        if role_hint and text_hint:
            strategies.append(
                ("get_by_role", f'page.get_by_role("{role_hint}", name="{text_hint}").click()',
                 lambda: self.page.get_by_role(role_hint, name=text_hint).click())
            )
        
        if text_hint:
            strategies.extend([
                ("get_by_text", f'page.get_by_text("{text_hint}").click()',
                 lambda: self.page.get_by_text(text_hint, exact=False).first.click()),
                ("get_by_text_exact", f'page.get_by_text("{text_hint}", exact=True).click()',
                 lambda: self.page.get_by_text(text_hint, exact=True).click()),
                ("locator_text", f'page.locator("text={text_hint}").click()',
                 lambda: self.page.locator(f"text={text_hint}").click())
            ])
        
        if "selector" in args:
            selector = args["selector"]
            strategies.append(
                ("locator_css", f'page.locator("{selector}").click()',
                 lambda: self.page.locator(selector).click())
            )
        
        last_error = None
        attempts = []
        
        for strategy_name, locator_str, action_fn in strategies:
            try:
                logger.info(f"Trying strategy: {strategy_name}")
                await action_fn()
                logger.info(f"✓ Success with: {strategy_name}")
                
                return [TextContent(
                    type="text",
                    text=f"Clicked element using {strategy_name}\nLocator: {locator_str}\nAttempted: {', '.join(attempts + [strategy_name])}"
                )]
            except Exception as e:
                attempts.append(strategy_name)
                last_error = str(e)
                logger.info(f"✗ Failed with {strategy_name}: {str(e)[:100]}")
                continue
        
        return [TextContent(
            type="text",
            text=f"Click failed after trying {len(strategies)} strategies: {', '.join(attempts)}\nLast error: {last_error}"
        )]
    
    async def _fill(self, args: dict) -> list[TextContent]:
        """Try multiple locator strategies to find and fill input field"""
        value = args["value"]
        label_hint = args.get("label")
        placeholder_hint = args.get("placeholder")
        selector_hint = args.get("selector")
        
        strategies = []
        
        if label_hint:
            strategies.extend([
                ("get_by_label", f'page.get_by_label("{label_hint}").fill("{value}")',
                 lambda: self.page.get_by_label(label_hint).fill(value)),
                ("get_by_label_partial", f'page.get_by_label("{label_hint}", exact=False).fill("{value}")',
                 lambda: self.page.get_by_label(label_hint, exact=False).fill(value))
            ])
        
        if placeholder_hint:
            strategies.append(
                ("get_by_placeholder", f'page.get_by_placeholder("{placeholder_hint}").fill("{value}")',
                 lambda: self.page.get_by_placeholder(placeholder_hint).fill(value))
            )
        
        if selector_hint:
            strategies.append(
                ("locator_css", f'page.locator("{selector_hint}").fill("{value}")',
                 lambda: self.page.locator(selector_hint).fill(value))
            )
        
        strategies.append(
            ("role_textbox", f'page.get_by_role("textbox").first.fill("{value}")',
             lambda: self.page.get_by_role("textbox").first.fill(value))
        )
        
        last_error = None
        attempts = []
        
        for strategy_name, locator_str, action_fn in strategies:
            try:
                logger.info(f"Trying strategy: {strategy_name}")
                await action_fn()
                logger.info(f"✓ Success with: {strategy_name}")
                
                return [TextContent(
                    type="text",
                    text=f"Filled input using {strategy_name}\nLocator: {locator_str}\nAttempted: {', '.join(attempts + [strategy_name])}"
                )]
            except Exception as e:
                attempts.append(strategy_name)
                last_error = str(e)
                logger.info(f"✗ Failed with {strategy_name}: {str(e)[:100]}")
                continue
        
        return [TextContent(
            type="text",
            text=f"Fill failed after trying {len(strategies)} strategies: {', '.join(attempts)}\nLast error: {last_error}"
        )]
    
    async def _get_text(self, selector: str | None = None) -> list[TextContent]:
        try:
            if selector:
                text = await self.page.locator(selector).text_content()
                locator_str = f'page.locator("{selector}").text_content()'
            else:
                text = await self.page.text_content("body")
                locator_str = 'page.text_content("body")'
            
            return [TextContent(
                type="text",
                text=f"Text content:\n{text}\n\nLocator: {locator_str}"
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"Get text error: {str(e)}")]
    
    async def _screenshot(self, path: str) -> list[TextContent]:
        try:
            await self.page.screenshot(path=path)
            return [TextContent(
                type="text",
                text=f"Screenshot saved to {path}\nLocator: page.screenshot(path='{path}')"
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"Screenshot error: {str(e)}")]
    
    async def cleanup(self):
        if self.browser:
            await self.browser.close()
        if self.playwright_context:
            await self.playwright_context.stop()
    
    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    server = PlaywrightMCPServer()
    try:
        await server.run()
    finally:
        await server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
