# Playwright Code Generation - Feature Matrix

## Overview

All automation engines now support automatic Playwright code generation! 🎉

## Engine Support Matrix

| Engine | Code Generation | Selector Quality | Best For |
|--------|----------------|------------------|----------|
| **Browser-Use (Basic)** | ✅ YES | ⭐⭐⭐⭐⭐ Excellent | AI-discovered selectors |
| **Browser-Use (Optimized)** | ✅ YES | ⭐⭐⭐⭐⭐ Excellent | Fast + AI-discovered |
| **Playwright MCP** | ✅ YES | ⭐⭐⭐⭐ Good | Tool-based automation |
| **Hybrid** | ✅ YES | ⭐⭐⭐⭐⭐ Excellent | Best of both worlds |

## How To Use

### Via API (Works with ALL engines)

```python
import requests

# Choose any engine!
engines = ['browser_use', 'browser_use_optimized', 'playwright_mcp', 'hybrid']

for engine in engines:
    response = requests.post('http://localhost:5000/api/automation/execute',
        headers={'X-API-Key': 'your-key'},
        json={
            'instruction': 'Go to Google and search for Python',
            'engine': engine
        }
    )
    
    result = response.json()
    
    # All engines return playwright_code
    if 'playwright_code' in result:
        with open(f'{engine}_script.py', 'w') as f:
            f.write(result['playwright_code'])
        print(f"✅ {engine}: Code generated!")
```

### Programmatic

#### Browser-Use

```python
from browser_use_codebase.playwright_code_generator import generate_playwright_code_from_history

# After running browser-use
history = await agent.run()
code = generate_playwright_code_from_history(history)
```

#### Playwright MCP

```python
from playwright_mcp_codebase.mcp_code_generator import generate_playwright_code_from_mcp_steps

# After running MCP automation
result = agent.execute_instruction("Search Google")
code = generate_playwright_code_from_mcp_steps(result['steps'])
```

## Engine-Specific Characteristics

### Browser-Use Engines

**Strengths:**
- ✅ AI discovers working selectors automatically
- ✅ Handles dynamic content excellently
- ✅ 90%+ ready-to-run code
- ✅ Best for exploration

**Generated Code:**
```python
# Selectors that AI actually used successfully
SEARCH_BOX = r"textarea[name='q']"
SEARCH_BUTTON = r"input[value='Google Search']"

await page.locator(SEARCH_BOX).fill("Python")
await page.locator(SEARCH_BUTTON).click()
```

### Playwright MCP Engine

**Strengths:**
- ✅ Clean tool-based automation
- ✅ Direct mapping: tool calls → Playwright code
- ✅ Good for structured workflows
- ✅ Deterministic steps

**Generated Code:**
```python
# Tool-based actions converted to Playwright
await page.goto("https://www.google.com")
await page.locator(INPUT_EMAIL).fill(email)
await page.keyboard.press("Enter")
```

**Note**: May include element references that need manual conversion:
```python
# Click element by reference (convert to specific selector)
# Original ref: e1
```

### Hybrid Engine

**Strengths:**
- ✅ Uses Browser-Use first (best selectors)
- ✅ Falls back to MCP for reliability
- ✅ Best overall code quality
- ✅ Recommended for production

**Generated Code:**
Inherits from whichever engine successfully completed the task.

## Code Quality Comparison

### Selector Reliability

```python
# Browser-Use: Discovered selectors (Excellent)
LINK_SIGNIN = r"a[data-testid='signin']"  # AI found this works

# Playwright MCP: Tool-specified selectors (Good)
LINK_SIGNIN = r"a:text('Sign In')"  # MCP used this

# Both work, but Browser-Use tends to find more robust selectors
```

### Completeness

| Aspect | Browser-Use | Playwright MCP | Hybrid |
|--------|------------|----------------|--------|
| Navigation | ✅ Complete | ✅ Complete | ✅ Complete |
| Clicks | ✅ Complete | ⚠️ May need ref conversion | ✅ Complete |
| Form Fills | ✅ Complete | ⚠️ May need ref conversion | ✅ Complete |
| Waits | ✅ Complete | ✅ Complete | ✅ Complete |
| Comments | ✅ Descriptive | ✅ Tool-based | ✅ Descriptive |

## When To Use Each Engine

### Use Browser-Use When:
- 🔍 Exploring new workflows
- 🎯 Need AI to discover selectors
- 📝 Creating initial automation scripts
- 🧪 Generating test scaffolds

