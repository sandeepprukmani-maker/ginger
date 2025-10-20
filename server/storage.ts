import {
  type AutomationRun,
  type InsertAutomationRun,
  type ExecutionStep,
  type InsertExecutionStep,
  type ScrapedData,
  type InsertScrapedData,
  type AssertionResult,
  type InsertAssertionResult,
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  // Automation Runs
  createRun(run: InsertAutomationRun): Promise<AutomationRun>;
  getRun(id: string): Promise<AutomationRun | undefined>;
  getAllRuns(): Promise<AutomationRun[]>;
  updateRunStatus(id: string, status: string, error?: string): Promise<void>;
  completeRun(id: string, error?: string): Promise<void>;

  // Execution Steps
  createStep(step: InsertExecutionStep): Promise<ExecutionStep>;
  getStepsByRunId(runId: string): Promise<ExecutionStep[]>;
  updateStepStatus(id: string, status: string, result?: any, error?: string | null, selector?: string): Promise<void>;

  // Scraped Data
  createScrapedData(data: InsertScrapedData): Promise<ScrapedData>;
  getScrapedDataByRunId(runId: string): Promise<ScrapedData[]>;

  // Assertion Results
  createAssertionResult(result: InsertAssertionResult): Promise<AssertionResult>;
  getAssertionResultsByRunId(runId: string): Promise<AssertionResult[]>;
}

export class MemStorage implements IStorage {
  private runs: Map<string, AutomationRun>;
  private steps: Map<string, ExecutionStep>;
  private scrapedData: Map<string, ScrapedData>;
  private assertionResults: Map<string, AssertionResult>;

  constructor() {
    this.runs = new Map();
    this.steps = new Map();
    this.scrapedData = new Map();
    this.assertionResults = new Map();
  }

  // Automation Runs
  async createRun(insertRun: InsertAutomationRun): Promise<AutomationRun> {
    const id = randomUUID();
    const run: AutomationRun = {
      id,
      command: insertRun.command,
      status: insertRun.status || "pending",
      createdAt: new Date(),
      completedAt: insertRun.completedAt || null,
      error: insertRun.error || null,
    };
    this.runs.set(id, run);
    return run;
  }

  async getRun(id: string): Promise<AutomationRun | undefined> {
    return this.runs.get(id);
  }

  async getAllRuns(): Promise<AutomationRun[]> {
    return Array.from(this.runs.values()).sort(
      (a, b) => b.createdAt.getTime() - a.createdAt.getTime()
    );
  }

  async updateRunStatus(id: string, status: string, error?: string): Promise<void> {
    const run = this.runs.get(id);
    if (run) {
      run.status = status;
      if (error) run.error = error;
      this.runs.set(id, run);
    }
  }

  async completeRun(id: string, error?: string): Promise<void> {
    const run = this.runs.get(id);
    if (run) {
      run.status = error ? "failed" : "completed";
      run.completedAt = new Date();
      if (error) run.error = error;
      this.runs.set(id, run);
    }
  }

  // Execution Steps
  async createStep(insertStep: InsertExecutionStep): Promise<ExecutionStep> {
    const id = randomUUID();
    const step: ExecutionStep = {
      id,
      runId: insertStep.runId,
      stepNumber: insertStep.stepNumber,
      stepType: insertStep.stepType,
      description: insertStep.description,
      selector: insertStep.selector || null,
      status: insertStep.status || "pending",
      result: insertStep.result || null,
      error: insertStep.error || null,
      screenshotPath: insertStep.screenshotPath || null,
      executedAt: insertStep.executedAt || null,
    };
    this.steps.set(id, step);
    return step;
  }

  async getStepsByRunId(runId: string): Promise<ExecutionStep[]> {
    return Array.from(this.steps.values())
      .filter((step) => step.runId === runId)
      .sort((a, b) => a.stepNumber - b.stepNumber);
  }

  async updateStepStatus(id: string, status: string, result?: any, error?: string | null, selector?: string): Promise<void> {
    const step = this.steps.get(id);
    if (step) {
      step.status = status;
      step.executedAt = new Date();
      if (result !== undefined) step.result = result;
      // Clear error if explicitly set to null (for recovery scenarios)
      if (error === null) {
        step.error = null;
      } else if (error) {
        step.error = error;
      }
      if (selector) step.selector = selector;
      this.steps.set(id, step);
    }
  }

  // Scraped Data
  async createScrapedData(insertData: InsertScrapedData): Promise<ScrapedData> {
    const id = randomUUID();
    const data: ScrapedData = {
      id,
      runId: insertData.runId,
      stepId: insertData.stepId || null,
      data: insertData.data,
      extractedAt: new Date(),
    };
    this.scrapedData.set(id, data);
    return data;
  }

  async getScrapedDataByRunId(runId: string): Promise<ScrapedData[]> {
    return Array.from(this.scrapedData.values())
      .filter((data) => data.runId === runId)
      .sort((a, b) => a.extractedAt.getTime() - b.extractedAt.getTime());
  }

  // Assertion Results
  async createAssertionResult(insertResult: InsertAssertionResult): Promise<AssertionResult> {
    const id = randomUUID();
    const result: AssertionResult = {
      id,
      runId: insertResult.runId,
      stepId: insertResult.stepId || null,
      assertionType: insertResult.assertionType,
      expected: insertResult.expected || null,
      actual: insertResult.actual || null,
      passed: insertResult.passed,
      message: insertResult.message || null,
      checkedAt: new Date(),
    };
    this.assertionResults.set(id, result);
    return result;
  }

  async getAssertionResultsByRunId(runId: string): Promise<AssertionResult[]> {
    return Array.from(this.assertionResults.values())
      .filter((result) => result.runId === runId)
      .sort((a, b) => a.checkedAt.getTime() - b.checkedAt.getTime());
  }
}

export const storage = new MemStorage();
