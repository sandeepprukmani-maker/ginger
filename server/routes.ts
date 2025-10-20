import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { orchestrator } from "./automation/orchestrator";
import { insertAutomationRunSchema } from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);

  // WebSocket server for real-time updates
  const wss = new WebSocketServer({ server: httpServer, path: "/ws" });
  const wsClients = new Set<WebSocket>();

  wss.on("connection", (ws) => {
    wsClients.add(ws);
    console.log("WebSocket client connected");

    ws.on("close", () => {
      wsClients.delete(ws);
      console.log("WebSocket client disconnected");
    });

    ws.on("error", (error) => {
      console.error("WebSocket error:", error);
      wsClients.delete(ws);
    });
  });

  // API Routes

  // Create new automation run
  app.post("/api/runs", async (req, res) => {
    try {
      const validated = insertAutomationRunSchema.parse(req.body);
      const run = await storage.createRun(validated);

      // Start execution asynchronously
      orchestrator.executeAutomation(run.id, wsClients).catch((error) => {
        console.error("Execution error:", error);
      });

      res.json(run);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  });

  // Get all runs
  app.get("/api/runs", async (req, res) => {
    try {
      const runs = await storage.getAllRuns();
      res.json(runs);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get specific run
  app.get("/api/runs/:id", async (req, res) => {
    try {
      const run = await storage.getRun(req.params.id);
      if (!run) {
        return res.status(404).json({ error: "Run not found" });
      }
      res.json(run);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get execution steps for a run
  app.get("/api/runs/:id/steps", async (req, res) => {
    try {
      const steps = await storage.getStepsByRunId(req.params.id);
      res.json(steps);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get scraped data for a run
  app.get("/api/runs/:id/scraped", async (req, res) => {
    try {
      const data = await storage.getScrapedDataByRunId(req.params.id);
      res.json(data);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get assertion results for a run
  app.get("/api/runs/:id/assertions", async (req, res) => {
    try {
      const assertions = await storage.getAssertionResultsByRunId(req.params.id);
      res.json(assertions);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  return httpServer;
}
