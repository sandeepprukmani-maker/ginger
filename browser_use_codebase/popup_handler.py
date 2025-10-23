"""
Popup Window Handler for Browser-Use
Automatically detects and switches to new popup windows
"""
import asyncio
import logging
from typing import Optional
from playwright.async_api import Page, BrowserContext

logger = logging.getLogger(__name__)


class PopupWindowHandler:
    """
    Monitors and handles popup windows automatically
    Switches to new windows when they appear during automation
    """
    
    def __init__(self, context: BrowserContext):
        """
        Initialize the popup handler
        
        Args:
            context: Playwright browser context to monitor
        """
        self.context = context
        self.current_page = None
        self.popup_detected = False
        self.new_pages = []
        
        context.on("page", self._on_new_page)
        logger.info("🔍 Popup window handler initialized")
    
    def _on_new_page(self, page: Page):
        """
        Event handler for new pages/windows
        
        Args:
            page: Newly created page object
        """
        logger.info(f"🆕 New window detected: {page.url}")
        self.new_pages.append(page)
        self.popup_detected = True
    
    async def get_active_page(self) -> Optional[Page]:
        """
        Get the currently active page (prioritizes new popups)
        
        Returns:
            Active page object or None
        """
        if self.new_pages:
            latest_page = self.new_pages[-1]
            
            try:
                await latest_page.wait_for_load_state("domcontentloaded", timeout=5000)
                logger.info(f"✅ Switched to popup window: {latest_page.url}")
                return latest_page
            except Exception as e:
                logger.warning(f"⚠️ Popup not ready yet: {str(e)}")
        
        all_pages = self.context.pages
        if all_pages:
            return all_pages[-1]
        
        return None
    
    def reset(self):
        """Reset the handler state"""
        self.new_pages.clear()
        self.popup_detected = False
        logger.info("🔄 Popup handler reset")
    
    def has_popup(self) -> bool:
        """Check if a popup window was detected"""
        return self.popup_detected
    
    def get_all_pages(self):
        """Get all open pages"""
        return self.context.pages
