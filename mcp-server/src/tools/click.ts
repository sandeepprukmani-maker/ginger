import { SessionManager } from '../session/sessionManager.js';
import { ClickParams, ClickParamsSchema } from '../types/schemas.js';

export async function click(
  sessionManager: SessionManager,
  args: unknown
): Promise<{ status: string; selector: string }> {
  const params: ClickParams = ClickParamsSchema.parse(args);
  const page = sessionManager.getPage();

  await page.click(params.selector);
  await page.waitForTimeout(500);

  return {
    status: 'success',
    selector: params.selector,
  };
}
