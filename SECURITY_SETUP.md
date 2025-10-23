# Security Setup Guide

This document describes the security features implemented in the AI Browser Automation application and how to configure them.

## Security Features

### 1. API Authentication

The application now supports optional API key authentication to protect automation endpoints from unauthorized access.

#### Setup

Set the `API_KEY` environment variable to enable authentication:

```bash
export API_KEY=your-secure-api-key-here
```

If `API_KEY` is not set, authentication is disabled (development mode).

#### Usage

Clients must provide the API key in one of two ways:

**Option 1: HTTP Header (Recommended)**
```http
POST /api/execute
X-API-Key: your-secure-api-key-here
Content-Type: application/json

{
  "instruction": "Go to example.com",
  "engine": "hybrid",
  "headless": false
}
```

**Option 2: Query Parameter**
```http
POST /api/execute?api_key=your-secure-api-key-here
Content-Type: application/json

{
  "instruction": "Go to example.com",
  "engine": "hybrid",
  "headless": false
}
```

### 2. Rate Limiting

Built-in rate limiting prevents abuse and cost exhaustion from excessive API calls.

**Default Limits:**
- 10 requests per minute per IP address
- Automatic cleanup of old request records

**Rate Limit Response:**
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again in 45 seconds.",
  "retry_after": 45
}
```

#### Customization

Edit `app/middleware/security.py` to adjust rate limits:

```python
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
```

### 3. Input Validation

All API inputs are validated before processing:

- **Instruction**: Required, non-empty, max 5000 characters
- **Engine Type**: Must be one of: `hybrid`, `browser_use`, `playwright_mcp`
- **Headless**: Must be a boolean value

Invalid requests return 400 Bad Request with descriptive error messages.

### 4. CORS Configuration

Cross-Origin Resource Sharing (CORS) is configured to control which domains can access the API.

#### Setup

Set the `CORS_ALLOWED_ORIGINS` environment variable:

```bash
# Allow all origins (development)
export CORS_ALLOWED_ORIGINS="*"

# Allow specific origins (production)
export CORS_ALLOWED_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

**Default:** `*` (all origins allowed)

#### Configuration

CORS is configured for:
- Routes: `/api/*`
- Methods: `GET`, `POST`, `OPTIONS`
- Headers: `Content-Type`, `X-API-Key`
- Credentials: Supported

### 5. Error Sanitization

Internal error details are sanitized before being returned to clients to prevent information leakage.

**Internal Error:**
```
OpenAI API error: Invalid API key sk-proj-...
```

**User-Facing Error:**
```json
{
  "success": false,
  "error": "Internal error",
  "message": "AI service error. Please try again later."
}
```

### 6. Timeout Protection

All automation requests have a 5-minute timeout to prevent runaway operations:

- Cross-platform implementation (works on Windows, Linux, macOS)
- Uses threading-based timeout instead of signals
- Returns 408 Request Timeout on expiration

**Important Limitation**: Due to Python's threading model, the timeout returns the HTTP response promptly but cannot forcefully terminate the underlying execution thread. The automation may continue running in the background until it completes naturally. To fully terminate stuck operations:

- The timeout triggers cleanup of cached engine instances
- Playwright processes are reset to prevent reuse of hung sessions
- Future requests use fresh engine instances

**Recommendation for Production**: For critical applications requiring hard termination, consider implementing:
- Process-level isolation (run engines in separate processes)
- Resource monitoring and automatic process killing
- Container-level timeouts (Docker, Kubernetes)

### 7. Process Monitoring

The engine orchestrator includes automatic recovery for crashed subprocesses:

- Detects Playwright MCP subprocess failures
- Automatically reinitializes crashed engines
- Cleans up zombie processes
- Logs all recovery attempts

## Environment Variables Summary

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for AI automation |
| `API_KEY` | No | - | API key for endpoint authentication |
| `CORS_ALLOWED_ORIGINS` | No | `*` | Comma-separated list of allowed origins |
| `SESSION_SECRET` | Recommended | - | Flask session secret key |

## Production Deployment Checklist

- [ ] Set `API_KEY` to a strong random value
- [ ] Set `CORS_ALLOWED_ORIGINS` to specific allowed domains
- [ ] Set `SESSION_SECRET` to a secure random value
- [ ] Configure rate limits for expected traffic
- [ ] Enable HTTPS with reverse proxy (nginx/Apache)
- [ ] Monitor logs for authentication failures
- [ ] Set up alerting for rate limit violations
- [ ] Regularly rotate API keys

## Security Best Practices

1. **Never commit secrets to version control**
   - Use environment variables for all secrets
   - Add `.env` files to `.gitignore`

2. **Use HTTPS in production**
   - API keys transmitted over HTTP can be intercepted
   - Configure SSL/TLS with a reverse proxy

3. **Monitor API usage**
   - Track OpenAI API costs
   - Monitor authentication failures
   - Alert on unusual traffic patterns

4. **Rotate credentials regularly**
   - Change `API_KEY` periodically
   - Update `OPENAI_API_KEY` if compromised

5. **Limit attack surface**
   - Use specific CORS origins in production
   - Configure firewall rules
   - Use rate limiting to prevent DoS

## Testing Authentication

Test that authentication is working:

```bash
# Without API key (should fail if API_KEY is set)
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"instruction": "test"}'

# With valid API key (should succeed)
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"instruction": "Go to example.com", "engine": "hybrid"}'
```

## Health Check

The `/health` endpoint shows security status:

```bash
curl http://localhost:5000/health
```

Response includes:
```json
{
  "status": "healthy",
  "security": {
    "authentication": "enabled",
    "rate_limiting": "enabled"
  }
}
```

## Support

For security issues or questions, please review the application logs and check the troubleshooting section in README.md.
