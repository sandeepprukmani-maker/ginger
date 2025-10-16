import { Browser, BrowserContext, Page, chromium } from 'playwright';

export class SessionManager {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;

  async ensureSession(): Promise<void> {
    if (!this.browser) {
      console.error('Starting Chromium browser...');
      this.browser = await chromium.launch({ headless: true });
      this.context = await this.browser.newContext();
      this.page = await this.context.newPage();
      console.error('Browser session started');
    }
  }

  getPage(): Page {
    if (!this.page) {
      throw new Error('Browser session not initialized. Call ensureSession() first.');
    }
    return this.page;
  }

  isActive(): boolean {
    return this.browser !== null && this.page !== null;
  }

  async cleanup(): Promise<void> {
    if (this.page) {
      await this.page.close();
      this.page = null;
    }
    if (this.context) {
      await this.context.close();
      this.context = null;
    }
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
    console.error('Browser session cleaned up');
  }
}
