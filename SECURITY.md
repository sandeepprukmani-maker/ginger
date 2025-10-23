# Security Guidelines

## API Key Management

### ✅ DO: Use Environment Variables

**Always** store sensitive credentials as environment variables:

```bash
# Replit Secrets (Recommended for Replit environment)
OPENAI_API_KEY=sk-...
SESSION_SECRET=your-random-secret-key
```

In Replit:
1. Click the lock icon (🔒) in the left sidebar
2. Add `OPENAI_API_KEY` with your OpenAI API key
3. `SESSION_SECRET` is automatically provided by Replit

### ❌ DON'T: Store Keys in Config Files

**Never** commit API keys to config.ini or any other files in version control:

```ini
# ❌ BAD - Don't do this!
[openai]
api_key = sk-proj-abc123...  # NEVER commit this!

# ✅ GOOD - Config files should only have non-sensitive settings
[openai]
model = gpt-4o-mini
```

## Flask Security

### Session Secret Key

The application uses `SESSION_SECRET` from environment variables to maintain secure user sessions:

```python
# ✅ Correct - Uses environment variable
app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET")

# ❌ Incorrect - Regenerates on every restart, breaking sessions
app.config['SECRET_KEY'] = os.urandom(24)
```

Replit automatically provides `SESSION_SECRET`, so no manual configuration is needed.

## Best Practices

### 1. Rotate Exposed Keys Immediately

If you accidentally commit an API key:
1. **Immediately** rotate the key at https://platform.openai.com/api-keys
2. Remove the key from your code
3. Add the new key to Replit Secrets
4. Consider using `git filter-branch` to remove from history (advanced)

### 2. Use `.gitignore`

Ensure sensitive files are never committed:

```gitignore
# Already included in this project
.env
config.ini
*.secret
*.key
.replit
```

### 3. Principle of Least Privilege

Only request the permissions your application needs:
- For OpenAI: Use API keys with minimal scopes
- For browser automation: Run in headless mode in production

### 4. Regular Security Audits

- Review dependencies for vulnerabilities: `pip list --outdated`
- Keep packages updated
- Monitor API key usage for unusual activity

## Reporting Security Issues

If you discover a security vulnerability:
1. **Do NOT** open a public issue
2. Contact the maintainer privately
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Features in This Application

✅ **Secrets Management**: All API keys loaded from environment variables  
✅ **Session Security**: Stable SECRET_KEY from Replit Secrets  
✅ **Request Timeouts**: 5-minute timeout prevents resource exhaustion  
✅ **Error Handling**: Errors don't expose sensitive information  
✅ **Logging**: Sensitive data never logged  

## Compliance

This application follows:
- OWASP Top 10 security best practices
- Python security guidelines
- Flask security recommendations
- OpenAI API security guidelines
