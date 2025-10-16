# Playwright MCP Server

A Model Context Protocol (MCP) server that provides Playwright browser automation capabilities to AI assistants and agents.

## Features

- **Browser Automation**: Navigate, click, fill forms, extract text, take screenshots
- **AI-Powered Planning**: Uses OpenAI to intelligently plan automation sequences from natural language
- **MCP Protocol**: Full compliance with Model Context Protocol for integration with Claude Desktop and other MCP clients
- **Fallback Planning**: Works without OpenAI API key using heuristic-based automation

## Available Tools

### Core Automation Tools
- `playwright_health_check` - Check browser session status
- `playwright_navigate` - Navigate to a URL
- `playwright_click` - Click an element (supports CSS, text, and role selectors)
- `playwright_fill` - Fill text into input fields
- `playwright_get_text` - Get text from a single element
- `playwright_get_all_text` - Get text from multiple elements
- `playwright_screenshot` - Take page screenshots

### AI Planning Tool
- `playwright_plan_and_execute` - Natural language automation (requires OPENAI_API_KEY)

## Installation

```bash
cd mcp-server
npm install
npm run build
```

## Usage

### With Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "node",
      "args": ["/path/to/mcp-server/build/index.js"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key-here"
      }
    }
  }
}
```

### Standalone

```bash
OPENAI_API_KEY=your-key npm start
```

### Programmatic Usage

```typescript
import { spawn } from 'child_process';

const server = spawn('node', ['build/index.js'], {
  stdio: ['pipe', 'pipe', 'inherit']
});

// Send JSON-RPC requests to server.stdin
// Read JSON-RPC responses from server.stdout
```

## Environment Variables

- `OPENAI_API_KEY` (optional) - Enables AI-powered automation planning

## Architecture

- **Session Manager**: Manages Playwright browser lifecycle
- **Tools**: Individual automation capabilities exposed as MCP tools
- **Planner**: AI-powered automation sequence generation
- **Transport**: stdio-based JSON-RPC communication

## Development

```bash
# Build
npm run build

# Run
npm start

# Development mode (rebuild + run)
npm run dev
```

## License

MIT
