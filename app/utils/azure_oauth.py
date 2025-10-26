"""
Azure OpenAI OAuth Token Fetcher
Handles OAuth2 client credentials flow for Azure OpenAI API authentication
"""
import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class OAuthTokenFetcher:
    """
    OAuth2 token fetcher for Azure OpenAI API
    Uses client credentials flow to obtain access tokens
    Provides a callable interface for LangChain's azure_ad_token_provider
    """
    
    def __init__(self, oauth_config: Optional[dict] = None):
        """
        Initialize OAuth token fetcher
        
        Args:
            oauth_config: Optional dictionary with OAuth configuration.
                         If not provided, will read from environment variables.
        """
        if oauth_config:
            self.token_url = oauth_config.get("OAUTH_TOKEN_URL")
            self.client_id = oauth_config.get("OAUTH_CLIENT_ID")
            self.client_secret = oauth_config.get("OAUTH_CLIENT_SECRET")
            self.grant_type = oauth_config.get("OAUTH_GRANT_TYPE", "client_credentials")
            self.scope = oauth_config.get("OAUTH_SCOPE")
        else:
            self.token_url = os.environ.get("OAUTH_TOKEN_URL")
            self.client_id = os.environ.get("OAUTH_CLIENT_ID")
            self.client_secret = os.environ.get("OAUTH_CLIENT_SECRET")
            self.grant_type = os.environ.get("OAUTH_GRANT_TYPE", "client_credentials")
            self.scope = os.environ.get("OAUTH_SCOPE")
        
        self._validate_config()
        
        self._token_cache = None
        self._token_expiry = 0
    
    def _validate_config(self):
        """Validate that all required OAuth configuration is present"""
        required_vars = [
            "OAUTH_TOKEN_URL",
            "OAUTH_CLIENT_ID", 
            "OAUTH_CLIENT_SECRET",
            "OAUTH_SCOPE"
        ]
        
        missing_vars = [var for var in required_vars if not getattr(self, var.lower().replace("oauth_", ""), None)]
        
        if missing_vars:
            logger.error(f"Missing required OAuth environment variables: {', '.join(missing_vars)}")
            raise ValueError(f"Missing required OAuth environment variables: {', '.join(missing_vars)}")
    
    def get_token(self) -> str:
        """
        Get OAuth access token using client credentials flow
        Caches token and refreshes when expired
        
        Returns:
            Access token string
            
        Raises:
            ValueError: If required environment variables are missing
            Exception: For API or network errors
        """
        import time
        
        current_time = time.time()
        
        if self._token_cache and current_time < self._token_expiry:
            logger.debug("Using cached OAuth token")
            return self._token_cache
        
        try:
            logger.info("Fetching OAuth token from Azure...")
            
            oauth_config = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": self.grant_type,
                "scope": self.scope,
            }
            
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    response = requests.post(
                        self.token_url,
                        data=oauth_config,
                        timeout=30
                    )
                    
                    if response.ok:
                        token_data = response.json()
                        access_token = token_data.get("access_token")
                        expires_in = token_data.get("expires_in", 3600)
                        
                        if not access_token:
                            logger.error("No access_token in response")
                            raise ValueError("OAuth response missing access_token")
                        
                        self._token_cache = access_token
                        self._token_expiry = current_time + expires_in - 300
                        
                        logger.info(f"✅ Successfully obtained OAuth token (expires in {expires_in}s)")
                        return access_token
                    
                    else:
                        result = response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text
                        logger.error(f"OAuth token request failed (attempt {attempt}): {result}")
                        
                        if attempt == max_retries:
                            raise Exception(f"Failed to obtain OAuth token after {max_retries} attempts: {result}")
                
                except requests.exceptions.RequestException as e:
                    logger.error(f"Network error during OAuth token request (attempt {attempt}): {str(e)}")
                    if attempt == max_retries:
                        raise Exception(f"Network error obtaining OAuth token: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in OAuth token fetcher: {str(e)}")
            raise
    
    def __call__(self) -> str:
        """
        Make the fetcher callable for use as azure_ad_token_provider
        
        Returns:
            Access token string
        """
        return self.get_token()


def get_openai_client_with_oauth(base_url: str, model: str, api_version: str = "2024-06-01") -> 'AzureOpenAI':
    """
    Returns an authenticated Azure OpenAI client using OAuth token fetcher
    
    Args:
        base_url: Azure OpenAI base URL (e.g., https://your-resource.openai.azure.com/)
        model: Deployment name (e.g., gpt-4.1-2025-04-14-eastus-dz)
        api_version: API version (default: 2024-06-01)
        
    Returns:
        Configured AzureOpenAI client using environment variables and OAuth
        
    Raises:
        EnvironmentError: If required environment variables are missing
        Exception: For API or network errors
    """
    from openai import AzureOpenAI
    
    required_env_vars = [
        "OAUTH_TOKEN_URL",
        "OAUTH_CLIENT_ID",
        "OAUTH_CLIENT_SECRET",
        "OAUTH_GRANT_TYPE",
        "OAUTH_SCOPE",
        "OA_BASE_URL"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    
    enable_oauth = os.environ.get("ENABLE_OAUTH", "true").lower() == "true"
    
    if not enable_oauth:
        logger.warning("⚠️  OAuth is disabled via ENABLE_OAUTH environment variable")
        logger.warning("⚠️  Falling back to API key authentication")
        
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        if not api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is required when OAuth is disabled")
        
        return AzureOpenAI(
            azure_endpoint=base_url,
            api_key=api_key,
            api_version=api_version
        )
    
    oauth_config = {
        "OAUTH_TOKEN_URL": os.environ.get("OAUTH_TOKEN_URL"),
        "OAUTH_CLIENT_ID": os.environ.get("OAUTH_CLIENT_ID"),
        "OAUTH_CLIENT_SECRET": os.environ.get("OAUTH_CLIENT_SECRET"),
        "OAUTH_GRANT_TYPE": os.environ.get("OAUTH_GRANT_TYPE"),
        "OAUTH_SCOPE": os.environ.get("OAUTH_SCOPE"),
    }
    
    token_fetcher = OAuthTokenFetcher(oauth_config)
    bearer_token = token_fetcher.get_token()
    
    client = AzureOpenAI(
        azure_endpoint=base_url,
        api_key=bearer_token,
        api_version=api_version
    )
    
    logger.info(f"✅ Azure OpenAI client configured with OAuth for deployment: {model}")
    
    return client
