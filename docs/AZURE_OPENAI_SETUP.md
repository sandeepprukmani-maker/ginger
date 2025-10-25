# Azure OpenAI with OAuth Setup Guide

This application is configured to work **exclusively** with Azure OpenAI using OAuth authentication.

## 🎯 Overview

This browser automation engine uses Azure OpenAI with OAuth token authentication. All API key-based authentication has been removed - the application only works with your Azure OpenAI setup.

## ✅ Requirements

1. **Environment Variables** (all required):
   ```bash
   OAUTH_TOKEN_URL=https://your-token-endpoint/oauth/token
   OAUTH_CLIENT_ID=your-client-id
   OAUTH_CLIENT_SECRET=your-client-secret
   OAUTH_GRANT_TYPE=client_credentials
   OAUTH_SCOPE=your-scope
   GM_BASE_URL=https://your-azure-endpoint.openai.azure.com/
   ```

2. **Model Configuration** in `config/config.ini`:
   ```ini
   [openai]
   model = gpt-4.1-2025-04-14-eastus-dz  # Your Azure deployment name
   timeout = 180
   use_chat_browser_use = false
   
   [azure]
   api_version = 2024-08-01-preview  # Azure API version
   ```

3. **Custom OAuth Module** (your `genai_gateway_tools` package)

## 🚀 How It Works

### Authentication Flow

1. Engine checks for Azure OAuth environment variables
2. Imports your custom OAuth token fetcher
3. Retrieves OAuth token using your credentials
4. Initializes `AzureChatOpenAI` with the token
5. Browser-use works seamlessly with Azure OpenAI!

## 📝 Setup Steps

### 1. Set Environment Variables

In your **local** environment (not Replit), set these variables:

```bash
# Linux/macOS (.bashrc or .zshrc)
export OAUTH_TOKEN_URL="https://your-token-endpoint/oauth/token"
export OAUTH_CLIENT_ID="your-client-id"
export OAUTH_CLIENT_SECRET="your-client-secret"
export OAUTH_GRANT_TYPE="client_credentials"
export OAUTH_SCOPE="your-scope"
export GM_BASE_URL="https://your-azure-endpoint.openai.azure.com/"

# Windows (PowerShell)
$env:OAUTH_TOKEN_URL="https://your-token-endpoint/oauth/token"
$env:OAUTH_CLIENT_ID="your-client-id"
# ... etc
```

Or use a `.env` file:
```bash
# .env file
OAUTH_TOKEN_URL=https://your-token-endpoint/oauth/token
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_GRANT_TYPE=client_credentials
OAUTH_SCOPE=your-scope
GM_BASE_URL=https://your-azure-endpoint.openai.azure.com/
```

### 2. Update Config File

Edit `config/config.ini`:

```ini
[azure]
# Azure OpenAI configuration with OAuth authentication
# Model deployment name - update this to match your Azure deployment name
model = gpt-4.1-2025-04-14-eastus-dz
# API version for Azure OpenAI
api_version = 2024-08-01-preview
# Timeout for API requests (seconds)
timeout = 180
```

### 3. Ensure OAuth Module Is Available

Make sure your `genai_gateway_tools` package is installed:

```bash
# If it's a local package
pip install -e /path/to/genai_gateway_tools

# Or add it to your PYTHONPATH
export PYTHONPATH="/path/to/genai_gateway_tools:$PYTHONPATH"
```

### 4. Run the Application

```bash
python main.py
```

You should see:
```
🔐 Using Azure OpenAI with OAuth authentication
📍 Endpoint: https://your-azure-endpoint.openai.azure.com/
🤖 Model: gpt-4.1-2025-04-14-eastus-dz
```

## 🔧 Customizing OAuth Integration

If you need to customize the OAuth logic, edit `app/utils/azure_oauth.py`:

```python
def get_azure_openai_token() -> str:
    # Your custom OAuth token retrieval logic here
    # Example: copy logic from your get_openai_client() function
    pass
```

## 🐛 Troubleshooting

### "Missing required environment variables"

**Problem**: Not all OAuth variables are set

**Solution**: Verify all 6 required variables are set:
```bash
env | grep -E "OAUTH|GM_BASE_URL"
```

### "Custom OAuth module not available"

**Problem**: `genai_gateway_tools` package not found

**Solutions**:
1. Install the package: `pip install -e /path/to/package`
2. Add to PYTHONPATH: `export PYTHONPATH="/path:$PYTHONPATH"`
3. Update `app/utils/azure_oauth.py` with your OAuth logic

### "Unable to complete the search... tools not available"

**Problem**: Model doesn't support function calling

**Solution**: Your Azure model `gpt-4.1-2025-04-14-eastus-dz` DOES support function calling. This error means:
- OAuth token might be invalid/expired
- Model name mismatch (check deployment name in Azure portal)
- API version incompatibility

**Check**:
```bash
# Verify your Azure deployment name matches config.ini
# Azure Portal → OpenAI → Deployments → Copy deployment name
```

## ✅ Verification

Test that it works:

```bash
# Start the application
python main.py

# Try a simple automation
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "Go to google.com and search for dogs",
    "engine": "browser_use",
    "headless": false
  }'
```

You should see the browser open, navigate to Google, and perform the search!

## 📚 Model Compatibility

### ✅ Compatible Azure Models (with function calling):
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-4`
- `gpt-4.1-2025-04-14-eastus-dz` (Your deployment)

### ❌ NOT Compatible:
- `gpt-3.5-turbo` (older versions without function calling)

## 🔄 Azure OpenAI Only

This application is configured to work **exclusively with Azure OpenAI**:

- ✅ Requires: `OAUTH_TOKEN_URL`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_GRANT_TYPE`, `OAUTH_SCOPE`, `GM_BASE_URL`
- ❌ Does NOT use: `OPENAI_API_KEY` (removed)
- ✅ Uses: OAuth token authentication only

## 🎉 Success!

Once configured, browser-use will seamlessly work with your Azure OpenAI deployment using OAuth authentication!
