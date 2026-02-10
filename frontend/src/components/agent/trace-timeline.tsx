"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatMs, formatDate } from "@/lib/utils/format";
import type { Trace } from "@/lib/schemas/agent";

const STEP_COLORS: Record<string, string> = {
  route: "bg-purple-500",
  cache_check: "bg-blue-500",
  rag_query: "bg-cyan-500",
  compress: "bg-yellow-500",
  generate: "bg-indigo-500",
  cache_store: "bg-green-500",
};

export function TraceTimeline({ trace }: { trace: Trace | null }) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!trace) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          No traces yet. Generate a playground to see the pipeline trace.
        </CardContent>
      </Card>
    );
  }

  const maxLatency = Math.max(...(trace.steps?.map((s) => s.latency_ms) ?? [1]));

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          Latest Trace
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px]">{trace.final_model ?? "-"}</Badge>
            <span className="text-[10px] text-muted-foreground">{formatDate(trace.started_at)}</span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-xs text-muted-foreground">{trace.prompt}</p>
        <div className="space-y-1.5">
          {(trace.steps ?? []).map((step) => (
            <div key={step.step_order}>
              <button
                className="flex w-full items-center gap-2 rounded p-1 text-left hover:bg-muted/50"
                onClick={() => setExpanded(expanded === step.step_order ? null : step.step_order)}
              >
                <div className={`h-3 w-3 rounded-full ${STEP_COLORS[step.step_name] ?? "bg-gray-500"}`} />
                <span className="text-xs font-medium">{step.step_name}</span>
                <div className="flex-1">
                  <div
                    className={`h-2 rounded ${STEP_COLORS[step.step_name] ?? "bg-gray-500"} opacity-60`}
                    style={{ width: `${(step.latency_ms / maxLatency) * 100}%` }}
                  />
                </div>
                <span className="text-xs font-mono text-muted-foreground">{formatMs(step.latency_ms)}</span>
              </button>
              {expanded === step.step_order && step.metadata && (
                <pre className="ml-5 mt-1 rounded bg-muted p-2 text-[10px] text-muted-foreground">
                  {JSON.stringify(step.metadata, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-end text-xs text-muted-foreground">
          Total: {formatMs(trace.total_latency_ms ?? 0)}
        </div>
      </CardContent>
    </Card>
  );
}
