import base64
import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from dataclasses import dataclass

from playwright.async_api import Page, Frame, ElementHandle

from .logger import get_logger

logger = get_logger()


@dataclass
class PageContext:
    """Rich context about the current page state."""
    url: str
    title: str
    has_iframes: bool
    has_popups: bool
    has_alerts: bool
    visible_elements: List[str]
    dom_snapshot: Optional[str] = None
    screenshot_base64: Optional[str] = None


class AdvancedPlaywrightTools:
    """
    Advanced Playwright tools with intelligent capabilities:
    - Vision-based element detection
    - Dynamic content handling
    - iframe/popup management
    - File upload/download
    - Smart waiting strategies
    - DOM inspection
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.frames: List[Frame] = []
        self.context_history: List[PageContext] = []
    
    async def get_page_context(self, include_screenshot: bool = False, 
                               include_dom: bool = False) -> PageContext:
        """
        Get comprehensive context about the current page.
        """
        try:
            url = self.page.url
            title = await self.page.title()
            
            frames = self.page.frames
            has_iframes = len(frames) > 1
            
            has_alerts = False
            has_popups = len(self.page.context.pages) > 1
            
            visible_elements = await self._get_visible_elements()
            
            dom_snapshot = None
            if include_dom:
                dom_snapshot = await self._get_dom_snapshot()
            
            screenshot_base64 = None
            if include_screenshot:
                screenshot_base64 = await self._capture_screenshot_base64()
            
            context = PageContext(
                url=url,
                title=title,
                has_iframes=has_iframes,
                has_popups=has_popups,
                has_alerts=has_alerts,
                visible_elements=visible_elements,
                dom_snapshot=dom_snapshot,
                screenshot_base64=screenshot_base64
            )
            
            self.context_history.append(context)
            if len(self.context_history) > 10:
                self.context_history.pop(0)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting page context: {e}")
            return PageContext(
                url="unknown",
                title="unknown",
                has_iframes=False,
                has_popups=False,
                has_alerts=False,
                visible_elements=[]
            )
    
    async def _get_visible_elements(self) -> List[str]:
        """Get list of visible interactive elements on the page."""
        script = """
        () => {
            const elements = [];
            const selectors = [
                'button', 'a', 'input', 'textarea', 'select',
                '[role="button"]', '[onclick]', '[href]',
                'h1', 'h2', 'h3', 'form', 'nav'
            ];
            
            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const text = el.textContent?.trim().substring(0, 50) || '';
                        const id = el.id ? `#${el.id}` : '';
                        const className = el.className ? `.${el.className.split(' ')[0]}` : '';
                        elements.push({
                            tag: el.tagName.toLowerCase(),
                            id: id,
                            class: className,
                            text: text,
                            type: el.type || '',
                            visible: true
                        });
                    }
                });
            });
            
            return elements.slice(0, 50);
        }
        """
        
        try:
            elements = await self.page.evaluate(script)
            return [
                f"{el['tag']}{el['id']}{el['class']} - {el['text']}"
                for el in elements
            ]
        except Exception as e:
            logger.error(f"Error getting visible elements: {e}")
            return []
    
    async def _get_dom_snapshot(self) -> str:
        """Get simplified DOM snapshot for AI analysis."""
        script = """
        () => {
            const getSnapshot = (el, depth = 0, maxDepth = 3) => {
                if (depth > maxDepth) return '';
                
                const indent = '  '.repeat(depth);
                const tag = el.tagName.toLowerCase();
                const id = el.id ? `#${el.id}` : '';
                const className = el.className ? `.${el.className.split(' ')[0]}` : '';
                const text = el.childNodes.length === 1 && el.childNodes[0].nodeType === 3
                    ? ` "${el.textContent.trim().substring(0, 30)}"`
                    : '';
                
                let result = `${indent}<${tag}${id}${className}${text}>\\n`;
                
                for (const child of el.children) {
                    result += getSnapshot(child, depth + 1, maxDepth);
                }
                
                return result;
            };
            
            return getSnapshot(document.body);
        }
        """
        
        try:
            snapshot = await self.page.evaluate(script)
            return snapshot[:5000]
        except Exception as e:
            logger.error(f"Error getting DOM snapshot: {e}")
            return ""
    
    async def _capture_screenshot_base64(self) -> str:
        """Capture screenshot as base64 for vision analysis."""
        try:
            screenshot_bytes = await self.page.screenshot(full_page=False)
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return ""
    
    async def smart_find_element(self, description: str) -> Optional[str]:
        """
        Find element using intelligent strategies based on natural language description.
        Returns the best selector found.
        """
        logger.info(f"Smart finding element: {description}")
        
        strategies = [
            self._find_by_text(description),
            self._find_by_aria_label(description),
            self._find_by_placeholder(description),
            self._find_by_id_or_class(description),
            self._find_by_type(description)
        ]
        
        for strategy in strategies:
            try:
                selector = await strategy
                if selector and await self._element_exists(selector):
                    logger.success(f"Found element with selector: {selector}")
                    return selector
            except Exception as e:
                logger.debug(f"Strategy failed: {e}")
                continue
        
        logger.warning(f"Could not find element: {description}")
        return None
    
    async def _find_by_text(self, description: str) -> Optional[str]:
        """Find element by visible text content."""
        keywords = description.lower().split()
        
        for keyword in keywords:
            if len(keyword) < 3:
                continue
            
            selector = f"text={keyword}"
            if await self._element_exists(selector):
                return selector
        
        return None
    
    async def _find_by_aria_label(self, description: str) -> Optional[str]:
        """Find element by ARIA label."""
        selector = f"[aria-label*='{description}' i]"
        return selector if await self._element_exists(selector) else None
    
    async def _find_by_placeholder(self, description: str) -> Optional[str]:
        """Find input by placeholder text."""
        selector = f"[placeholder*='{description}' i]"
        return selector if await self._element_exists(selector) else None
    
    async def _find_by_id_or_class(self, description: str) -> Optional[str]:
        """Find element by ID or class name."""
        clean_desc = description.lower().replace(' ', '-')
        
        selectors = [
            f"#{clean_desc}",
            f".{clean_desc}",
            f"[id*='{clean_desc}']",
            f"[class*='{clean_desc}']"
        ]
        
        for selector in selectors:
            if await self._element_exists(selector):
                return selector
        
        return None
    
    async def _find_by_type(self, description: str) -> Optional[str]:
        """Find element by type (button, link, input, etc.)."""
        type_map = {
            'button': 'button, [role="button"], input[type="submit"]',
            'link': 'a[href]',
            'input': 'input',
            'search': 'input[type="search"], input[name*="search"]',
            'email': 'input[type="email"], input[name*="email"]',
            'password': 'input[type="password"]',
            'submit': 'button[type="submit"], input[type="submit"]',
            'form': 'form',
            'heading': 'h1, h2, h3, h4, h5, h6'
        }
        
        desc_lower = description.lower()
        for keyword, selector in type_map.items():
            if keyword in desc_lower:
                if await self._element_exists(selector):
                    return selector
        
        return None
    
    async def _element_exists(self, selector: str) -> bool:
        """Check if element exists and is visible."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                is_visible = await element.is_visible()
                return is_visible
            return False
        except Exception:
            return False
    
    async def handle_iframe(self, iframe_selector: Optional[str] = None) -> Optional[Frame]:
        """Switch context to iframe for automation."""
        try:
            if iframe_selector:
                frame_element = await self.page.query_selector(iframe_selector)
                if frame_element:
                    frame = await frame_element.content_frame()
                    if frame:
                        logger.info(f"Switched to iframe: {iframe_selector}")
                        return frame
            else:
                frames = self.page.frames
                if len(frames) > 1:
                    logger.info(f"Found {len(frames)} frames")
                    return frames[1]
            
            return None
        except Exception as e:
            logger.error(f"Error handling iframe: {e}")
            return None
    
    async def handle_popup(self) -> Optional[Page]:
        """Handle popup windows."""
        try:
            pages = self.page.context.pages
            if len(pages) > 1:
                popup = pages[-1]
                logger.info(f"Switched to popup: {popup.url}")
                return popup
            return None
        except Exception as e:
            logger.error(f"Error handling popup: {e}")
            return None
    
    async def wait_for_dynamic_content(self, timeout: int = 10000):
        """Wait for dynamic content to load (AJAX, lazy loading, etc.)."""
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
            
            await self.page.wait_for_function(
                """() => {
                    return document.readyState === 'complete' &&
                           performance.timing.loadEventEnd > 0;
                }""",
                timeout=timeout
            )
            
            logger.info("Dynamic content loaded")
        except Exception as e:
            logger.warning(f"Timeout waiting for dynamic content: {e}")
    
    async def scroll_to_element(self, selector: str):
        """Scroll element into view."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                await element.scroll_into_view_if_needed()
                logger.info(f"Scrolled to element: {selector}")
        except Exception as e:
            logger.error(f"Error scrolling to element: {e}")
    
    async def handle_file_upload(self, selector: str, file_path: str):
        """Handle file upload."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                await element.set_input_files(file_path)
                logger.success(f"File uploaded: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False
    
    async def extract_table_data(self, table_selector: str = "table") -> List[Dict[str, Any]]:
        """Extract structured data from HTML tables."""
        script = f"""
        (selector) => {{
            const table = document.querySelector(selector);
            if (!table) return [];
            
            const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            
            return rows.map(row => {{
                const cells = Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim());
                const rowData = {{}};
                headers.forEach((header, i) => {{
                    rowData[header] = cells[i] || '';
                }});
                return rowData;
            }});
        }}
        """
        
        try:
            data = await self.page.evaluate(script, table_selector)
            logger.info(f"Extracted {len(data)} rows from table")
            return data
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return []
    
    async def extract_links(self, filter_text: Optional[str] = None) -> List[Dict[str, str]]:
        """Extract all links from page, optionally filtered by text."""
        script = """
        (filterText) => {
            const links = Array.from(document.querySelectorAll('a[href]'));
            return links
                .filter(a => !filterText || a.textContent.toLowerCase().includes(filterText.toLowerCase()))
                .map(a => ({
                    text: a.textContent.trim(),
                    href: a.href,
                    title: a.title || ''
                }))
                .slice(0, 100);
        }
        """
        
        try:
            links = await self.page.evaluate(script, filter_text)
            logger.info(f"Extracted {len(links)} links")
            return links
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    async def wait_for_navigation_complete(self, timeout: int = 30000):
        """Wait for page navigation to complete fully."""
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=timeout)
            await self.page.wait_for_load_state('load', timeout=timeout)
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
            logger.info("Navigation completed")
        except Exception as e:
            logger.warning(f"Navigation timeout: {e}")
