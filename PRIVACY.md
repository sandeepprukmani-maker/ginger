# Privacy & Data Protection

This is a **privacy-focused, local-only** version of browser-use. All telemetry, analytics, and external data sharing have been **permanently removed**.

## What Data Stays Local?

**EVERYTHING except your LLM API calls.**

All browser automation, task execution, screenshots, and data processing happen entirely on your machine. The only external communication is:
- **API calls to your chosen LLM provider** (OpenAI, Anthropic, Google, etc.) - only if you use cloud LLMs
- **NO communication** if you use Ollama (fully local LLM)

## What Has Been Removed?

### 1. Telemetry System (Completely Gutted)
- ✅ PostHog analytics **completely removed**
- ✅ All telemetry API keys **deleted**
- ✅ All telemetry capture calls **disabled**
- ✅ User tracking **eliminated**
- ✅ Usage statistics collection **removed**

**Files Modified:**
- `browser_use/telemetry/service.py` - Now a no-op service
- `browser_use/config.py` - Telemetry hardcoded to False

### 2. Cloud Sync (Permanently Disabled)
- ✅ Cloud event reporting **disabled**
- ✅ Cloud authentication **removed**
- ✅ External API connections **eliminated**
- ✅ Automation run data sharing **blocked**
- ✅ All browser-use.com API calls **removed**

**Files Modified:**
- `browser_use/sync/service.py` - Now a no-op service
- `browser_use/sync/auth.py` - Authentication disabled
- `browser_use/agent/cloud_events.py` - Events are no-ops
- `browser_use/config.py` - Cloud URLs removed

### 3. External Connections Removed
- ❌ `https://eu.i.posthog.com` - PostHog analytics server
- ❌ `https://api.browser-use.com` - Cloud API for sync and auth
- ❌ `https://cf.browser-use.com` - Cloud CDN (logo and assets)
- ❌ `https://cloud.browser-use.com` - Cloud UI portal
- ❌ `https://pypi.org` - Version check calls
- ❌ Cloud browser service - Remote browser connections

**All external URLs have been removed, disabled, or set to empty strings.**

**Files Modified:**
- `browser_use/browser/cloud.py` - Cloud browser disabled, raises errors
- `browser_use/utils.py` - Version check returns None without calling PyPI
- `browser_use/config.py` - All cloud URLs set to empty strings

### 4. Branding Removed
- ✅ Bouncing logo animation **removed** from browser tabs
- ✅ Cloud branding **eliminated**
- ✅ Privacy-focused UI implemented

**File Modified:**
- `browser_use/browser/watchdogs/aboutblank_watchdog.py`

## What Gets Sent to LLM Providers?

When you use cloud LLM providers (OpenAI, Anthropic, Google), the following is sent:
- Task description you provide
- Web page content being automated
- Screenshots (if vision is enabled)
- Action history for context

This is **necessary for AI automation** and goes directly to your chosen LLM provider, not to browser-use servers.

### Using Ollama for 100% Local Operation

To ensure **ZERO external data sharing**:
1. Install Ollama: https://ollama.ai
2. Download a model: `ollama pull llama3.2`
3. Select "Ollama (Local)" in the app
4. All processing happens on your machine

## Complete List of Removed External Connections

### 1. Telemetry & Analytics
- `https://eu.i.posthog.com/capture` - Event tracking endpoint
- PostHog API key: `phc_F8JMNjW1i2KbGUTaW1unnDdLSPCoyc52SGRU0JecaUh` (removed)
- User ID tracking (disabled)
- Device fingerprinting (disabled)

### 2. Cloud Services
- `https://api.browser-use.com/api/v1/events` - Event sync endpoint
- `https://api.browser-use.com/api/v2/browsers` - Cloud browser creation
- `https://api.browser-use.com/oauth/device` - OAuth authentication
- Cloud session management (disabled)
- Cloud file upload (disabled)

### 3. CDN & Assets
- `https://cf.browser-use.com/logo.svg` - Logo loading
- Cloud-hosted assets (disabled)

### 4. Version Checking
- `https://pypi.org/pypi/browser-use/json` - Version check API
- Update notifications (disabled)

### 5. All httpx/requests Calls Removed
Except for necessary LLM provider API calls (OpenAI, Anthropic, Google, etc.)

## Verification

You can verify no external connections by:

1. **Running the test script:**
   ```bash
   uv run python test_local.py
   ```

2. **Monitoring network traffic:**
   - Use tools like Wireshark or Little Snitch
   - Block all connections except to your LLM provider
   - The app will work perfectly

3. **Code inspection:**
   - Check `browser_use/telemetry/service.py` - all methods are no-ops
   - Check `browser_use/sync/service.py` - cloud sync always disabled
   - Check `browser_use/config.py` - telemetry and sync hardcoded to False

## Technical Details

### No User Tracking
- No user IDs sent externally
- No device fingerprinting
- No session tracking to external servers
- Local device ID stays local

### No Analytics
- No event tracking
- No usage statistics
- No error reporting to external servers
- No performance metrics sent externally

### No Cloud Services
- No cloud browser connections
- No cloud authentication
- No cloud storage
- No cloud sync

## Data That Stays On Your Machine

✅ Browser automation sessions  
✅ Screenshots and recordings  
✅ Task history  
✅ Execution logs  
✅ Configuration files  
✅ Browser profiles  
✅ Downloaded files  
✅ Automation results  

## Questions?

**Q: Can browser-use track what I'm automating?**  
A: No. All telemetry and cloud sync has been permanently removed.

**Q: Does any data leave my machine?**  
A: Only API calls to your chosen LLM provider (or nothing if using Ollama).

**Q: Can I verify this?**  
A: Yes. Run `test_local.py` or inspect the modified source files.

**Q: Will future updates re-enable telemetry?**  
A: This is a forked, privacy-focused version. All tracking is permanently removed.

## License

This privacy-focused version maintains the MIT license of the original browser-use project.

---

**Your automation data is yours. Period.** 🔒
