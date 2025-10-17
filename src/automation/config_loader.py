"""
Configuration loader for reading from config.ini file
"""
import configparser
import os
from pathlib import Path
from typing import Optional


class ConfigLoader:
    """Load and manage configuration from config.ini file"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from .ini file"""
        if not Path(self.config_file).exists():
            raise FileNotFoundError(f"Configuration file {self.config_file} not found!")
        
        self.config.read(self.config_file)
    
    def _get_value(self, section: str, key: str, fallback: Optional[str] = None) -> Optional[str]:
        """Get a value from config, supporting environment variable substitution"""
        value = self.config.get(section, key, fallback=fallback)
        
        if value and value.startswith("${") and value.endswith("}"):
            # Environment variable substitution
            env_var = value[2:-1]
            return os.getenv(env_var, fallback)
        
        return value
    
    def _get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get a boolean value from config"""
        value = self._get_value(section, key, str(fallback))
        return value.lower() in ('true', 'yes', '1', 'on') if value else fallback
    
    def _get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get an integer value from config"""
        value = self._get_value(section, key, str(fallback))
        try:
            return int(value) if value else fallback
        except ValueError:
            return fallback
    
    # OpenAI Configuration
    @property
    def openai_api_key(self) -> Optional[str]:
        return self._get_value('OpenAI', 'api_key')
    
    @property
    def openai_model(self) -> str:
        return self._get_value('OpenAI', 'model', 'gpt-4o-mini') or 'gpt-4o-mini'
    
    # Browser Configuration
    @property
    def browser_type(self) -> str:
        return self._get_value('Browser', 'browser_type', 'chromium') or 'chromium'
    
    @property
    def browser_headless(self) -> bool:
        return self._get_bool('Browser', 'headless', False)
    
    @property
    def browser_timeout(self) -> int:
        return self._get_int('Browser', 'timeout', 30000)
    
    @property
    def screenshot_on_error(self) -> bool:
        return self._get_bool('Browser', 'screenshot_on_error', True)
    
    # Automation Configuration
    @property
    def max_retries(self) -> int:
        return self._get_int('Automation', 'max_retries', 3)
    
    @property
    def retry_delay(self) -> int:
        return self._get_int('Automation', 'retry_delay', 2)
    
    @property
    def log_level(self) -> str:
        return self._get_value('Automation', 'log_level', 'INFO') or 'INFO'
    
    @property
    def enable_vision(self) -> bool:
        return self._get_bool('Automation', 'enable_vision', True)
    
    # Paths Configuration
    @property
    def screenshots_dir(self) -> str:
        return self._get_value('Paths', 'screenshots_dir', 'screenshots') or 'screenshots'
    
    @property
    def logs_dir(self) -> str:
        return self._get_value('Paths', 'logs_dir', 'logs') or 'logs'
    
    # MCP Configuration
    @property
    def auto_refresh_dom(self) -> bool:
        return self._get_bool('MCP', 'auto_refresh_dom', True)
    
    @property
    def autonomous_execution(self) -> bool:
        return self._get_bool('MCP', 'autonomous_execution', True)


# Singleton instance
_config_instance: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance
