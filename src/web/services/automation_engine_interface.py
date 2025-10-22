"""
Shared interface for automation engines
"""
from typing import Protocol, Dict, Any, List
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result from an automation execution"""
    success: bool
    message: str
    steps: List[Dict[str, Any]]
    error: str = ""
    engine_used: str = ""
    fallback_occurred: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            'success': self.success,
            'message': self.message,
            'steps': self.steps,
            'error': self.error,
            'engine_used': self.engine_used,
            'fallback_occurred': self.fallback_occurred
        }


class AutomationEngine(Protocol):
    """Protocol/Interface for automation engines"""
    
    def execute_instruction(
        self, 
        instruction: str, 
        headless: bool = True
    ) -> ExecutionResult:
        """
        Execute a browser automation instruction
        
        Args:
            instruction: Natural language instruction to execute
            headless: Whether to run browser in headless mode
            
        Returns:
            ExecutionResult with success status, steps, and metadata
        """
        ...
    
    def reset_conversation(self) -> None:
        """Reset the conversation/session state"""
        ...
    
    @property
    def name(self) -> str:
        """Return the engine name"""
        ...
