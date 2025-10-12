import os
import sys
import subprocess
import re
import base64


def detect_browsers():
    """Detect available browsers on the system"""
    browsers = []
    try:
        if sys.platform == 'win32':
            paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            if any(os.path.exists(p) for p in paths):
                browsers.append('chromium')
        elif sys.platform == 'darwin':
            if os.path.exists('/Applications/Google Chrome.app'):
                browsers.append('chromium')
            if os.path.exists('/Applications/Firefox.app'):
                browsers.append('firefox')
            if os.path.exists('/Applications/Safari.app'):
                browsers.append('webkit')
        else:
            if subprocess.run(['which', 'google-chrome'], capture_output=True).returncode == 0:
                browsers.append('chromium')
            if subprocess.run(['which', 'firefox'], capture_output=True).returncode == 0:
                browsers.append('firefox')
        if not browsers:
            browsers = ['chromium']
    except Exception as e:
        print(f"Browser detection error: {e}")
        browsers = ['chromium']

    print(f"Detected browsers: {browsers}")
    return browsers


def extract_failed_locator_local(error_message):
    """Extract the failed locator from Playwright error messages."""
    patterns = [
        r'locator\(["\']([^"\']+)["\']\)',
        r'waiting for locator\(["\']([^"\']+)["\']\)',
        r'waiting for ([^\s]+)',
        r'Timeout.*?locator\(["\']([^"\']+)["\']\)',
    ]

    for pattern in patterns:
        match = re.search(pattern, error_message)
        if match:
            return match.group(1)

    return None


def encode_screenshot(screenshot_bytes):
    """Encode screenshot to base64 string"""
    if screenshot_bytes:
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    return None