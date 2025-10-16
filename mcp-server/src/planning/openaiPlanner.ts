import OpenAI from 'openai';
import { SessionManager } from '../session/sessionManager.js';
import { PlanAutomationParams, PlanAutomationParamsSchema } from '../types/schemas.js';
import { navigate } from '../tools/navigate.js';
import { click } from '../tools/click.js';
import { fill } from '../tools/fill.js';
import { getText } from '../tools/getText.js';
import { getAllText } from '../tools/getAllText.js';
import { screenshot } from '../tools/screenshot.js';

interface AutomationAction {
  tool: string;
  parameters: Record<string, unknown>;
  description: string;
}

interface PlanResult {
  success: boolean;
  actions: AutomationAction[];
  results: Array<{
    action: string;
    tool: string;
    result: unknown;
    success: boolean;
  }>;
}

export async function planAndExecute(
  sessionManager: SessionManager,
  args: unknown
): Promise<PlanResult> {
  const params: PlanAutomationParams = PlanAutomationParamsSchema.parse(args);
  
  const openaiKey = process.env.OPENAI_API_KEY;
  let actions: AutomationAction[];

  if (openaiKey) {
    actions = await generateActionsWithOpenAI(params.url, params.prompt, openaiKey);
  } else {
    console.error('OpenAI API key not found, using fallback planning');
    actions = await fallbackPlanning(params.url, params.prompt);
  }

  const results = await executeActions(sessionManager, actions);

  return {
    success: results.some((r) => r.success),
    actions,
    results,
  };
}

async function generateActionsWithOpenAI(
  url: string,
  prompt: string,
  apiKey: string
): Promise<AutomationAction[]> {
  const openai = new OpenAI({ apiKey });

  const systemPrompt = `You are a web automation expert using Playwright.
Analyze the user request and generate a sequence of Playwright actions.

Available actions:
- navigate: Go to a URL
- click: Click an element (use CSS selectors, text selectors like 'text=Button', or role selectors)
- fill: Fill an input field
- screenshot: Take a screenshot
- get_text: Get text from an element
- get_all_text: Get text from multiple elements

Return JSON array format:
[
  {
    "tool": "navigate|click|fill|screenshot|get_text|get_all_text",
    "parameters": {
      "url": "for navigate",
      "selector": "CSS selector or text=Button or [role=button]",
      "text": "for fill actions"
    },
    "description": "what this step accomplishes"
  }
]

For selectors, prefer:
- Text selectors: "text=Login" or "text=Submit"
- Role selectors: "[role='button']", "[role='link']"
- CSS selectors: "button.submit", "input[name='email']"
- Common patterns: "h1", "a", "button", "input[type='text']"

IMPORTANT: Always start with navigate action to the URL.`;

  const userContent = `URL: ${url}
User Request: ${prompt}

Generate the sequence of Playwright actions needed.`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userContent },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.1,
      max_tokens: 2000,
    });

    const content = response.choices[0]?.message?.content;
    if (!content) {
      throw new Error('No response from OpenAI');
    }

    const data = JSON.parse(content);
    
    if (Array.isArray(data)) {
      return data;
    } else if (data.actions && Array.isArray(data.actions)) {
      return data.actions;
    }
    
    throw new Error('Invalid response format from OpenAI');
  } catch (error) {
    console.error('OpenAI planning failed:', error);
    return fallbackPlanning(url, prompt);
  }
}

async function fallbackPlanning(url: string, prompt: string): Promise<AutomationAction[]> {
  const promptLower = prompt.toLowerCase();
  const actions: AutomationAction[] = [];

  actions.push({
    tool: 'navigate',
    parameters: { url },
    description: `Navigate to ${url}`,
  });

  if (promptLower.includes('click')) {
    if (promptLower.includes('button')) {
      actions.push({
        tool: 'click',
        parameters: { selector: 'button' },
        description: 'Click the first button',
      });
    } else {
      actions.push({
        tool: 'click',
        parameters: { selector: 'a' },
        description: 'Click the first link',
      });
    }
  }

  if (['type', 'fill', 'enter'].some((word) => promptLower.includes(word))) {
    actions.push({
      tool: 'fill',
      parameters: { selector: 'input', text: 'example text' },
      description: 'Fill text input',
    });
  }

  if (promptLower.includes('screenshot')) {
    actions.push({
      tool: 'screenshot',
      parameters: {},
      description: 'Take screenshot',
    });
  }

  if (['get', 'scrape', 'extract'].some((word) => promptLower.includes(word))) {
    if (promptLower.includes('title')) {
      actions.push({
        tool: 'get_text',
        parameters: { selector: 'h1' },
        description: 'Get page title',
      });
    } else {
      actions.push({
        tool: 'get_all_text',
        parameters: { selector: 'a' },
        description: 'Get all link texts',
      });
    }
  }

  return actions;
}

async function executeActions(
  sessionManager: SessionManager,
  actions: AutomationAction[]
): Promise<Array<{ action: string; tool: string; result: unknown; success: boolean }>> {
  const results = [];

  for (const action of actions) {
    try {
      console.error(`Executing: ${action.description}`);
      
      let result: unknown;
      
      switch (action.tool) {
        case 'navigate':
          result = await navigate(sessionManager, action.parameters);
          break;
        case 'click':
          result = await click(sessionManager, action.parameters);
          break;
        case 'fill':
          result = await fill(sessionManager, action.parameters);
          break;
        case 'get_text':
          result = await getText(sessionManager, action.parameters);
          break;
        case 'get_all_text':
          result = await getAllText(sessionManager, action.parameters);
          break;
        case 'screenshot':
          result = await screenshot(sessionManager, action.parameters);
          break;
        default:
          throw new Error(`Unknown tool: ${action.tool}`);
      }

      results.push({
        action: action.description,
        tool: action.tool,
        result,
        success: true,
      });

      await new Promise((resolve) => setTimeout(resolve, 500));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      results.push({
        action: action.description,
        tool: action.tool,
        result: { error: errorMessage },
        success: false,
      });
    }
  }

  return results;
}
