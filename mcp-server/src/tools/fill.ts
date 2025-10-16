import { SessionManager } from '../session/sessionManager.js';
import { FillParams, FillParamsSchema } from '../types/schemas.js';

export async function fill(
  sessionManager: SessionManager,
  args: unknown
): Promise<{ status: string; selector: string; text: string }> {
  const params: FillParams = FillParamsSchema.parse(args);
  const page = sessionManager.getPage();

  await page.fill(params.selector, params.text);

  return {
    status: 'success',
    selector: params.selector,
    text: params.text,
  };
}
