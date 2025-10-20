import { storage } from "../storage";
import { generateExecutionPlan } from "./llm-planner";
import { PlaywrightExecutor } from "./playwright-executor";
import type { AutomationRun } from "@shared/schema";
import type { WebSocket } from "ws";

export class AutomationOrchestrator {
  private activeExecutions: Map<string, boolean> = new Map();

  async executeAutomation(runId: string, wsClients: Set<WebSocket>): Promise<void> {
    if (this.activeExecutions.get(runId)) {
      throw new Error("Automation already running");
    }

    this.activeExecutions.set(runId, true);

    try {
      const run = await storage.getRun(runId);
      if (!run) {
        throw new Error("Run not found");
      }

      this.broadcast(wsClients, {
        type: "run_status",
        runId,
        status: "running",
      });

      await storage.updateRunStatus(runId, "running");

      this.broadcast(wsClients, {
        type: "log",
        runId,
        message: "Generating execution plan from natural language...",
        level: "info",
      });

      const plan = await generateExecutionPlan(run.command);

      this.broadcast(wsClients, {
        type: "log",
        runId,
        message: `Plan generated with ${plan.steps.length} steps`,
        level: "info",
      });

      const executor = new PlaywrightExecutor();
      await executor.initialize();

      try {
        for (let i = 0; i < plan.steps.length; i++) {
          const step = plan.steps[i];
          
          const dbStep = await storage.createStep({
            runId,
            stepNumber: i + 1,
            stepType: step.stepType,
            description: step.description,
            status: "running",
          });

          this.broadcast(wsClients, {
            type: "step_update",
            runId,
            step: {
              id: dbStep.id,
              stepNumber: dbStep.stepNumber,
              stepType: dbStep.stepType,
              description: dbStep.description,
              status: "running",
            },
          });

          this.broadcast(wsClients, {
            type: "log",
            runId,
            message: `Executing step ${i + 1}: ${step.description}`,
            level: "info",
          });

          let result = await executor.executeStep(step);

          if (!result.success) {
            await storage.updateStepStatus(dbStep.id, "failed", result.result, result.error, result.selector);
            
            this.broadcast(wsClients, {
              type: "step_update",
              runId,
              step: {
                id: dbStep.id,
                stepNumber: dbStep.stepNumber,
                stepType: dbStep.stepType,
                description: dbStep.description,
                status: "failed",
                error: result.error,
              },
            });

            this.broadcast(wsClients, {
              type: "log",
              runId,
              message: `Step ${i + 1} failed: ${result.error}. Attempting recovery...`,
              level: "warn",
            });

            // Retry logic for transient failures
            if (step.stepType !== "assert" && i > 0) {
              this.broadcast(wsClients, {
                type: "log",
                runId,
                message: `Retrying step ${i + 1} with fallback strategy...`,
                level: "info",
              });

              await new Promise((resolve) => setTimeout(resolve, 2000));
              const retryResult = await executor.executeStep(step);

              if (!retryResult.success) {
                this.broadcast(wsClients, {
                  type: "log",
                  runId,
                  message: `Retry failed. Aborting run: ${retryResult.error}`,
                  level: "error",
                });
                throw new Error(`Step ${i + 1} failed after retry: ${retryResult.error}`);
              }

              // Retry succeeded - replace result and clear error
              result = retryResult;
              
              await storage.updateStepStatus(
                dbStep.id,
                "completed",
                retryResult.result,
                null,
                retryResult.selector
              );

              this.broadcast(wsClients, {
                type: "log",
                runId,
                message: `Step ${i + 1} succeeded on retry`,
                level: "info",
              });
            } else {
              throw new Error(`Step ${i + 1} failed: ${result.error}`);
            }
          } else {
            await storage.updateStepStatus(
              dbStep.id,
              "completed",
              result.result,
              undefined,
              result.selector
            );
          }

          // Broadcast success update (either first attempt or after retry)
          this.broadcast(wsClients, {
            type: "step_update",
            runId,
            step: {
              id: dbStep.id,
              stepNumber: dbStep.stepNumber,
              stepType: dbStep.stepType,
              description: dbStep.description,
              status: "completed",
              result: result.result,
            },
          });

          // Handle data extraction and assertions (works for both first attempt and retry)
          if (step.stepType === "extract" && result.result) {
            const scrapedData = await storage.createScrapedData({
              runId,
              stepId: dbStep.id,
              data: result.result,
            });

            this.broadcast(wsClients, {
              type: "scraped_data",
              runId,
              data: scrapedData,
            });

            this.broadcast(wsClients, {
              type: "log",
              runId,
              message: `Data extracted successfully`,
              level: "info",
            });
          }

          if (step.stepType === "assert" && result.result) {
            const assertion = await storage.createAssertionResult({
              runId,
              stepId: dbStep.id,
              assertionType: step.assertionType || "exists",
              expected: result.result.expected || null,
              actual: result.result.actual || null,
              passed: result.result.passed ? "true" : "false",
              message: result.result.message || null,
            });

            this.broadcast(wsClients, {
              type: "assertion_result",
              runId,
              assertion,
            });

            this.broadcast(wsClients, {
              type: "log",
              runId,
              message: result.result.passed
                ? `Assertion passed: ${step.description}`
                : `Assertion failed: ${step.description}`,
              level: result.result.passed ? "info" : "warn",
            });
          }

          await new Promise((resolve) => setTimeout(resolve, 500));
        }

        await storage.completeRun(runId);

        this.broadcast(wsClients, {
          type: "run_status",
          runId,
          status: "completed",
        });

        this.broadcast(wsClients, {
          type: "log",
          runId,
          message: "Automation completed successfully",
          level: "info",
        });
      } finally {
        await executor.cleanup();
      }
    } catch (error: any) {
      await storage.completeRun(runId, error.message);

      this.broadcast(wsClients, {
        type: "run_status",
        runId,
        status: "failed",
        error: error.message,
      });

      this.broadcast(wsClients, {
        type: "log",
        runId,
        message: `Automation failed: ${error.message}`,
        level: "error",
      });
    } finally {
      this.activeExecutions.delete(runId);
    }
  }

  private broadcast(clients: Set<WebSocket>, message: any) {
    const payload = JSON.stringify(message);
    clients.forEach((client) => {
      if (client.readyState === 1) { // WebSocket.OPEN
        client.send(payload);
      }
    });
  }
}

export const orchestrator = new AutomationOrchestrator();
