import logging
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme


custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
})

console = Console(theme=custom_theme)


class AutomationLogger:
    def __init__(self, name: str = "automation", log_level: str = "INFO", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if not self.logger.handlers:
            console_handler = RichHandler(
                console=console,
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                show_time=True,
                show_path=True
            )
            console_handler.setLevel(getattr(logging, log_level.upper()))
            self.logger.addHandler(console_handler)
            
            if log_file:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def success(self, message: str):
        console.print(f"✅ {message}", style="success")
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def exception(self, message: str):
        self.logger.exception(message)


def get_logger(name: str = "automation", log_level: str = "INFO", log_file: Optional[str] = None) -> AutomationLogger:
    return AutomationLogger(name, log_level, log_file)
