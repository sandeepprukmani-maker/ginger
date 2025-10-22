"""
AI Browser Automation with Self-Healing Code Generation

This package provides AI-powered browser automation with automatic code generation
and self-healing capabilities.
"""

__version__ = "1.0.0"

from .automation_engine import BrowserAutomationEngine
from .playwright_code_generator import PlaywrightCodeGenerator
from .self_healing_executor import SelfHealingExecutor
from .locator_utils import LocatorBuilder, LocatorHealer

__all__ = [
    "BrowserAutomationEngine",
    "PlaywrightCodeGenerator",
    "SelfHealingExecutor",
    "LocatorBuilder",
    "LocatorHealer",
]
