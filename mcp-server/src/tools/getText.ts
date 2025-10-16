import { SessionManager } from '../session/sessionManager.js';
import { GetTextParams, GetTextParamsSchema } from '../types/schemas.js';

export async function getText(
  sessionManager: SessionManager,
  args: unknown
): Promise<{ status: string; selector: string; text: string }> {
  const params: GetTextParams = GetTextParamsSchema.parse(args);
  const page = sessionManager.getPage();

  const text = await page.innerText(params.selector);

  return {
    status: 'success',
    selector: params.selector,
    text,
  };
}
