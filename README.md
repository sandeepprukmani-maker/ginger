# Playwright MCP Automation Studio

A complete Model Context Protocol (MCP) server implementation that enables AI assistants to control and automate web browsers using Playwright. This project bridges AI models (particularly Claude and OpenAI) with browser automation through the MCP protocol.

## 🎯 What's Implemented

✅ **Full MCP Server** (TypeScript/Node.js)
- Complete MCP protocol implementation with stdio transport
- 8 browser automation tools exposed via JSON-RPC
- Works with Claude Desktop and any MCP-compatible client

✅ **Browser Automation Tools**
- `playwright_health_check` - Check browser session status
- `playwright_navigate` - Navigate to URLs
- `playwright_click` - Click elements (CSS, text, role selectors)
- `playwright_fill` - Fill forms
- `playwright_get_text` - Extract text from elements
- `playwright_get_all_text` - Extract text from multiple elements
- `playwright_screenshot` - Capture screenshots
- `playwright_plan_and_execute` - AI-powered automation from natural language

✅ **AI Planning Engine**
- OpenAI GPT-4 integration for intelligent automation
- Translates natural language to browser actions
- Fallback heuristic planning without API key

✅ **Web Interface**
- Flask-based UI for visual automation
- Python MCP client for server communication
- Real-time results and execution tracking

## 🚀 Quick Start

### 1. MCP Server (for Claude Desktop)

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "playwright": {
      "command": "node",
      "args": ["/path/to/this/project/mcp-server/build/index.js"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key-optional"
      }
    }
  }
}
```

Then restart Claude Desktop and you'll see the Playwright tools available!

### 2. Web Interface

The web UI is already running at the preview URL. Just add your OpenAI API key to the environment to enable AI-powered automation.

To run manually:
```bash
python web_ui_mcp.py
```

## 🔧 Usage Examples

### With Claude Desktop

Once configured, you can ask Claude:
- "Navigate to example.com and get the page title"
- "Go to hacker news and get the top 5 story titles"
- "Take a screenshot of google.com"

### Web Interface

1. Enter a URL (e.g., `https://example.com`)
2. Describe what you want to automate
3. Click "Generate & Execute Automation"
4. View the results and generated code

## 📁 Project Structure

```
.
├── mcp-server/              # TypeScript MCP Server
│   ├── src/
│   │   ├── index.ts        # Main server entry point
│   │   ├── session/        # Browser lifecycle management
│   │   ├── tools/          # Individual automation tools
│   │   ├── planning/       # AI planning engine
│   │   └── types/          # Type definitions
│   └── build/              # Compiled JavaScript
├── mcp_client.py           # Python MCP client
├── web_ui_mcp.py          # Flask web interface
├── templates/             # HTML templates
└── mcp-config-example.json # Claude Desktop config example
```

## 🔑 Environment Variables

- `OPENAI_API_KEY` (optional) - Enables AI-powered automation planning
  - Without it, the server uses fallback heuristic planning

## 🛠 Development

### Build MCP Server
```bash
cd mcp-server
npm install
npm run build
```

### Test MCP Server
```bash
cd mcp-server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node build/index.js
```

## 📚 Documentation

- [MCP Server README](mcp-server/README.md) - Detailed server documentation
- [replit.md](replit.md) - Architecture and technical details
- [mcp-config-example.json](mcp-config-example.json) - Claude Desktop setup

## 🎓 Architecture

The system consists of:

1. **MCP Server** (Node.js/TypeScript)
   - Implements Model Context Protocol
   - Manages Playwright browser sessions
   - Exposes automation tools via stdio/JSON-RPC

2. **Python MCP Client**
   - Communicates with MCP server via subprocess
   - Handles stdio transport and JSON-RPC messages

3. **Web UI** (Flask)
   - User-friendly interface
   - Integrates with MCP client
   - Shows automation results in real-time

## 🚢 Deployment

This project is ready to deploy! The web interface can be published to make it publicly accessible.

## 📝 License

MIT