### Use Playwright MCP When:
- 🔧 You have known selectors
- 📊 Structured, deterministic tasks
- ⚡ Want faster execution
- 🎭 Tool-based approach preferred

### Use Hybrid When:
- 🏆 Want best of both worlds
- 🛡️ Need reliability + quality
- 🚀 Production use cases
- ❓ Unsure which to use (default recommendation)

## Demo Scripts

### Browser-Use Code Generation
```bash
python examples/generate_playwright_code_demo.py
```

### Playwright MCP Code Generation
```bash
python examples/mcp_code_generation_demo.py
```

## Complete Example: All Engines

```python
import requests

instruction = "Go to GitHub trending repos and click the first Python repo"

# Test all engines
engines = {
    'browser_use': 'AI-Powered Browser-Use',
    'browser_use_optimized': 'Optimized Browser-Use (10X faster stopping)',
    'playwright_mcp': 'Tool-Based Playwright MCP',
    'hybrid': 'Hybrid Intelligence (Recommended)'
}

for engine_id, engine_name in engines.items():
    print(f"\n{'='*60}")
    print(f"Testing: {engine_name}")
    print('='*60)
    
    response = requests.post('http://localhost:5000/api/automation/execute',
        headers={'X-API-Key': 'your-api-key'},
        json={
            'instruction': instruction,
            'engine': engine_id
        }
    )
    
    result = response.json()
    
    if result['success']:
        print(f"✅ Success!")
        print(f"   Steps: {len(result.get('steps', []))}")
        
        if 'playwright_code' in result:
            print(f"   Playwright code: Generated ✅")
            
            # Save to file
            filename = f"generated_{engine_id}.py"
            with open(filename, 'w') as f:
                f.write(result['playwright_code'])
            print(f"   Saved to: {filename}")
        else:
            print(f"   Playwright code: Not generated ❌")
    else:
        print(f"❌ Failed: {result.get('error')}")
```

## Advanced: Custom Code Generation

### Browser-Use Custom Generation

```python
from browser_use_codebase.playwright_code_generator import PlaywrightCodeGenerator

generator = PlaywrightCodeGenerator(
    history=agent_history,
    task_description="Custom automation task"
)

# Customize output
code = generator.generate_python_code(
    use_locators=True,        # Extract reusable locators
    include_comments=True,     # Add step comments
    async_style=True          # async/await (recommended)
)
```

### Playwright MCP Custom Generation

```python
from playwright_mcp_codebase.mcp_code_generator import MCPCodeGenerator

generator = MCPCodeGenerator(
    steps=mcp_steps,
    task_description="MCP automation task"
)

code = generator.generate_python_code(
    use_locators=True,
    include_comments=True,
    async_style=True
)
```

## Tips for Best Results

### 1. Choose the Right Engine

- **New workflow?** → Browser-Use (discovers selectors)
- **Known workflow?** → Playwright MCP (faster)
- **Production?** → Hybrid (reliable)
- **Not sure?** → Hybrid (recommended)

### 2. Review Generated Code

Always review before production use:
- ✅ Check selectors are specific enough
- ✅ Verify waits are appropriate
- ✅ Add error handling
- ✅ Add assertions for tests

### 3. Enhance Generated Code

Use generated code as foundation:
```python
# Generated (starting point)
await page.locator(BUTTON).click()

# Enhanced (production-ready)
await page.locator(BUTTON).wait_for(state='visible')
await page.locator(BUTTON).click()
await expect(page.locator(SUCCESS_MSG)).to_be_visible()
```

### 4. Version Control

Commit generated scripts:
```bash
git add automation_scripts/
git commit -m "Add Playwright scripts for checkout flow"
```

## Troubleshooting

### "No playwright_code in response"

Check:
1. Engine supports code generation (all do now!)
2. Automation completed successfully
3. Check logs for generation errors

### "Selectors not working"

- **Browser-Use**: Should work (AI-discovered)
- **Playwright MCP**: May need ref conversion
- **Solution**: Use Playwright Inspector to find better selectors

### "Code incomplete"

Some complex actions need manual implementation:
```python
# Generated comment:
# Scroll action (implement page.evaluate for scrolling)

# Implement:
await page.evaluate("window.scrollBy(0, 500)")
```

## Documentation

- [Main Code Generation Guide](docs/PLAYWRIGHT_CODE_GENERATION.md)
- [MCP-Specific Guide](docs/MCP_CODE_GENERATION.md)
- [Quick Start](PLAYWRIGHT_CODE_GENERATION_QUICKSTART.md)

## Support

Questions?
- Check documentation above
- Review demo scripts
- Examine generated code examples
