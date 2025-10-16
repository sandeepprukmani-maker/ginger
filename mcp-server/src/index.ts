#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { SessionManager } from './session/sessionManager.js';
import { registerTools } from './tools/index.js';

const server = new Server(
  {
    name: 'playwright-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const sessionManager = new SessionManager();
let tools: Tool[] = [];

server.setRequestHandler(ListToolsRequestSchema, async () => {
  if (tools.length === 0) {
    tools = registerTools();
  }
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    await sessionManager.ensureSession();

    switch (name) {
      case 'playwright_health_check':
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                status: 'healthy',
                browser: 'chromium',
                sessionActive: sessionManager.isActive(),
              }),
            },
          ],
        };

      case 'playwright_navigate': {
        const { navigate } = await import('./tools/navigate.js');
        const result = await navigate(sessionManager, args);
        return {
          content: [{ type: 'text', text: JSON.stringify(result) }],
        };
      }

      case 'playwright_click': {
        const { click } = await import('./tools/click.js');
        const result = await click(sessionManager, args);
        return {
          content: [{ type: 'text', text: JSON.stringify(result) }],
        };
      }

      case 'playwright_fill': {
        const { fill } = await import('./tools/fill.js');
        const result = await fill(sessionManager, args);
        return {
          content: [{ type: 'text', text: JSON.stringify(result) }],
        };
      }

      case 'playwright_get_text': {
        const { getText } = await import('./tools/getText.js');
        const result = await getText(sessionManager, args);
        return {
          content: [{ type: 'text', text: JSON.stringify(result) }],
        };
      }

      case 'playwright_get_all_text': {
        const { getAllText } = await import('./tools/getAllText.js');
        const result = await getAllText(sessionManager, args);
        return {
          content: [{ type: 'text', text: JSON.stringify(result) }],
        };
      }

      case 'playwright_screenshot': {
        const { screenshot } = await import('./tools/screenshot.js');
        const result = await screenshot(sessionManager, args);
        return {
          content: [{ type: 'text', text: JSON.stringify(result) }],
        };
      }

      case 'playwright_plan_and_execute': {
        const { planAndExecute } = await import('./planning/openaiPlanner.js');
        const result = await planAndExecute(sessionManager, args);
        return {
          content: [{ type: 'text', text: JSON.stringify(result) }],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            error: errorMessage,
            tool: name,
          }),
        },
      ],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('Playwright MCP Server running on stdio');
  
  process.on('SIGINT', async () => {
    await sessionManager.cleanup();
    process.exit(0);
  });
}

main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});
