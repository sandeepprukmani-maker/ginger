"""
Azure OpenAI OAuth Integration
Integrates Azure OpenAI with OAuth token authentication for browser-use

This module uses your existing OAuth infrastructure for authentication.
Make sure you have your custom OAuth module available in your Python path.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_azure_openai_token() -> str:
    """
    Get Azure OpenAI OAuth token using your existing OAuth infrastructure
    
    This function attempts to import your custom OAuth module.
    If not available, falls back to using a placeholder that you can replace.
    
    Returns:
        OAuth access token for Azure OpenAI
    
    Raises:
        EnvironmentError: If required environment variables are missing
        ImportError: If OAuth module is not available
    """
    required_env_vars = [
        "OAUTH_TOKEN_URL",
        "OAUTH_CLIENT_ID",
        "OAUTH_CLIENT_SECRET",
        "OAUTH_GRANT_TYPE",
        "OAUTH_SCOPE",
        "GM_BASE_URL"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    
    try:
        # Try to import your custom OAuth module
        # Update this import path to match your project structure
        from genai_gateway_tools.oauth import OAuthConfig, OAuthTokenFetcher
        
        oauth_config = OAuthConfig(
            token_url=os.environ["OAUTH_TOKEN_URL"],
            client_id=os.environ["OAUTH_CLIENT_ID"],
            client_secret=os.environ["OAUTH_CLIENT_SECRET"],
            grant_type=os.environ["OAUTH_GRANT_TYPE"],
            scope=os.environ["OAUTH_SCOPE"]
        )
        
        token_fetcher = OAuthTokenFetcher(oauth_config)
        token = token_fetcher.get_token()
        
        logger.info("✅ Retrieved Azure OpenAI OAuth token")
        return token
        
    except ImportError:
        # Fallback: Use your own OAuth implementation
        # Replace this with your actual get_openai_client() function logic
        logger.warning("⚠️  Custom OAuth module not found. Using fallback method.")
        logger.warning("⚠️  Please update app/utils/azure_oauth.py to use your OAuth implementation.")
        
        # This is a placeholder - replace with your actual OAuth token retrieval
        # You can copy the logic from your get_openai_client() function
        raise ImportError(
            "Custom OAuth module not available. "
            "Please install your genai_gateway_tools package or "
            "update app/utils/azure_oauth.py to use your OAuth implementation."
        )


def get_azure_base_url() -> str:
    """
    Get Azure OpenAI base URL from environment
    
    Returns:
        Base URL for Azure OpenAI endpoint
    """
    base_url = os.environ.get("GM_BASE_URL")
    if not base_url:
        raise EnvironmentError("GM_BASE_URL environment variable not set")
    
    return base_url
