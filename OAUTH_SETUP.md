# OAuth 2.0 Authentication Setup Guide

## Overview

Your Ginger browser automation project has been successfully refactored to use **OAuth 2.0 client credentials flow** for authentication instead of direct API keys. This provides enhanced security and works seamlessly with your gateway endpoint and GPT-4.1 model.

## What Changed

### 1. **New OAuth Authentication Module** (`auth/oauth_handler.py`)
   - `OAuthConfig`: Configuration dataclass for OAuth credentials
   - `OAuthTokenFetcher`: Handles token fetching with automatic caching and expiration management
   - `OAuthTokenManager`: Thread-safe singleton that persists tokens across requests
   - `enable_certs()`: Certificate management for secure gateway connections
   - `get_oauth_token_with_retry()`: Public API with retry logic (3 attempts by default)

### 2. **Engine Updates**
   All browser automation engines now use OAuth tokens:
   - `app/engines/browser_use/engine.py` - Browser-Use engine
   - `app/engines/browser_use/engine_optimized.py` - Optimized Browser-Use engine
   - `app/engines/playwright_mcp/agent/conversation_agent.py` - Playwright MCP agent

### 3. **Environment Configuration**
   Updated `.env.example` with OAuth variables (see below)

### 4. **Application Startup**
   `main.py` now validates OAuth configuration on startup

### 5. **Documentation**
   Updated `replit.md` to reflect OAuth authentication architecture

## Required Environment Variables

You **must** set these environment variables for the application to work:

```bash
OAUTH_TOKEN_URL=https://your-oauth-provider.com/oauth/token
OAUTH_CLIENT_ID=your_client_id_here
OAUTH_CLIENT_SECRET=your_client_secret_here
OAUTH_GRANT_TYPE=client_credentials
OAUTH_SCOPE=your_required_scope
GW_BASE_URL=https://your-gateway-endpoint.com/v1
```

### Additional Variables (existing)
```bash
SESSION_SECRET=your_secret_key_here
DATABASE_URL=postgresql://user:password@localhost/dbname
CORS_ALLOWED_ORIGINS=*
```

## How It Works

### Token Lifecycle

1. **Initialization**: On first request, `OAuthTokenManager` creates a token fetcher
2. **Token Fetch**: Fetcher requests OAuth token from `OAUTH_TOKEN_URL` using client credentials
3. **Caching**: Token is cached in memory with expiration time
4. **Automatic Refresh**: Token is refreshed 300 seconds (5 minutes) before expiration
5. **Reuse**: Subsequent requests use the cached token until it expires

### Thread Safety

The `OAuthTokenManager` uses a singleton pattern with threading locks to ensure:
- Only one token fetcher instance exists across all requests
- Concurrent requests share the same cached token
- No race conditions during token refresh

### Error Handling

- **Missing Variables**: Application validates all OAuth variables on startup
- **Token Fetch Failures**: Automatic retry with 3 attempts
- **Gateway Errors**: Clear error messages with troubleshooting hints

## Testing Your Setup

### 1. Verify Environment Variables

Run the application and check the startup logs:

```bash
python main.py
```

Expected output:
```
================================================================================
🚀 AI BROWSER AUTOMATION - STARTING UP
================================================================================
✅ OAuth configuration found
✅ Gateway URL: https://your-gateway-endpoint.com/v1
```

### 2. Test Token Fetching

The application will automatically fetch tokens when needed. Monitor logs for:
```
OAuth token refreshed. Expires in 3600s, will refresh after 300s
```

### 3. Test Browser Automation

Use the web interface or API to execute a simple automation task:
```json
{
  "instruction": "Navigate to google.com",
  "engine": "browser_use",
  "headless": true
}
```

## Model Configuration

The default model has been updated to **GPT-4.1** (`gpt-4.1-2025-04-14-eastus-dz`), which is optimized for coding tasks and compatible with browser-use library.

You can change the model in `config/config.ini`:
```ini
[openai]
model = gpt-4.1-2025-04-14-eastus-dz
```

## Troubleshooting

### Error: "Missing required environment variables"
**Solution**: Ensure all OAuth variables are set in your environment or `.env` file

### Error: "Failed to obtain OAuth token"
**Possible causes**:
- Invalid client credentials
- Incorrect token URL
- Network/firewall issues
- SSL certificate problems

**Solution**: 
- Verify credentials with your OAuth provider
- Check certificate configuration (use `enable_certs()`)
- Review network access to the token endpoint

### Error: "Gateway endpoint not responding"
**Solution**: 
- Verify `GW_BASE_URL` is correct
- Ensure the gateway is accessible from your network
- Check if the model name is supported by your gateway

## Security Best Practices

✅ **Never commit credentials to version control**  
✅ **Use environment variables for all secrets**  
✅ **Tokens are cached in memory only (not persisted to disk)**  
✅ **Automatic token refresh prevents long-lived tokens**  
✅ **Thread-safe implementation for production use**  

## Compatibility

- ✅ **browser-use library**: Fully compatible via `base_url` parameter
- ✅ **GPT-4.1 model**: Default model optimized for browser automation
- ✅ **Gateway architecture**: Custom endpoints supported
- ✅ **Multi-threaded Flask**: Thread-safe singleton pattern
- ✅ **Token caching**: Reduces API calls and prevents rate limiting

## Next Steps

1. Set up your OAuth credentials in the Replit Secrets or `.env` file
2. Start the application and verify OAuth configuration
3. Test browser automation with a simple task
4. Monitor logs for token refresh behavior
5. Deploy to production when ready

For questions or issues, refer to `replit.md` for full architecture documentation.
