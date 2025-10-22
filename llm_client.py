"""
Centralized LLM Client Module
Provides configured OpenAI clients for different services in the project
"""
import os
from typing import Optional
from openai import OpenAI
from langchain_openai import ChatOpenAI
from browser_use import ChatBrowserUse


class ChatOpenAIWithProvider(ChatOpenAI):
    """Wrapper for ChatOpenAI that adds provider attribute for browser-use compatibility"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add provider attribute required by browser-use token tracking
        self.provider = "openai"


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
        Get ChatOpenAI client for browser-use automation with provider attribute
        
        Args:
            model: Override default model (gpt-4o-mini)
            
        Returns:
            Configured ChatOpenAI client with provider attribute for browser-use
        """
        if not self._api_key:
            raise ValueError("API key is not configured")
        # Use ChatOpenAIWithProvider wrapper that adds the provider attribute
        # required by browser-use 0.8.1+ token tracking
        return ChatOpenAIWithProvider(
            model=model or self.BROWSER_USE_MODEL,
            openai_api_key=self._api_key,
            temperature=0.7
        )
    
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
