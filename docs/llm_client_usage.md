# LLM Client Module

## Overview

The `llm_client.py` module provides a centralized interface for creating and managing OpenAI clients across the entire project. This ensures consistent configuration, easier maintenance, and separation of concerns.

## Features

- **Centralized API Key Management**: Single point of configuration for OpenAI API keys
- **Service-Specific Clients**: Pre-configured clients for different services
- **Model Configuration**: Each service can use different models
- **Singleton Pattern**: Efficient reuse of client instances
- **Type-Safe**: Full type hints for better IDE support

## Usage

### Basic Usage

```python
from llm_client import get_browser_use_client, get_playwright_mcp_client

# Get ChatOpenAI client for browser-use
browser_use_llm = get_browser_use_client()

# Get OpenAI client for Playwright MCP
mcp_client = get_playwright_mcp_client()
mcp_model = get_playwright_mcp_model()  # Get the configured model name
```

### Advanced Usage

```python
from llm_client import LLMClientFactory

# Create factory with custom API key
factory = LLMClientFactory(api_key="your-api-key-here")

# Get clients with custom models
browser_llm = factory.get_browser_use_client(model="gpt-4")
automation_llm = factory.get_automation_engine_client(model="gpt-4o-mini")
```

## Available Clients

### 1. Browser-Use Client
**Function**: `get_browser_use_client(model: Optional[str] = None) -> ChatOpenAI`
- Default Model: `gpt-4o-mini`
- Used by: `src/web/services/browser_use/engine.py`
- Purpose: Powers natural language browser automation

### 2. Playwright MCP Client
**Function**: `get_playwright_mcp_client(model: Optional[str] = None) -> OpenAI`
- Default Model: `gpt-4o-mini`
- Used by: `src/web/services/playwright_mcp/browser_agent.py`
- Purpose: Intelligent browser control via MCP tools

**Function**: `get_playwright_mcp_model() -> str`
- Returns: The configured model name for Playwright MCP

### 3. Automation Engine Client
**Function**: `get_automation_engine_client(model: Optional[str] = None) -> ChatOpenAI`
- Default Model: `gpt-4o-mini`
- Used by: `src/automation/automation_engine.py`
- Purpose: Core automation engine

### 4. Self-Healing Client
**Function**: `get_self_healing_client(model: Optional[str] = None) -> ChatOpenAI`
- Default Model: `gpt-4o-mini`
- Used by: `src/automation/self_healing_executor.py`
- Purpose: AI-powered locator healing and recovery

## Configuration

The module uses the `OPENAI_API_KEY` environment variable by default. You can also provide the API key explicitly:

```python
from llm_client import LLMClientFactory

factory = LLMClientFactory(api_key="sk-...")
```

## Model Configuration

To change the default model for a service, modify the class constants in `llm_client.py`:

```python
class LLMClientFactory:
    BROWSER_USE_MODEL = "gpt-4o-mini"
    PLAYWRIGHT_MCP_MODEL = "gpt-4o-mini"
    AUTOMATION_ENGINE_MODEL = "gpt-4o-mini"
    SELF_HEALING_MODEL = "gpt-4o-mini"
```

## Benefits

1. **Single Source of Truth**: All OpenAI client configuration in one place
2. **Easy Updates**: Change models or settings without touching multiple files
3. **Consistent Error Handling**: Centralized validation and error messages
4. **Testing**: Easy to mock and test with the singleton pattern
5. **Security**: API keys managed in one secure location

## Migration Guide

### Before (Old Pattern)
```python
import os
from langchain_openai import ChatOpenAI

api_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)
```

### After (New Pattern)
```python
from llm_client import get_browser_use_client

llm = get_browser_use_client()
```

## Architecture

```
llm_client.py (Root)
├── LLMClientFactory (Main Class)
│   ├── get_browser_use_client()
│   ├── get_playwright_mcp_client()
│   ├── get_automation_engine_client()
│   └── get_self_healing_client()
│
└── Convenience Functions
    ├── get_browser_use_client()
    ├── get_playwright_mcp_client()
    ├── get_automation_engine_client()
    └── get_self_healing_client()
```

## Future Enhancements

- Add support for other LLM providers (Anthropic, Google, etc.)
- Implement token usage tracking
- Add request retry logic
- Support for streaming responses
- Configuration file support
