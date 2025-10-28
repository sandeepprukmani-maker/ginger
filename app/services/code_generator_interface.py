"""
Unified Code Generator Interface
Provides a common interface for all code generators in the system
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum


class GeneratorType(Enum):
    """Type of code generator"""
    BROWSER_USE = "browser_use"
    PLAYWRIGHT_MCP = "playwright_mcp"


class CodeGeneratorInterface(ABC):
    """
    Abstract base class for code generators
    
    All code generators must implement this interface to ensure
    consistent behavior across the system
    """
    
    @abstractmethod
    def generate_code(
        self,
        task_description: str = "Automated browser task",
        test_framework: bool = True,
        include_comments: bool = True,
        async_style: bool = True
    ) -> str:
        """
        Generate complete Playwright Python code
        
        Args:
            task_description: Description of what the automation does
            test_framework: Use pytest-playwright framework (recommended)
            include_comments: Add explanatory comments
            async_style: Use async/await (recommended)
            
        Returns:
            Complete Python script as string
        """
        pass
    
    @abstractmethod
    def get_generator_type(self) -> GeneratorType:
        """
        Get the type of this generator
        
        Returns:
            GeneratorType enum value
        """
        pass
    
    @abstractmethod
    def has_actions(self) -> bool:
        """
        Check if the generator has any actions to generate code from
        
        Returns:
            True if actions are available, False otherwise
        """
        pass
    
    def generate_metadata(self) -> Dict[str, Any]:
        """
        Generate metadata about the generated code
        
        Returns:
            Dictionary with metadata (action count, quality scores, etc.)
        """
        return {
            'generator_type': self.get_generator_type().value,
            'has_actions': self.has_actions()
        }


def create_generator_from_engine_result(
    engine_type: str,
    result: Dict[str, Any],
    task_description: str = "Automated browser task"
) -> Optional[CodeGeneratorInterface]:
    """
    Factory function to create appropriate code generator based on engine type
    
    Args:
        engine_type: 'browser_use' or 'playwright_mcp'
        result: Execution result from the engine
        task_description: Description of the task
        
    Returns:
        CodeGeneratorInterface instance or None if creation fails
    """
    try:
        if engine_type == 'browser_use':
            from app.engines.browser_use.playwright_code_generator import PlaywrightCodeGenerator
            
            history = result.get('history')
            if history:
                return BrowserUseCodeGenerator(history, task_description)
        
        elif engine_type == 'playwright_mcp':
            from app.engines.playwright_mcp.mcp_code_generator import MCPCodeGenerator
            
            steps = result.get('steps') or []
            if steps:
                return PlaywrightMCPCodeGenerator(steps, task_description)
        
        return None
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create code generator for {engine_type}: {str(e)}")
        return None


class BrowserUseCodeGenerator(CodeGeneratorInterface):
    """Wrapper for PlaywrightCodeGenerator to implement unified interface"""
    
    def __init__(self, history, task_description: str):
        from app.engines.browser_use.playwright_code_generator import PlaywrightCodeGenerator
        self.generator = PlaywrightCodeGenerator(history, task_description)
        self.generator.parse_history()
    
    def generate_code(
        self,
        task_description: str = None,
        test_framework: bool = True,
        include_comments: bool = True,
        async_style: bool = True
    ) -> str:
        if task_description is not None:
            self.generator.task_description = task_description
        return self.generator.generate_python_code(
            use_locators=True,
            include_comments=include_comments,
            async_style=async_style,
            test_framework=test_framework
        )
    
    def get_generator_type(self) -> GeneratorType:
        return GeneratorType.BROWSER_USE
    
    def has_actions(self) -> bool:
        return len(self.generator.actions) > 0
    
    def generate_metadata(self) -> Dict[str, Any]:
        base_meta = super().generate_metadata()
        base_meta.update({
            'action_count': len(self.generator.actions),
            'locator_count': len(self.generator.locators)
        })
        return base_meta


class PlaywrightMCPCodeGenerator(CodeGeneratorInterface):
    """Wrapper for MCPCodeGenerator to implement unified interface"""
    
    def __init__(self, steps: List[Dict[str, Any]], task_description: str):
        from app.engines.playwright_mcp.mcp_code_generator import MCPCodeGenerator
        self.generator = MCPCodeGenerator(steps, task_description)
        self.generator.parse_steps()
    
    def generate_code(
        self,
        task_description: str = None,
        test_framework: bool = True,
        include_comments: bool = True,
        async_style: bool = True
    ) -> str:
        if task_description is not None:
            self.generator.task_description = task_description
        return self.generator.generate_python_code(
            test_framework=test_framework,
            include_comments=include_comments,
            async_style=async_style
        )
    
    def get_generator_type(self) -> GeneratorType:
        return GeneratorType.PLAYWRIGHT_MCP
    
    def has_actions(self) -> bool:
        return len(self.generator.actions) > 0
    
    def generate_metadata(self) -> Dict[str, Any]:
        base_meta = super().generate_metadata()
        base_meta.update({
            'action_count': len(self.generator.actions),
            'element_metadata_count': len(self.generator.element_metadata)
        })
        return base_meta
