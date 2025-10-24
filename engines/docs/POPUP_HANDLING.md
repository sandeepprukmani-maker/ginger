# Popup Window Handling

## Overview

The browser-use engine has been enhanced to automatically handle popup windows and new tabs that open during automation.

## How It Works

When a button or link opens a new window (like "Sign in with Google", "Continue with Facebook", etc.), the browser-use AI agent:

1. **Detects the new window** - Playwright automatically tracks new windows/tabs
2. **Switches context automatically** - The AI agent continues working in the new window
3. **Completes the task seamlessly** - No manual window switching required

## Enhanced System Instructions

The AI agent now receives specific instructions about popup handling:

- When a popup opens, it automatically switches to work in the new window
- All subsequent actions are performed in the active window
- Window switches happen transparently without user intervention

## Examples

### LinkedIn Sign-in with Google

**Instruction:**
```
Open https://www.linkedin.com/, click "Join now", click "Continue with Google", enter email "test@example.com", click next
```

**What happens:**
1. Opens LinkedIn
2. Clicks "Join now"
3. Clicks "Continue with Google" → **New popup window opens**
4. **Automatically switches to Google sign-in window**
5. Enters email in the popup
6. Clicks next

### Multi-Window Workflow

The agent can handle complex multi-window scenarios:
- OAuth flows (Google, Facebook, etc.)
- Payment gateways
- External verification pages
- Pop-up forms

## Configuration

The popup handling is enabled by default in browser-use engine with these optimizations:

- **LLM Timeout**: 180 seconds (increased from 60s)
- **Max Steps**: 25 steps (optimized for performance)
- **System Prompt**: Enhanced with popup handling instructions

## Best Practices

### 1. Be Explicit in Instructions
✅ **Good:** "Click 'Sign in with Google', enter email 'test@example.com' in the popup, click next"

❌ **Avoid:** "Sign in with Google" (too vague)

### 2. Break Complex Tasks into Steps
For very complex workflows, break them into smaller tasks:

**Step 1:**
```
Navigate to site.com and click "Sign in with Google"
```

**Step 2:**
```
Enter email "test@example.com" and click next
```

### 3. Use Headless Mode for Faster Performance
Headless mode (checkbox in UI) runs faster and is more reliable for popup handling.

## Troubleshooting

### Popup Not Detected
If the agent doesn't switch to a popup:

1. **Check if it's actually a popup** - Some sites use embedded forms instead
2. **Use explicit instructions** - Tell the agent to work in the new window
3. **Try Playwright MCP engine** - More granular control for complex scenarios

### Timeout Issues
If actions in popups timeout:

1. **Enable headless mode** - Faster execution
2. **Simplify the instruction** - Break into smaller steps
3. **Check network speed** - OpenAI API calls need good connectivity

## Technical Details

### Browser-Use Integration
- Built on Playwright (version 1.52+)
- Uses AI-powered element detection
- Automatically handles browser contexts

### Window Switching Logic
- Browser-use tracks all open pages/windows
- AI agent automatically works in the most recently opened window
- Falls back to main window when popups close

## Limitations

1. **Nested Popups**: Multiple levels of popups may require explicit instructions
2. **Browser Security**: Some sites block automation in popups
3. **Timing**: Very fast popup opens/closes might be missed

## Future Enhancements

Planned improvements:
- [ ] Explicit popup detection logging
- [ ] Configurable popup timeout
- [ ] Popup window priority rules
- [ ] Multi-popup orchestration
