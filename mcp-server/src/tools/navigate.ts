import { SessionManager } from '../session/sessionManager.js';
import { NavigateParams, NavigateParamsSchema } from '../types/schemas.js';

export async function navigate(
  sessionManager: SessionManager,
  args: unknown
): Promise<{ status: string; url: string; title: string }> {
  const params: NavigateParams = NavigateParamsSchema.parse(args);
  const page = sessionManager.getPage();

  await page.goto(params.url, { waitUntil: 'networkidle' });
  const title = await page.title();

  return {
    status: 'success',
    url: params.url,
    title,
  };
}
