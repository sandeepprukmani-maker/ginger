# Privacy & Telemetry Configuration

## ⚠️ IMPORTANT: Disable External Data Transmission

By default, the browser-use library sends **anonymized telemetry** and **cloud sync data** to external servers. This includes:

- Task execution information
- Browser automation steps
- Agent decisions and actions
- Performance metrics
- Error reports

## 🔒 How to Ensure Nothing Leaves Your System

### Environment Variables (Required)

Add these to your `.env` file or export them in your shell:

```bash
# DISABLE ALL EXTERNAL DATA TRANSMISSION
ANONYMIZED_TELEMETRY=false
BROWSER_USE_CLOUD_SYNC=false
```

### For Local Development

If you're running locally, create/update your `.env` file in the project root:

```bash
# .env
ANONYMIZED_TELEMETRY=false
BROWSER_USE_CLOUD_SYNC=false

# Your other configuration...
OAUTH_TOKEN_URL=your-oauth-token-url
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_GRANT_TYPE=client_credentials
OAUTH_SCOPE=your-scope
GW_BASE_URL=https://your-gateway-url.com/v1
```

### For Production/Replit

Set these as **Secrets** in your Replit environment:
1. Go to Secrets (lock icon in sidebar)
2. Add secret: `ANONYMIZED_TELEMETRY` = `false`
3. Add secret: `BROWSER_USE_CLOUD_SYNC` = `false`

## What Gets Disabled

When you set these environment variables to `false`:

### ❌ Anonymized Telemetry (PostHog)
- **Disabled**: Usage analytics sent to PostHog
- **Disabled**: Feature usage tracking
- **Disabled**: Error reporting to external services
- **Disabled**: Performance metrics collection

### ❌ Cloud Sync
- **Disabled**: Agent task synchronization to browser-use cloud
- **Disabled**: Step-by-step execution logs sent to cloud
- **Disabled**: Output files uploaded to cloud storage
- **Disabled**: Agent state synchronization
- **Disabled**: Device tracking and identification

## Verification

To verify telemetry and cloud sync are disabled, check the startup logs:

```bash
# You should NOT see these messages:
"☁️  Cloud sync enabled"
"📊 Telemetry enabled"
"🔄 Syncing to browser-use cloud"
```

With detailed logging enabled (`enable_detailed_logging = true`), you'll see in the logs that no external connections are made except to your configured gateway endpoint.

## What Still Works

Everything related to your automation works normally:
- ✅ Browser automation with GPT-4.1
- ✅ Playwright MCP engine
- ✅ Browser-use engine
- ✅ Local database storage
- ✅ Screenshot/PDF generation
- ✅ All browser actions

The **ONLY** external connection is to your configured AI gateway endpoint (`GW_BASE_URL`) for LLM calls.

## Network Monitoring

To verify nothing unexpected leaves your system, you can monitor network traffic:

```bash
# Monitor outgoing connections (Linux/Mac)
sudo tcpdump -i any -n 'tcp[tcpflags] & (tcp-syn) != 0' | grep -v "your-gateway-domain"

# You should only see connections to your gateway URL
```

## Technical Details

The browser-use library has these data collection features:

1. **Telemetry** (`browser_use.telemetry`)
   - PostHog analytics client
   - Captures CLI events, task completions, errors
   - Sends to PostHog servers

2. **Cloud Sync** (`browser_use.cloud`)
   - WebSocket connection to `api.browser-use.com`
   - Sends agent tasks, steps, outputs
   - Stores device IDs and user information

Both are **completely disabled** when environment variables are set to `false`.

## Privacy-First Configuration

This is the recommended privacy-first configuration:

```ini
# config/config.ini

[logging]
enable_detailed_logging = true  # See everything locally
log_llm_requests = true         # Monitor LLM calls
log_llm_responses = true        # Verify responses
log_browser_actions = true      # Track browser actions
```

```bash
# .env

# Privacy settings
ANONYMIZED_TELEMETRY=false
BROWSER_USE_CLOUD_SYNC=false

# Only your AI gateway
GW_BASE_URL=https://your-private-gateway.com/v1
```

This ensures:
- ✅ All data stays on your system
- ✅ Only your AI gateway is contacted
- ✅ Full visibility through local logs
- ✅ No third-party services involved

## Support

If you see any unexpected network connections:
1. Enable detailed logging
2. Check the logs for external URLs
3. Verify environment variables are set correctly
4. Restart the application after changing environment variables
