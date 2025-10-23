# Windows Browser Timeout Troubleshooting Guide

## The Issue

The browser-use library (v0.9.0) has a **hardcoded 30-second timeout** for browser startup events. On Windows systems, especially with antivirus software running, the browser can take longer than 30 seconds to launch, resulting in timeout errors:

```
TimeoutError: Event handler browser_use.browser.watchdog_base.BrowserSession.on_BrowserStartEvent timed out after 30.0s
```

## Why This Happens on Windows

1. **Antivirus scanning** - Windows Defender or third-party antivirus scans Playwright binaries
2. **First launch overhead** - Initial browser launch creates cache and profile data
3. **System resources** - Other running applications competing for resources
4. **Windows file system** - Slower than Linux for creating temporary files

## Solutions (In Order of Effectiveness)

### Solution 1: Use Headless Mode (Fastest)
Headless mode launches significantly faster because it doesn't need to initialize the GUI:

1. In the web interface, ensure "Headless" toggle is **ON** (enabled)
2. Headless browsers use less memory and start ~50% faster

### Solution 2: Temporarily Disable Antivirus
**WARNING: Only do this for testing, re-enable afterward**

1. Open Windows Security
2. Go to "Virus & threat protection"
3. Click "Manage settings" under "Virus & threat protection settings"
4. Temporarily turn off "Real-time protection"
5. Run your browser automation task
6. **Re-enable protection immediately after testing**

### Solution 3: Add Playwright to Antivirus Exclusions (Recommended for Long-term Use)

**For Windows Defender:**
1. Open Windows Security → Virus & threat protection
2. Scroll down to "Virus & threat protection settings" → Manage settings
3. Scroll down to "Exclusions" → Add or remove exclusions
4. Add these folders:
   ```
   C:\Users\<YourUsername>\AppData\Local\ms-playwright
   C:\Users\<YourUsername>\Downloads\ginger (1) 2\ginger\.venv
   ```

**For Third-Party Antivirus:**
- Check your antivirus documentation for how to add exclusions
- Add the same folders as above

### Solution 4: Run as Administrator
1. Right-click Command Prompt or PowerShell
2. Select "Run as administrator"
3. Navigate to your project directory
4. Activate virtual environment: `.venv\Scripts\activate`
5. Run: `python main.py`

### Solution 5: Close Resource-Intensive Applications
- Close Chrome/Edge/Firefox browsers
- Close VS Code or other IDEs
- Close video editing or gaming software
- Check Task Manager for high CPU/memory usage

### Solution 6: Run Task Once to Warm Up Cache
The **first** browser launch is always the slowest because it:
- Creates browser profile directories
- Generates cache files
- Initializes browser data

**Try this:**
1. Run a simple task: "go to example.com"
2. Wait for it to timeout (yes, let it fail)
3. Run your actual task - it should be faster now
4. Subsequent runs will use cached data

### Solution 7: Alternative - Use Direct Playwright (Workaround)

If browser-use continues to timeout, you can create a simpler Playwright implementation. Create this file:

**File: `simple_browser_task.py`**
```python
import asyncio
from playwright.async_api import async_playwright

async def simple_google_search(search_term):
    """Simple Playwright implementation without browser-use"""
    async with async_playwright() as p:
        # Launch with increased timeout
        browser = await p.chromium.launch(
            headless=True,
            timeout=90000  # 90 second timeout
        )
        
        page = await browser.new_page()
        
        try:
            # Navigate to Google
            await page.goto('https://google.com', timeout=60000)
            
            # Handle cookie consent if present
            try:
                await page.click('button:has-text("Accept")', timeout=3000)
            except:
                pass  # No cookie consent, continue
            
            # Search
            await page.fill('input[name="q"]', search_term)
            await page.press('input[name="q"]', 'Enter')
            
            # Wait for results
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot
            await page.screenshot(path=f'search_result.png')
            
            print(f"✓ Search completed for: {search_term}")
            print(f"✓ Screenshot saved as: search_result.png")
            
        finally:
            await browser.close()

# Run it
if __name__ == "__main__":
    asyncio.run(simple_google_search("dogs"))
```

Run it with:
```powershell
python simple_browser_task.py
```

## Understanding the Error

The timeout occurs in these stages:
1. **BrowserStartEvent** - browser-use library tries to start browser
2. **LocalBrowserWatchdog.on_BrowserLaunchEvent** - waiting for browser to fully launch
3. After 30 seconds, if not complete → **TIMEOUT**

This is a limitation of the browser-use library, not your code or Windows.

## Long-term Recommendation

For Windows development:
1. **Always use headless mode** (fastest)
2. **Add Playwright to antivirus exclusions** (prevents scanning overhead)
3. **Keep browser sessions alive** (already configured with `keep_alive=True`)
4. **Consider WSL2** - Run the application in Windows Subsystem for Linux 2 for better performance

## Testing Your Setup

Try this quick test to check if your browser launches successfully:

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Test Playwright directly (bypasses browser-use timeout)
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=True); print('✓ Browser launched successfully!'); browser.close()"
```

If this succeeds but browser-use still times out, the issue is specifically with the browser-use library's timeout handling.

## Why Replit Works But Windows Doesn't

- **Replit**: Linux environment, no antivirus, SSD storage, optimized for development
- **Windows**: Antivirus scanning, different file system, more background processes

This is a known issue with browser automation on Windows and affects many tools, not just browser-use.

## Summary

**Quick Fix Checklist:**
- ☐ Use headless mode
- ☐ Add Playwright folder to antivirus exclusions  
- ☐ Close unnecessary applications
- ☐ Run first task to warm up cache (can fail)
- ☐ Try again - should work faster

**If nothing works:**
- Use the simple_browser_task.py workaround above
- Or use WSL2 for Linux-like performance on Windows
