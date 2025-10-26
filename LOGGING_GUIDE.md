# Detailed Logging Configuration Guide

## Overview

This application now includes comprehensive logging capabilities to help you debug and monitor browser automation tasks. The logging system is fully configurable via `config/config.ini`.

## Configuration Location

All logging settings are in `config/config.ini` under the `[logging]` section.

## Quick Start

### Enable Detailed Logging

To see everything that's happening during automation:

```ini
[logging]
enable_detailed_logging = true
```

### Disable Detailed Logging

For production or minimal output:

```ini
[logging]
enable_detailed_logging = false
```

## Configuration Options

### Log Levels

Control verbosity for different components:

```ini
# Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
# DEBUG - Most verbose, shows all internal operations
# INFO - Standard logging, shows major steps  
# WARNING - Only warnings and errors
# ERROR - Only errors
# CRITICAL - Only critical failures

app_log_level = DEBUG              # Main application logs
browser_use_log_level = DEBUG      # Browser-use library logs
agent_log_level = DEBUG            # AI agent decision logs
llm_log_level = DEBUG              # LLM API call logs
playwright_log_level = INFO        # Playwright browser logs
```

### Feature-Specific Logging

Enable/disable specific types of logging:

```ini
# LLM Communication
log_llm_requests = true    # Log every request sent to GPT-4.1
log_llm_responses = true   # Log every response from GPT-4.1

# Browser Actions
log_browser_actions = true # Log every browser action (click, fill, navigate)
log_page_state = true      # Log page state after each action

# Performance
log_performance = true     # Log timing information for operations
```

## What Gets Logged

### When `enable_detailed_logging = true`

#### Browser-Use Engine Logs

**LLM Communication:**
```
================================================================================
🔄 CALLING agent.run() - LLM will be invoked repeatedly
Model: gpt-4.1-2025-04-14-eastus-dz
Gateway URL: https://your-gateway-url.com/v1
Max steps: 25
Task: navigate to linkedin.com and click join now
================================================================================
```

**Performance Timing:**
```
⏱️  agent.run() completed in 12.45s
```

**Error Details:**
```
================================================================================
❌ AGENT.RUN() FAILED
Error Type: APIConnectionError
Error Message: Connection to gateway failed
================================================================================
[Full stack trace]
```

#### Playwright MCP Engine Logs

**LLM Requests:**
```
================================================================================
📤 LLM REQUEST (Iteration 1/10)
Model: gpt-4.1-2025-04-14-eastus-dz
Gateway: https://your-gateway-url.com/v1
Messages count: 2
Tools available: 15
================================================================================
```

**LLM Responses:**
```
================================================================================
📥 LLM RESPONSE (Iteration 1)
Finish reason: tool_calls
Tokens - Prompt: 1543, Completion: 127, Total: 1670
================================================================================
⏱️  LLM response received in 2.34s
```

**Browser Actions:**
```
================================================================================
🎬 BROWSER ACTION: browser_navigate_to
Arguments: {
  "url": "https://linkedin.com"
}
================================================================================
✅ Action 'browser_navigate_to' succeeded
⏱️  Action 'browser_navigate_to' completed in 3.21s
```

**Action Failures:**
```
================================================================================
❌ Action 'browser_click' FAILED
Error: Element not found: button[aria-label="Join now"]
================================================================================
```

## Troubleshooting Common Issues

### Issue: Browser opens but nothing happens

**Enable these logs:**
```ini
enable_detailed_logging = true
llm_log_level = DEBUG
log_llm_requests = true
log_llm_responses = true
```

**What to look for:**
- Check if LLM requests are being sent
- Look for API connection errors
- Verify OAuth token is being obtained
- Check for timeout errors

### Issue: Browser actions fail

**Enable these logs:**
```ini
enable_detailed_logging = true
browser_use_log_level = DEBUG
log_browser_actions = true
log_page_state = true
```

**What to look for:**
- Element selector errors
- Timeout waiting for elements
- Navigation failures
- Page load issues

### Issue: Slow performance

**Enable these logs:**
```ini
enable_detailed_logging = true
log_performance = true
```

**What to look for:**
- LLM response times
- Browser action durations
- Network wait times

## Example: Debug Configuration

Use this configuration when troubleshooting:

```ini
[logging]
enable_detailed_logging = true
app_log_level = DEBUG
browser_use_log_level = DEBUG
agent_log_level = DEBUG
llm_log_level = DEBUG
playwright_log_level = INFO
log_llm_requests = true
log_llm_responses = true
log_browser_actions = true
log_page_state = true
log_performance = true
```

## Example: Production Configuration

Use this configuration for production deployments:

```ini
[logging]
enable_detailed_logging = false
app_log_level = INFO
browser_use_log_level = WARNING
agent_log_level = INFO
llm_log_level = WARNING
playwright_log_level = WARNING
log_llm_requests = false
log_llm_responses = false
log_browser_actions = false
log_page_state = false
log_performance = false
```

## Log Output Location

Logs are written to:
- **Console/Terminal**: All logs appear in the application console
- **Workflow logs**: Available in the Replit workflow viewer
- **File location**: `/tmp/logs/` (temporary, rotated automatically)

## Understanding Log Messages

### Symbols

- `🚀` - Application startup
- `🔧` - Configuration loaded
- `🤖` - Agent initialization
- `🔄` - LLM call starting
- `📤` - Request sent
- `📥` - Response received
- `🎬` - Browser action
- `✅` - Success
- `❌` - Failure
- `⚠️` - Warning
- `⏱️` - Performance timing
- `📊` - Processing data

## Performance Impact

Detailed logging adds minimal overhead:
- `log_llm_requests/responses`: ~5ms per call
- `log_browser_actions`: ~2ms per action
- `log_performance`: ~1ms per operation
- `log_page_state`: ~10-20ms (depending on page size)

Total impact: < 1% for most automations

## Need Help?

If the logs show errors you don't understand:

1. Copy the full error section (between `===` lines)
2. Include the task you were trying to execute
3. Note which engine you're using (Browser-Use or Playwright MCP)
4. Share your `config/config.ini` logging settings

The detailed logs are designed to pinpoint exactly where things go wrong in the automation pipeline.
