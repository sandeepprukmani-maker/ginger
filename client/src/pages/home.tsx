import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { 
  Play, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Loader2,
  Terminal,
  Download,
  ChevronRight,
  Activity,
  Wifi,
  WifiOff
} from "lucide-react";
import type { AutomationRun, ExecutionStep, ScrapedData, AssertionResult } from "@shared/schema";
import { useWebSocket } from "@/hooks/use-websocket";

export default function Home() {
  const { isConnected } = useWebSocket();
  const [command, setCommand] = useState("");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  // Fetch all runs
  const { data: runs = [] } = useQuery<AutomationRun[]>({
    queryKey: ["/api/runs"],
  });

  // Fetch selected run details with polling for running automations
  const { data: selectedRun } = useQuery<AutomationRun>({
    queryKey: ["/api/runs", selectedRunId],
    enabled: !!selectedRunId,
    refetchInterval: 1000,
  });

  const { data: steps = [] } = useQuery<ExecutionStep[]>({
    queryKey: ["/api/runs", selectedRunId, "steps"],
    enabled: !!selectedRunId,
    refetchInterval: selectedRun?.status === "running" ? 1000 : false,
  });

  const { data: scrapedData = [] } = useQuery<ScrapedData[]>({
    queryKey: ["/api/runs", selectedRunId, "scraped"],
    enabled: !!selectedRunId,
  });

  const { data: assertions = [] } = useQuery<AssertionResult[]>({
    queryKey: ["/api/runs", selectedRunId, "assertions"],
    enabled: !!selectedRunId,
  });

  // Create new automation run
  const createRunMutation = useMutation({
    mutationFn: async (cmd: string) => {
      const response = await apiRequest("POST", "/api/runs", { command: cmd });
      return await response.json() as AutomationRun;
    },
    onSuccess: (data: AutomationRun) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runs"] });
      setSelectedRunId(data.id);
      setCommand("");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (command.trim()) {
      createRunMutation.mutate(command);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: { icon: Clock, className: "bg-chart-3/10 text-chart-3 border-chart-3/20" },
      running: { icon: Loader2, className: "bg-chart-4/10 text-chart-4 border-chart-4/20" },
      completed: { icon: CheckCircle2, className: "bg-chart-2/10 text-chart-2 border-chart-2/20" },
      failed: { icon: XCircle, className: "bg-destructive/10 text-destructive border-destructive/20" },
    };
    
    const variant = variants[status as keyof typeof variants] || variants.pending;
    const Icon = variant.icon;
    
    return (
      <Badge variant="outline" className={`${variant.className} border`}>
        <Icon className={`w-3 h-3 mr-1 ${status === 'running' ? 'animate-spin' : ''}`} />
        {status}
      </Badge>
    );
  };

  const exportToJSON = () => {
    if (!selectedRun) return;
    const data = {
      run: selectedRun,
      steps,
      scrapedData,
      assertions,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `automation-${selectedRun.id}.json`;
    a.click();
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - Run History */}
      <div className="w-80 border-r border-border bg-card flex flex-col">
        <div className="p-4 border-b border-card-border">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              Run History
            </h2>
            <div className="flex items-center gap-1" title={isConnected ? "Connected" : "Disconnected"}>
              {isConnected ? (
                <Wifi className="w-4 h-4 text-chart-2" />
              ) : (
                <WifiOff className="w-4 h-4 text-muted-foreground" />
              )}
            </div>
          </div>
        </div>
        
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {runs.map((run) => (
              <button
                key={run.id}
                data-testid={`run-item-${run.id}`}
                onClick={() => setSelectedRunId(run.id)}
                className={`w-full text-left p-3 rounded-md transition-colors hover-elevate active-elevate-2 ${
                  selectedRunId === run.id ? 'bg-accent' : ''
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  {getStatusBadge(run.status)}
                  <span className="text-xs text-muted-foreground">
                    {new Date(run.createdAt).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-sm font-mono line-clamp-2">{run.command}</p>
              </button>
            ))}
            
            {runs.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <Terminal className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">No automation runs yet</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Command Input */}
        <div className="p-6 border-b border-border bg-card">
          <form onSubmit={handleSubmit} className="space-y-3">
            <label className="text-sm font-medium">Natural Language Command</label>
            <Textarea
              data-testid="input-command"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="Example: Go to google.com, search for 'web automation', and extract the top 5 result titles"
              className="min-h-[100px] font-mono text-sm resize-none"
              disabled={createRunMutation.isPending}
            />
            <div className="flex items-center gap-3">
              <Button
                type="submit"
                data-testid="button-execute"
                disabled={!command.trim() || createRunMutation.isPending}
                className="gap-2"
              >
                {createRunMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Execute Automation
                  </>
                )}
              </Button>
              
              <p className="text-xs text-muted-foreground">
                The AI will automatically identify elements and execute your instructions
              </p>
            </div>
          </form>
        </div>

        {/* Results Area */}
        <ScrollArea className="flex-1 p-6">
          {selectedRun ? (
            <div className="space-y-6 max-w-6xl">
              {/* Run Header */}
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-2">
                      <CardTitle className="flex items-center gap-3">
                        Automation Run
                        {getStatusBadge(selectedRun.status)}
                      </CardTitle>
                      <p className="text-sm font-mono text-muted-foreground">
                        {selectedRun.command}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      data-testid="button-export-json"
                      onClick={exportToJSON}
                      className="gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Export JSON
                    </Button>
                  </div>
                </CardHeader>
                
                {selectedRun.error && (
                  <CardContent>
                    <div className="bg-destructive/10 border border-destructive/20 rounded-md p-4">
                      <p className="text-sm text-destructive font-mono">{selectedRun.error}</p>
                    </div>
                  </CardContent>
                )}
              </Card>

              {/* Execution Steps */}
              {steps.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Execution Steps</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {steps.map((step, idx) => (
                      <div key={step.id} data-testid={`step-${step.id}`}>
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold">
                            {idx + 1}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline" className="text-xs">
                                {step.stepType}
                              </Badge>
                              {getStatusBadge(step.status)}
                            </div>
                            
                            <p className="text-sm mb-1">{step.description}</p>
                            
                            {step.selector && (
                              <p className="text-xs font-mono text-muted-foreground">
                                Selector: {step.selector}
                              </p>
                            )}
                            
                            {step.result && (
                              <div className="mt-2 bg-muted/50 rounded-md p-2">
                                <pre className="text-xs font-mono overflow-x-auto">
                                  {JSON.stringify(step.result, null, 2)}
                                </pre>
                              </div>
                            )}
                            
                            {step.error && (
                              <p className="text-xs text-destructive mt-1">{step.error}</p>
                            )}
                          </div>
                        </div>
                        
                        {idx < steps.length - 1 && (
                          <div className="ml-4 my-2">
                            <ChevronRight className="w-4 h-4 text-muted-foreground rotate-90" />
                          </div>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Scraped Data */}
              {scrapedData.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Scraped Data</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {scrapedData.map((item) => (
                        <div key={item.id} data-testid={`scraped-${item.id}`} className="bg-muted/30 rounded-md p-3">
                          <pre className="text-xs font-mono overflow-x-auto">
                            {JSON.stringify(item.data, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Assertions */}
              {assertions.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Assertions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {assertions.map((assertion) => (
                        <div
                          key={assertion.id}
                          data-testid={`assertion-${assertion.id}`}
                          className={`flex items-start gap-3 p-3 rounded-md border ${
                            assertion.passed === "true"
                              ? "bg-chart-2/5 border-chart-2/20"
                              : "bg-destructive/5 border-destructive/20"
                          }`}
                        >
                          {assertion.passed === "true" ? (
                            <CheckCircle2 className="w-5 h-5 text-chart-2 flex-shrink-0" />
                          ) : (
                            <XCircle className="w-5 h-5 text-destructive flex-shrink-0" />
                          )}
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline" className="text-xs">
                                {assertion.assertionType}
                              </Badge>
                            </div>
                            
                            {assertion.message && (
                              <p className="text-sm mb-2">{assertion.message}</p>
                            )}
                            
                            <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                              {assertion.expected && (
                                <div>
                                  <span className="text-muted-foreground">Expected: </span>
                                  <span>{assertion.expected}</span>
                                </div>
                              )}
                              {assertion.actual && (
                                <div>
                                  <span className="text-muted-foreground">Actual: </span>
                                  <span>{assertion.actual}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center">
                <Terminal className="w-16 h-16 mx-auto mb-4 opacity-30" />
                <h3 className="text-lg font-medium mb-2">No Automation Selected</h3>
                <p className="text-sm">
                  Enter a command above or select a run from the history
                </p>
              </div>
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
}
