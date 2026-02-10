"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { MetricsSchema } from "@/lib/schemas/system";
import { ModelCard } from "@/components/metrics/model-card";
import { MetricsGrid } from "@/components/metrics/metrics-grid";
import { VramGauge } from "@/components/metrics/vram-gauge";
import { ActivityLog } from "@/components/metrics/activity-log";

export function MetricsTab() {
  const { data } = useApiQuery(["metrics"], "/api/metrics", MetricsSchema, {
    refetchInterval: 15_000,
  });

  const models = data?.models ?? {};
  const generator = models["generator"] ?? models["qwen2.5-coder:14b"] ?? {};
  const router = models["router"] ?? models["qwen2.5:3b"] ?? {};

  return (
    <div className="space-y-4 p-4 lg:p-6">
      <div className="grid gap-4 lg:grid-cols-2">
        <ModelCard title="Generator (14B)" model={generator as Record<string, unknown>} color="text-indigo-400" />
        <ModelCard title="Router (3B)" model={router as Record<string, unknown>} color="text-purple-400" />
      </div>

      <MetricsGrid data={data} />

      <div className="grid gap-4 lg:grid-cols-3">
        <VramGauge vram={data?.vram} />
        <div className="lg:col-span-2">
          <ActivityLog activities={data?.recent_activity ?? []} />
        </div>
      </div>
    </div>
  );
}
