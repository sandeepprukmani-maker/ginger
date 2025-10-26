# Azure OpenAI OAuth Authentication Setup Guide

## Overview

This browser automation application now supports Azure OpenAI with OAuth2 authentication using client credentials flow. This enables secure, token-based authentication without storing API keys.

## Configuration

### 1. Enable Azure OpenAI

Edit `config/config.ini` and set:

```ini
[azure_openai]
use_azure = true
deployment_name = gpt-4.1-2025-04-14-eastus-dz
api_version = 2024-06-01
enable_oauth = true
```

### 2. Required Environment Variables (Secrets)

Add the following secrets to your Replit Secrets (already configured):

| Variable | Description | Example |
|----------|-------------|---------|
| `OAUTH_TOKEN_URL` | Azure OAuth token endpoint | `https://login.microsoftonline.com/YOUR_TENANT_ID/oauth2/v2.0/token` |
| `OAUTH_CLIENT_ID` | Azure application (client) ID | Your Azure AD app client ID |
| `OAUTH_CLIENT_SECRET` | Azure AD app client secret | Your generated client secret |
| `OAUTH_GRANT_TYPE` | OAuth grant type | `client_credentials` |
| `OAUTH_SCOPE` | OAuth scope for Azure OpenAI | `https://cognitiveservices.azure.com/.default` |
| `OA_BASE_URL` | Azure OpenAI endpoint | `https://your-resource.openai.azure.com/` |

## How It Works

### OAuth Token Management

1. **Token Fetching**: The `OAuthTokenFetcher` class handles authentication with Azure AD
2. **Token Caching**: Tokens are cached and automatically refreshed 5 minutes before expiration
3. **Auto-Refresh**: No manual token management needed - everything is handled automatically
4. **LangChain Integration**: Tokens are provided via `azure_ad_token_provider` parameter

### Architecture

```
Browser Automation Request
    ↓
BrowserUseEngine (__init__)
    ↓
Read config.ini [use_azure=true]
    ↓
Create OAuthTokenFetcher
    ↓
Configure AzureChatOpenAI with azure_ad_token_provider
    ↓
Execute automation with Azure OpenAI
```

### Token Lifecycle

1. **First Request**: Fetches OAuth token from Azure AD
2. **Subsequent Requests**: Uses cached token (if not expired)
3. **Near Expiry**: Automatically refreshes token 5 minutes before expiration
4. **Retry Logic**: 3 retry attempts with error handling

## Usage

### Using Browser-Use Engine

Simply use the application normally - OAuth authentication is handled transparently:

1. Open the web interface
2. Select "Browser Use" engine
3. Enter your automation task
4. Click "Execute Automation"

The system will:
- Authenticate with Azure AD using OAuth
- Use your specified deployment (`gpt-4.1-2025-04-14-eastus-dz`)
- Execute browser automation with Azure OpenAI

### Switching Back to Standard OpenAI

To use standard OpenAI instead:

1. Edit `config/config.ini`
2. Set `use_azure = false` in the `[azure_openai]` section
3. Ensure `OPENAI_API_KEY` is set in secrets
4. Restart the application

## Security Features

✅ **Secrets Management**: All credentials stored in Replit Secrets (environment variables)
✅ **No Hardcoded Keys**: API keys and secrets never stored in code
✅ **Token Auto-Refresh**: Tokens automatically refreshed before expiration
✅ **Error Handling**: Comprehensive error handling with retry logic
✅ **Logging**: Detailed logging for debugging (without exposing secrets)

## Troubleshooting

### Common Issues

**Issue: "Missing required OAuth environment variables"**
- **Solution**: Verify all 6 OAuth secrets are set in Replit Secrets

**Issue: "Failed to obtain OAuth token"**
- **Solution**: Check that your Azure AD app has correct permissions
- Verify the token URL contains the correct tenant ID
- Ensure client secret hasn't expired

**Issue: "OA_BASE_URL environment variable must be set"**
- **Solution**: Add your Azure OpenAI endpoint URL to secrets

### Checking Logs

Monitor the workflow logs for OAuth-related messages:
- `🔐 Using OAuth authentication for Azure OpenAI`
- `✅ Successfully obtained OAuth token (expires in XXs)`
- `✅ Azure OpenAI configured with OAuth for deployment: ...`

## Performance

- **Token Caching**: Reduces authentication overhead
- **5-Minute Buffer**: Ensures tokens are refreshed before they expire
- **Retry Logic**: 3 attempts with exponential backoff
- **30-Second Timeout**: Per OAuth request

## Architecture Review

The implementation has been reviewed and approved with the following findings:

✅ **Correct Integration**: Properly uses LangChain's `azure_ad_token_provider`
✅ **Token Management**: Sound caching and refresh logic
✅ **Security**: No security risks observed
✅ **Error Handling**: Comprehensive validation and error messages

### Recommendations for Production

1. Monitor token refresh frequency in logs
2. Add concurrency protection for high-parallelism scenarios
3. Document OAuth requirements for operations teams

## Files Modified

- `app/utils/azure_oauth.py` - OAuth token fetcher implementation
- `app/engines/browser_use/engine.py` - Azure OpenAI integration
- `config/config.ini` - Azure OpenAI configuration section

## Support

For issues or questions:
1. Check workflow logs for error messages
2. Verify all environment variables are set correctly
3. Ensure Azure AD app permissions are configured
4. Review this documentation for common issues
