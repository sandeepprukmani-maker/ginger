class BrowserManager:
    def __init__(self):
        self.active_page = None
        self.active_playwright_instance = None
        self.widget_injection_complete = None

    async def cleanup_browser(self):
        """Clean up browser resources"""
        if self.active_page and hasattr(self.active_page, 'context') and hasattr(self.active_page.context, 'browser'):
            try:
                browser = self.active_page.context.browser
                await browser.close()
                print("✅ Browser closed after healing attempt")
            except Exception as e:
                print(f"Browser cleanup error: {e}")
            finally:
                self.active_page = None

        if self.active_playwright_instance and hasattr(self.active_playwright_instance, 'stop'):
            try:
                await self.active_playwright_instance.stop()
                print("✅ Playwright instance stopped")
            except Exception as e:
                print(f"Playwright cleanup error: {e}")
            finally:
                self.active_playwright_instance = None

    def set_active_page(self, page):
        """Set the active page for healing operations"""
        self.active_page = page

    def set_playwright_instance(self, playwright_instance):
        """Set the active playwright instance"""
        self.active_playwright_instance = playwright_instance

    def set_widget_event(self, event):
        """Set the widget injection completion event"""
        self.widget_injection_complete = event