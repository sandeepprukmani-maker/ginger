import { useEffect, useRef, useState } from "react";
import { queryClient } from "@/lib/queryClient";
import type { WSMessage } from "@shared/schema";

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connected");
        setIsConnected(true);
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setIsConnected(false);
        wsRef.current = null;

        // Reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleMessage = (message: WSMessage) => {
    switch (message.type) {
      case "run_status":
        // Invalidate run queries to refetch updated status
        queryClient.invalidateQueries({ queryKey: ["/api/runs"] });
        queryClient.invalidateQueries({ queryKey: ["/api/runs", message.runId] });
        break;

      case "step_update":
        // Invalidate steps query for the run
        queryClient.invalidateQueries({ queryKey: ["/api/runs", message.runId, "steps"] });
        break;

      case "scraped_data":
        // Invalidate scraped data query for live updates
        queryClient.invalidateQueries({ queryKey: ["/api/runs", message.runId, "scraped"] });
        break;

      case "assertion_result":
        // Invalidate assertions query for live updates
        queryClient.invalidateQueries({ queryKey: ["/api/runs", message.runId, "assertions"] });
        break;

      case "log":
        // Logs are handled by individual components if needed
        console.log(`[${message.level}] ${message.message}`);
        break;
    }
  };

  return { isConnected };
}
