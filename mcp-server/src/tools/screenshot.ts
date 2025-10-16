import { SessionManager } from '../session/sessionManager.js';
import { ScreenshotParams, ScreenshotParamsSchema } from '../types/schemas.js';

export async function screenshot(
  sessionManager: SessionManager,
  args: unknown
): Promise<{ status: string; path: string; base64?: string }> {
  const params: ScreenshotParams = ScreenshotParamsSchema.parse(args);
  const page = sessionManager.getPage();

  const timestamp = Date.now();
  const path = `screenshot_${timestamp}.png`;

  const buffer = await page.screenshot({
    path,
    fullPage: params.fullPage || false,
  });

  return {
    status: 'success',
    path,
    base64: buffer.toString('base64'),
  };
}
