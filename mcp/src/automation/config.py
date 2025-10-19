from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import os


class BrowserType(Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class SelectorStrategy(Enum):
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ARIA = "aria"
    AUTO = "auto"


@dataclass
class BrowserConfig:
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone: str = "America/New_York"
    
    screenshot_on_error: bool = True
    video_recording: bool = False
    trace_recording: bool = False
    
    slow_mo: int = 0
    
    proxy: Optional[Dict[str, str]] = None
    
    ignore_https_errors: bool = True
    
    downloads_path: Optional[str] = None


@dataclass
class AutomationConfig:
    max_retries: int = 3
    retry_delay: int = 2
    wait_strategy: str = "networkidle"
    
    screenshot_dir: str = "screenshots"
    video_dir: str = "videos"
    session_dir: str = "sessions"
    
    log_level: str = "INFO"
    log_file: Optional[str] = "automation.log"
    
    save_session: bool = False
    session_name: str = "default"
    
    openai_model: str = "gpt-4o-mini"
    mcp_timeout: int = 300


def load_config_from_env() -> Dict[str, Any]:
    return {
        "browser_type": BrowserType(os.getenv("BROWSER_TYPE", "chromium")),
        "headless": os.getenv("HEADLESS", "true").lower() == "true",
        "timeout": int(os.getenv("TIMEOUT", "30000")),
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }
