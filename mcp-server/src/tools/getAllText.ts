import { SessionManager } from '../session/sessionManager.js';
import { GetAllTextParams, GetAllTextParamsSchema } from '../types/schemas.js';

export async function getAllText(
  sessionManager: SessionManager,
  args: unknown
): Promise<{ status: string; selector: string; texts: string[] }> {
  const params: GetAllTextParams = GetAllTextParamsSchema.parse(args);
  const page = sessionManager.getPage();

  const elements = await page.locator(params.selector).all();
  const texts: string[] = [];

  for (const element of elements) {
    const text = await element.innerText();
    texts.push(text);
  }

  return {
    status: 'success',
    selector: params.selector,
    texts,
  };
}
