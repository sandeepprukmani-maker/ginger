import { chromium, Browser, Page, Locator } from "playwright";
import type { AutomationStep } from "./llm-planner";

export class PlaywrightExecutor {
  private browser: Browser | null = null;
  private page: Page | null = null;

  async initialize() {
    this.browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
    });
    this.page = await context.newPage();
  }

  async cleanup() {
    if (this.page) await this.page.close();
    if (this.browser) await this.browser.close();
    this.page = null;
    this.browser = null;
  }

  async executeStep(step: AutomationStep): Promise<{
    success: boolean;
    result?: any;
    error?: string;
    selector?: string;
  }> {
    if (!this.page) {
      throw new Error("Executor not initialized");
    }

    try {
      switch (step.stepType) {
        case "navigate":
          return await this.handleNavigate(step);
        case "click":
          return await this.handleClick(step);
        case "type":
          return await this.handleType(step);
        case "extract":
          return await this.handleExtract(step);
        case "assert":
          return await this.handleAssert(step);
        case "wait":
          return await this.handleWait(step);
        case "screenshot":
          return await this.handleScreenshot(step);
        default:
          return {
            success: false,
            error: `Unknown step type: ${step.stepType}`,
          };
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message,
      };
    }
  }

  private async handleNavigate(step: AutomationStep) {
    if (!this.page || !step.target) {
      return { success: false, error: "Invalid navigate step" };
    }

    let url = step.target;
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = "https://" + url;
    }

    await this.page.goto(url, {
      waitUntil: (step.waitCondition as any) || "networkidle",
      timeout: step.timeout || 30000,
    });

    return {
      success: true,
      result: { url: this.page.url() },
      selector: url,
    };
  }

  private async handleClick(step: AutomationStep) {
    if (!this.page || !step.target) {
      return { success: false, error: "Invalid click step" };
    }

    const locator = await this.findElement(step.target);
    const selectorUsed = await this.getLocatorDescription(locator);

    await locator.click({ timeout: step.timeout || 10000 });

    return {
      success: true,
      selector: selectorUsed,
    };
  }

  private async handleType(step: AutomationStep) {
    if (!this.page || !step.target || !step.value) {
      return { success: false, error: "Invalid type step" };
    }

    const locator = await this.findElement(step.target);
    const selectorUsed = await this.getLocatorDescription(locator);

    await locator.fill(step.value, { timeout: step.timeout || 10000 });

    return {
      success: true,
      result: { value: step.value },
      selector: selectorUsed,
    };
  }

  private async handleExtract(step: AutomationStep) {
    if (!this.page || !step.target) {
      return { success: false, error: "Invalid extract step" };
    }

    const data = await this.extractData(step.target, step.description);

    return {
      success: true,
      result: data,
      selector: step.target,
    };
  }

  private async handleAssert(step: AutomationStep) {
    if (!this.page || !step.target) {
      return { success: false, error: "Invalid assert step" };
    }

    const result = await this.performAssertion(step);

    return {
      success: result.passed,
      result,
      selector: result.selector,
    };
  }

  private async handleWait(step: AutomationStep) {
    if (!this.page) {
      return { success: false, error: "Invalid wait step" };
    }

    const timeout = step.timeout || 5000;

    if (step.waitCondition) {
      await this.page.waitForLoadState(step.waitCondition as any, { timeout });
    } else {
      await this.page.waitForTimeout(timeout);
    }

    return { success: true };
  }

  private async handleScreenshot(step: AutomationStep) {
    if (!this.page) {
      return { success: false, error: "Invalid screenshot step" };
    }

    const screenshot = await this.page.screenshot({ fullPage: true });

    return {
      success: true,
      result: { screenshot: screenshot.toString("base64") },
    };
  }

  private async findElement(description: string): Promise<Locator> {
    if (!this.page) {
      throw new Error("Page not initialized");
    }

    const lowerDesc = description.toLowerCase();

    if (lowerDesc.includes("button")) {
      const buttons = await this.page.getByRole("button").all();
      for (const btn of buttons) {
        const text = await btn.textContent();
        if (text && text.toLowerCase().includes(lowerDesc.replace("button", "").trim())) {
          return btn;
        }
      }
      return this.page.getByRole("button").first();
    }

    if (lowerDesc.includes("input") || lowerDesc.includes("field")) {
      const textboxes = await this.page.getByRole("textbox").all();
      const inputs = await this.page.locator("input").all();
      
      for (const input of [...textboxes, ...inputs]) {
        const placeholder = await input.getAttribute("placeholder");
        const label = await this.getLabelForInput(input);
        
        if (
          (placeholder && placeholder.toLowerCase().includes(lowerDesc)) ||
          (label && label.toLowerCase().includes(lowerDesc))
        ) {
          return input;
        }
      }
      
      return this.page.getByRole("textbox").first();
    }

    if (lowerDesc.includes("link")) {
      const links = await this.page.getByRole("link").all();
      for (const link of links) {
        const text = await link.textContent();
        if (text && text.toLowerCase().includes(lowerDesc.replace("link", "").trim())) {
          return link;
        }
      }
      return this.page.getByRole("link").first();
    }

    try {
      return this.page.getByText(description, { exact: false }).first();
    } catch {
      return this.page.locator(`text=${description}`).first();
    }
  }

  private async getLabelForInput(input: Locator): Promise<string | null> {
    try {
      const id = await input.getAttribute("id");
      if (id && this.page) {
        const label = this.page.locator(`label[for="${id}"]`);
        const labelText = await label.textContent();
        return labelText;
      }
    } catch {
      // Ignore
    }
    return null;
  }

  private async getLocatorDescription(locator: Locator): Promise<string> {
    try {
      const element = await locator.first().elementHandle();
      if (!element) return "unknown";

      const tagName = await element.evaluate((el) => el.tagName.toLowerCase());
      const text = await element.textContent();
      const role = await element.getAttribute("role");
      const ariaLabel = await element.getAttribute("aria-label");

      if (ariaLabel) return `${tagName}[aria-label="${ariaLabel}"]`;
      if (role) return `${tagName}[role="${role}"]`;
      if (text) return `${tagName} with text "${text.substring(0, 30)}"`;
      
      return tagName;
    } catch {
      return "element";
    }
  }

  private async extractData(target: string, description: string): Promise<any> {
    if (!this.page) return null;

    try {
      if (target.includes("result") || target.includes("list")) {
        const items = await this.page.locator("li, .result, [class*='result']").all();
        const extracted = [];

        for (let i = 0; i < Math.min(items.length, 20); i++) {
          const text = await items[i].textContent();
          if (text && text.trim()) {
            extracted.push(text.trim());
          }
        }

        return extracted.length > 0 ? extracted : null;
      }

      const textContent = await this.page.textContent("body");
      return { extractedText: textContent?.substring(0, 1000) };
    } catch (error: any) {
      return { error: error.message };
    }
  }

  private async performAssertion(step: AutomationStep): Promise<{
    passed: boolean;
    expected?: string;
    actual?: string;
    message?: string;
    selector?: string;
  }> {
    if (!this.page || !step.target) {
      return {
        passed: false,
        message: "Invalid assertion step",
      };
    }

    try {
      const locator = await this.findElement(step.target);
      const selectorUsed = await this.getLocatorDescription(locator);

      switch (step.assertionType) {
        case "exists": {
          const count = await locator.count();
          return {
            passed: count > 0,
            expected: "element exists",
            actual: count > 0 ? "element found" : "element not found",
            selector: selectorUsed,
          };
        }

        case "text_match": {
          const text = await locator.textContent();
          const matches = text?.includes(step.expectedValue || "") || false;
          return {
            passed: matches,
            expected: step.expectedValue,
            actual: text || "",
            selector: selectorUsed,
          };
        }

        case "count": {
          const count = await locator.count();
          const expected = step.expectedValue || "1";
          let passed = false;

          if (expected.startsWith(">=")) {
            passed = count >= parseInt(expected.substring(2));
          } else if (expected.startsWith("<=")) {
            passed = count <= parseInt(expected.substring(2));
          } else if (expected.startsWith(">")) {
            passed = count > parseInt(expected.substring(1));
          } else if (expected.startsWith("<")) {
            passed = count < parseInt(expected.substring(1));
          } else {
            passed = count === parseInt(expected);
          }

          return {
            passed,
            expected,
            actual: count.toString(),
            selector: selectorUsed,
          };
        }

        case "visible": {
          const visible = await locator.isVisible();
          return {
            passed: visible,
            expected: "visible",
            actual: visible ? "visible" : "not visible",
            selector: selectorUsed,
          };
        }

        case "enabled": {
          const enabled = await locator.isEnabled();
          return {
            passed: enabled,
            expected: "enabled",
            actual: enabled ? "enabled" : "disabled",
            selector: selectorUsed,
          };
        }

        default:
          return {
            passed: false,
            message: `Unknown assertion type: ${step.assertionType}`,
          };
      }
    } catch (error: any) {
      return {
        passed: false,
        message: error.message,
      };
    }
  }

  async getPageContext(): Promise<string> {
    if (!this.page) return "";

    try {
      const snapshot = await this.page.accessibility.snapshot();
      return JSON.stringify(snapshot, null, 2).substring(0, 2000);
    } catch {
      return "";
    }
  }
}
