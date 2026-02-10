"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { WorkflowListSchema } from "@/lib/schemas/playground";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

export function WorkflowBrowser() {
  const { data: workflows } = useApiQuery(
    ["workflows"],
    "/api/workflows",
    WorkflowListSchema,
  );

  const handleGenerate = async (workflowId: string) => {
    await fetch("/api/generate/workflow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workflow_id: workflowId }),
    });
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Workflows ({workflows?.length ?? 0})</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-80">
          <div className="space-y-2">
            {(workflows ?? []).map((wf) => (
              <div
                key={wf.workflow_id}
                className="flex items-center justify-between rounded border border-border p-2"
              >
                <div>
                  <p className="text-xs font-medium">{wf.name}</p>
                  <Badge variant="outline" className="mt-1 text-[10px]">
                    {wf.category}
                  </Badge>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleGenerate(wf.workflow_id)}
                >
                  Generate
                </Button>
              </div>
            ))}
            {(!workflows || workflows.length === 0) && (
              <p className="py-4 text-center text-xs text-muted-foreground">
                No workflows found. Run the scraper first.
              </p>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
