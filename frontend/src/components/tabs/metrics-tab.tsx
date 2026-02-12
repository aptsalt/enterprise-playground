"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { MetricsSchema } from "@/lib/schemas/system";
import { ModelCard } from "@/components/metrics/model-card";
import { MetricsGrid } from "@/components/metrics/metrics-grid";
import { VramGauge } from "@/components/metrics/vram-gauge";
import { ActivityLog } from "@/components/metrics/activity-log";
import { FeatureInfoDialog } from "@/components/ui/feature-info-dialog";

export function MetricsTab() {
  const { data } = useApiQuery(["metrics"], "/api/metrics", MetricsSchema, {
    refetchInterval: 15_000,
  });

  const models = data?.models ?? data?.model_breakdown ?? {};
  const generatorApi = models["generator"] ?? models["qwen2.5-coder:14b"] ?? {};
  const routerApi = models["router"] ?? models["qwen2.5:3b"] ?? {};

  const generator = {
    role: "HTML/CSS/JS generation",
    vram_gb: 8.5,
    ctx_size: 8192,
    max_tokens: 6144,
    temperature: 0.7,
    ...generatorApi,
  } as Record<string, unknown>;

  const router = {
    role: "Classification & routing",
    vram_gb: 2.0,
    ctx_size: 2048,
    max_tokens: 512,
    temperature: 0.1,
    ...routerApi,
  } as Record<string, unknown>;

  return (
    <div className="space-y-4 p-4 lg:p-6">
      <div className="grid gap-4 lg:grid-cols-2">
        <ModelCard
          title="Generator (14B)"
          model={generator as Record<string, unknown>}
          color="text-indigo-600 dark:text-indigo-400"
          featureId="dual-model"
        />
        <ModelCard
          title="Router (3B)"
          model={router as Record<string, unknown>}
          color="text-purple-600 dark:text-purple-400"
          featureId="smart-router"
        />
      </div>

      <MetricsGrid data={data} />

      <div className="grid gap-4 lg:grid-cols-3">
        <VramGauge vram={data?.vram} />
        <div className="lg:col-span-2">
          <ActivityLog activities={data?.recent_activity ?? data?.recent ?? []} />
        </div>
      </div>
    </div>
  );
}
