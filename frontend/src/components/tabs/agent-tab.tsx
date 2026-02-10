"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { AgentStatsSchema, TraceSchema } from "@/lib/schemas/agent";
import { AgentStatsRow } from "@/components/agent/agent-stats-row";
import { TraceTimeline } from "@/components/agent/trace-timeline";
import { ModelDistribution } from "@/components/agent/model-distribution";
import { RouterMethods } from "@/components/agent/router-methods";
import { StepLatency } from "@/components/agent/step-latency";
import { TokenEconomy } from "@/components/agent/token-economy";
import { TraceTable } from "@/components/agent/trace-table";
import { z } from "zod";

export function AgentTab() {
  const { data: stats } = useApiQuery(
    ["agent-stats"],
    "/api/agent/stats",
    AgentStatsSchema,
    { refetchInterval: 10_000 },
  );
  const { data: traces } = useApiQuery(
    ["agent-traces"],
    "/api/agent/traces?limit=30",
    z.array(TraceSchema),
    { refetchInterval: 10_000 },
  );

  const latestTrace = traces?.[0] ?? null;

  return (
    <div className="space-y-4 p-4 lg:p-6">
      <AgentStatsRow stats={stats} />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TraceTimeline trace={latestTrace} />
        </div>
        <div className="space-y-4">
          <ModelDistribution distribution={stats?.model_distribution} />
          <RouterMethods methods={stats?.router_methods} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <StepLatency latencies={stats?.step_avg_latencies} />
        <TokenEconomy economy={stats?.token_economy} />
      </div>

      <TraceTable traces={traces ?? []} />
    </div>
  );
}
