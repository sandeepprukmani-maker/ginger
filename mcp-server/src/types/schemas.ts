import { z } from 'zod';

export const NavigateParamsSchema = z.object({
  url: z.string().url().describe('URL to navigate to')
});

export const ClickParamsSchema = z.object({
  selector: z.string().describe('CSS selector, text selector (text=Login), or role selector')
});

export const FillParamsSchema = z.object({
  selector: z.string().describe('CSS selector for the input field'),
  text: z.string().describe('Text to fill into the field')
});

export const GetTextParamsSchema = z.object({
  selector: z.string().describe('CSS selector for the element')
});

export const GetAllTextParamsSchema = z.object({
  selector: z.string().describe('CSS selector for the elements')
});

export const ScreenshotParamsSchema = z.object({
  fullPage: z.boolean().optional().describe('Capture full page screenshot')
});

export const PlanAutomationParamsSchema = z.object({
  url: z.string().url().describe('Target URL for automation'),
  prompt: z.string().describe('Natural language description of automation task')
});

export type NavigateParams = z.infer<typeof NavigateParamsSchema>;
export type ClickParams = z.infer<typeof ClickParamsSchema>;
export type FillParams = z.infer<typeof FillParamsSchema>;
export type GetTextParams = z.infer<typeof GetTextParamsSchema>;
export type GetAllTextParams = z.infer<typeof GetAllTextParamsSchema>;
export type ScreenshotParams = z.infer<typeof ScreenshotParamsSchema>;
export type PlanAutomationParams = z.infer<typeof PlanAutomationParamsSchema>;
