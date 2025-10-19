"""
Centralized Configuration Manager
Loads configuration from config.ini at the root level
"""

import os
import configparser
from pathlib import Path
from typing import Optional


class Config:
    """Centralized configuration management"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern to ensure one config instance"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from config.ini file"""
        self._config = configparser.ConfigParser()
        
        # Get the root directory (project root)
        root_dir = Path(__file__).parent.parent.parent
        config_path = root_dir / 'config.ini'
        
        if config_path.exists():
            self._config.read(config_path)
            print(f"✅ Configuration loaded from: {config_path}")
        else:
            print(f"⚠️  config.ini not found at {config_path}")
            print(f"   Using environment variables and defaults")
    
    def get(self, section: str, key: str, fallback: Optional[str] = None) -> str:
        """
        Get configuration value.
        Priority: config.ini > environment variables > fallback
        """
        # Try to get from config.ini first
        if self._config and self._config.has_option(section, key):
            value = self._config.get(section, key)
            
            # Don't return placeholder values
            if value and not value.startswith('your_') and value != '':
                return value
        
        # Fall back to environment variable (uppercase)
        env_value = os.environ.get(key.upper())
        if env_value:
            return env_value
        
        # Use fallback if provided
        return fallback or ''
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.get(section, key)
        if value:
            return value.lower() in ('true', 'yes', '1', 'on')
        return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value"""
        value = self.get(section, key)
        try:
            return int(value) if value else fallback
        except ValueError:
            return fallback
    
    # API Keys
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        return self.get('API_KEYS', 'OPENAI_API_KEY')
    
    @property
    def gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key"""
        return self.get('API_KEYS', 'GEMINI_API_KEY')
    
    # Server Configuration
    @property
    def host(self) -> str:
        """Get server host"""
        return self.get('SERVER', 'HOST', '0.0.0.0')
    
    @property
    def port(self) -> int:
        """Get server port"""
        return self.get_int('SERVER', 'PORT', 5000)
    
    @property
    def debug(self) -> bool:
        """Get debug mode"""
        return self.get_bool('SERVER', 'DEBUG', False)
    
    # Browser Configuration
    @property
    def default_browser(self) -> str:
        """Get default browser"""
        return self.get('BROWSER', 'DEFAULT_BROWSER', 'chromium')
    
    @property
    def headless(self) -> bool:
        """Get headless mode"""
        return self.get_bool('BROWSER', 'HEADLESS', True)
    
    @property
    def timeout(self) -> int:
        """Get browser timeout"""
        return self.get_int('BROWSER', 'TIMEOUT', 30000)
    
    # Automation Configuration
    @property
    def max_retries(self) -> int:
        """Get max retries"""
        return self.get_int('AUTOMATION', 'MAX_RETRIES', 3)
    
    @property
    def enable_tracing(self) -> bool:
        """Get tracing enabled"""
        return self.get_bool('AUTOMATION', 'ENABLE_TRACING', True)
    
    @property
    def enable_healing(self) -> bool:
        """Get healing enabled"""
        return self.get_bool('AUTOMATION', 'ENABLE_HEALING', True)
    
    # Database Configuration
    @property
    def database_url(self) -> str:
        """Get database URL"""
        return self.get('DATABASE', 'DATABASE_URL', 'sqlite:///data/database/visionvault.db')
    
    # Paths
    @property
    def screenshots_dir(self) -> str:
        """Get screenshots directory"""
        return self.get('PATHS', 'SCREENSHOTS_DIR', 'data/uploads/screenshots')
    
    @property
    def logs_dir(self) -> str:
        """Get logs directory"""
        return self.get('PATHS', 'LOGS_DIR', 'data/logs')
    
    @property
    def uploads_dir(self) -> str:
        """Get uploads directory"""
        return self.get('PATHS', 'UPLOADS_DIR', 'data/uploads')
    
    # Feature Flags
    @property
    def enable_mcp(self) -> bool:
        """Get MCP enabled"""
        return self.get_bool('FEATURES', 'ENABLE_MCP', True)
    
    @property
    def enable_code_gen(self) -> bool:
        """Get code generation enabled"""
        return self.get_bool('FEATURES', 'ENABLE_CODE_GEN', True)
    
    @property
    def enable_hybrid(self) -> bool:
        """Get hybrid mode enabled"""
        return self.get_bool('FEATURES', 'ENABLE_HYBRID', True)
    
    @property
    def enable_self_learning(self) -> bool:
        """Get self-learning enabled"""
        return self.get_bool('FEATURES', 'ENABLE_SELF_LEARNING', True)


# Global config instance
config = Config()
