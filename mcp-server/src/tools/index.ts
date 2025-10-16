import { Tool } from '@modelcontextprotocol/sdk/types.js';

export function registerTools(): Tool[] {
  return [
    {
      name: 'playwright_health_check',
      description: 'Check if the Playwright browser session is healthy and active',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    {
      name: 'playwright_navigate',
      description: 'Navigate to a URL in the browser',
      inputSchema: {
        type: 'object',
        properties: {
          url: {
            type: 'string',
            description: 'URL to navigate to',
          },
        },
        required: ['url'],
      },
    },
    {
      name: 'playwright_click',
      description: 'Click an element using a selector (CSS, text, or role)',
      inputSchema: {
        type: 'object',
        properties: {
          selector: {
            type: 'string',
            description: 'CSS selector, text selector (text=Login), or role selector',
          },
        },
        required: ['selector'],
      },
    },
    {
      name: 'playwright_fill',
      description: 'Fill text into an input field',
      inputSchema: {
        type: 'object',
        properties: {
          selector: {
            type: 'string',
            description: 'CSS selector for the input field',
          },
          text: {
            type: 'string',
            description: 'Text to fill into the field',
          },
        },
        required: ['selector', 'text'],
      },
    },
    {
      name: 'playwright_get_text',
      description: 'Get text content from a single element',
      inputSchema: {
        type: 'object',
        properties: {
          selector: {
            type: 'string',
            description: 'CSS selector for the element',
          },
        },
        required: ['selector'],
      },
    },
    {
      name: 'playwright_get_all_text',
      description: 'Get text content from all matching elements',
      inputSchema: {
        type: 'object',
        properties: {
          selector: {
            type: 'string',
            description: 'CSS selector for the elements',
          },
        },
        required: ['selector'],
      },
    },
    {
      name: 'playwright_screenshot',
      description: 'Take a screenshot of the current page',
      inputSchema: {
        type: 'object',
        properties: {
          fullPage: {
            type: 'boolean',
            description: 'Capture full page screenshot',
          },
        },
      },
    },
    {
      name: 'playwright_plan_and_execute',
      description: 'Use AI to plan and execute a sequence of automation steps based on natural language prompt',
      inputSchema: {
        type: 'object',
        properties: {
          url: {
            type: 'string',
            description: 'Target URL for automation',
          },
          prompt: {
            type: 'string',
            description: 'Natural language description of automation task',
          },
        },
        required: ['url', 'prompt'],
      },
    },
  ];
}
