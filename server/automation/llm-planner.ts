import OpenAI from "openai";

// the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export interface ExecutionPlan {
  steps: AutomationStep[];
  reasoning: string;
}

export interface AutomationStep {
  stepType: "navigate" | "click" | "type" | "extract" | "assert" | "wait" | "screenshot";
  description: string;
  target?: string; // semantic description of element (e.g., "search button", "email input")
  value?: string; // for type actions or assertion values
  assertionType?: "exists" | "text_match" | "count" | "visible" | "enabled";
  expectedValue?: string;
  waitCondition?: "networkidle" | "load" | "domcontentloaded";
  timeout?: number;
}

const SYSTEM_PROMPT = `You are an expert web automation planner. Your job is to convert natural language instructions into structured automation plans that can be executed by Playwright.

Key principles:
1. Use semantic descriptions for elements (e.g., "search button", "email input field") instead of selectors
2. Break complex tasks into simple, atomic steps
3. Include appropriate waits for page loads and network activity
4. Add assertions to validate expected outcomes
5. Use extract steps to capture data users want to scrape
6. Be defensive - add checks before critical actions

Available step types:
- navigate: Go to a URL
- click: Click an element (use semantic description)
- type: Enter text into an input (use semantic description + value)
- extract: Scrape data from page (describe what to extract)
- assert: Validate page state (exists, text_match, count, visible, enabled)
- wait: Wait for condition (networkidle, load, domcontentloaded)
- screenshot: Capture page state

Output your plan as JSON with this structure:
{
  "steps": [
    {
      "stepType": "navigate",
      "description": "Navigate to google.com",
      "target": "https://google.com",
      "waitCondition": "networkidle"
    },
    {
      "stepType": "type",
      "description": "Enter search query",
      "target": "search input",
      "value": "web automation"
    },
    {
      "stepType": "click",
      "description": "Click search button",
      "target": "search button"
    },
    {
      "stepType": "wait",
      "description": "Wait for results to load",
      "waitCondition": "networkidle"
    },
    {
      "stepType": "extract",
      "description": "Extract top 5 search result titles",
      "target": "search results"
    },
    {
      "stepType": "assert",
      "description": "Verify at least 5 results exist",
      "assertionType": "count",
      "target": "search results",
      "expectedValue": ">=5"
    }
  ],
  "reasoning": "This plan navigates to Google, performs a search, waits for results, extracts the titles, and validates the count."
}`;

export async function generateExecutionPlan(command: string): Promise<ExecutionPlan> {
  try {
    const response = await openai.chat.completions.create({
      model: "gpt-5",
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: `Create an automation plan for this command:\n\n${command}` },
      ],
      response_format: { type: "json_object" },
      max_completion_tokens: 4096,
    });

    const content = response.choices[0].message.content;
    if (!content) {
      throw new Error("No response from LLM");
    }

    const plan = JSON.parse(content) as ExecutionPlan;
    
    if (!plan.steps || !Array.isArray(plan.steps) || plan.steps.length === 0) {
      throw new Error("Invalid plan structure - no steps generated");
    }

    return plan;
  } catch (error: any) {
    throw new Error(`Failed to generate execution plan: ${error.message}`);
  }
}

export async function generateSmartSelector(
  pageContext: string,
  elementDescription: string
): Promise<string> {
  try {
    const prompt = `Given this page context and element description, suggest the best Playwright locator strategy.

Page context (accessibility tree snippet):
${pageContext}

Element to find: ${elementDescription}

Respond with JSON in this format:
{
  "locatorType": "role|text|label|placeholder|testid",
  "locatorValue": "the value to use",
  "reasoning": "why this is the best choice"
}

Prefer using role-based locators (getByRole) when possible for accessibility. Use getByText for visible text, getByLabel for form inputs with labels, getByPlaceholder for inputs with placeholders.`;

    const response = await openai.chat.completions.create({
      model: "gpt-5",
      messages: [{ role: "user", content: prompt }],
      response_format: { type: "json_object" },
      max_completion_tokens: 512,
    });

    const content = response.choices[0].message.content;
    if (!content) {
      throw new Error("No response from LLM");
    }

    const result = JSON.parse(content);
    return result.locatorValue || elementDescription;
  } catch (error: any) {
    return elementDescription;
  }
}
