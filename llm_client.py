"""
Centralized LLM Client Module
Provides configured OpenAI clients for different services in the project
"""
import os
from typing import Optional, Any
from openai import OpenAI
from langchain_openai import ChatOpenAI
from pydantic import ConfigDict


class ChatOpenAIWithExtras(ChatOpenAI):
    """
    Wrapper for ChatOpenAI that allows extra attributes
    Required for browser-use library which adds provider and ainvoke attributes
    """
    model_config = ConfigDict(extra='allow', arbitrary_types_allowed=True)
    
    @property
    def model(self) -> str:
        """Return model name for browser-use compatibility"""
        return self.model_name


class LLMClientFactory:
    """Factory for creating configured LLM clients"""
    
    # Model configurations for different services
    BROWSER_USE_MODEL = "gpt-4o-mini"
    PLAYWRIGHT_MCP_MODEL = "gpt-4o-mini"
    AUTOMATION_ENGINE_MODEL = "gpt-4o-mini"
    SELF_HEALING_MODEL = "gpt-4o-mini"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM client factory
        
        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY env var
        """
        self._api_key = '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'
        if not self._api_key:
            raise ValueError(
                "OpenAI API key is required. "
                "Provide it as an argument or set OPENAI_API_KEY environment variable."
            )
    
    def get_browser_use_client(self, model: Optional[str] = None):
        """
        Get ChatOpenAI client for browser-use automation
        
        Args:
            model: Override default model (gpt-4o-mini)
            
        Returns:
            ChatOpenAIWithExtras client that allows browser-use to add attributes
        """
        if not self._api_key:
            raise ValueError("API key is not configured")
        
        # Use ChatOpenAIWithExtras which allows extra attributes for browser-use
        llm = ChatOpenAIWithExtras(
            model=model or self.BROWSER_USE_MODEL,
            api_key=self._api_key,
            temperature=0.7
        )
        
        # Add provider attribute required by browser-use token tracking
        llm.provider = 'openai'
        
        return llm
    
    def get_playwright_mcp_client(self, model: Optional[str] = None) -> OpenAI:
        """
        Get OpenAI client for Playwright MCP browser agent
        
        Args:
            model: Override default model (gpt-4o-mini)
            
        Returns:
            Configured OpenAI client for Playwright MCP
        """
        # Return OpenAI client - the model will be passed when making API calls
        return OpenAI(api_key=self._api_key)
    
    def get_playwright_mcp_model(self) -> str:
        """Get the configured model name for Playwright MCP"""
        return self.PLAYWRIGHT_MCP_MODEL
    
    def get_automation_engine_client(self, model: Optional[str] = None) -> ChatOpenAI:
        """
        Get ChatOpenAI client for automation engine
        
        Args:
            model: Override default model (gpt-4o-mini)
            
        Returns:
            Configured ChatOpenAI client for automation engine
        """
        if not self._api_key:
            raise ValueError("API key is not configured")
        return ChatOpenAI(
            model=model or self.AUTOMATION_ENGINE_MODEL,
            api_key=self._api_key  # type: ignore
        )
    
    def get_self_healing_client(self, model: Optional[str] = None) -> ChatOpenAI:
        """
        Get ChatOpenAI client for self-healing executor
        
        Args:
            model: Override default model (gpt-4o-mini)
            
        Returns:
            Configured ChatOpenAI client for self-healing
        """
        if not self._api_key:
            raise ValueError("API key is not configured")
        return ChatOpenAI(
            model=model or self.SELF_HEALING_MODEL,
            api_key=self._api_key  # type: ignore
        )


# Singleton instance for easy access
_factory_instance: Optional[LLMClientFactory] = None


def get_llm_factory(api_key: Optional[str] = None) -> LLMClientFactory:
    """
    Get or create the singleton LLM client factory
    
    Args:
        api_key: OpenAI API key. Only used on first call to create the factory.
        
    Returns:
        LLMClientFactory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = LLMClientFactory(api_key=api_key)
    return _factory_instance


def reset_llm_factory():
    """Reset the singleton factory (useful for testing)"""
    global _factory_instance
    _factory_instance = None


# Convenience functions for direct client access
def get_browser_use_client(model: Optional[str] = None):
    """Get ChatOpenAI client for browser-use automation"""
    return get_llm_factory().get_browser_use_client(model)


def get_playwright_mcp_client(model: Optional[str] = None) -> OpenAI:
    """Get OpenAI client for Playwright MCP"""
    return get_llm_factory().get_playwright_mcp_client(model)


def get_playwright_mcp_model() -> str:
    """Get the configured model name for Playwright MCP"""
    return get_llm_factory().get_playwright_mcp_model()


def get_automation_engine_client(model: Optional[str] = None) -> ChatOpenAI:
    """Get ChatOpenAI client for automation engine"""
    return get_llm_factory().get_automation_engine_client(model)


def get_self_healing_client(model: Optional[str] = None) -> ChatOpenAI:
    """Get ChatOpenAI client for self-healing executor"""
    return get_llm_factory().get_self_healing_client(model)
