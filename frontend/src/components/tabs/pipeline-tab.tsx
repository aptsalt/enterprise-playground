"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { PipelineStatusSchema } from "@/lib/schemas/system";
import { PhaseCard } from "@/components/pipeline/phase-card";
import { FeatureInfoDialog } from "@/components/ui/feature-info-dialog";
import { getFeatureIdForPhase } from "@/lib/data/feature-info";

const PHASE_META: { key: string; label: string; color: string; description: string }[] = [
  { key: "scrape", label: "Scrape", color: "text-orange-600 dark:text-orange-400", description: "Playwright + BeautifulSoup capture" },
  { key: "map", label: "Map", color: "text-amber-600 dark:text-yellow-400", description: "Rule-based + 3B LLM structuring" },
  { key: "store", label: "Store / RAG", color: "text-cyan-600 dark:text-cyan-400", description: "ChromaDB + nomic-embed-text" },
  { key: "route", label: "Route", color: "text-purple-600 dark:text-purple-400", description: "Keyword + 3B classifier" },
  { key: "generate", label: "Generate", color: "text-indigo-600 dark:text-indigo-400", description: "14B Coder + RAG context" },
  { key: "cache", label: "Cache", color: "text-blue-600 dark:text-blue-400", description: "Semantic similarity matching" },
  { key: "train", label: "Fine-Tune", color: "text-red-600 dark:text-red-400", description: "QLoRA + PEFT on your data" },
];

export function PipelineTab() {
  const { data } = useApiQuery(
    ["pipeline-status"],
    "/api/pipeline/status",
    PipelineStatusSchema,
    { refetchInterval: 30_000 },
  );

  return (
    <div className="space-y-4 p-4 lg:p-6">
      <div>
        <h2 className="text-lg font-semibold">ML Pipeline</h2>
        <p className="text-sm text-muted-foreground">
          End-to-end: Scrape &rarr; Structure &rarr; Embed &rarr; Route &rarr; Generate &rarr; Cache &rarr; Train
        </p>
      </div>

      <div className="flex items-center justify-center py-2">
        <div className="flex items-center gap-1">
          {PHASE_META.map((p, i) => {
            const featureId = getFeatureIdForPhase(p.key);
            const label = (
              <span className={`text-xs font-bold ${p.color}`}>{p.label}</span>
            );

            return (
              <div key={p.key} className="flex items-center gap-1">
                {featureId ? (
                  <FeatureInfoDialog featureId={featureId}>
                    {label}
                  </FeatureInfoDialog>
                ) : (
                  label
                )}
                {i < PHASE_META.length - 1 && (
                  <span className="text-muted-foreground">&rarr;</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {PHASE_META.map((p) => (
          <PhaseCard
            key={p.key}
            label={p.label}
            color={p.color}
            description={p.description}
            count={data?.phases?.[p.key]?.count ?? 0}
            phaseKey={p.key}
          />
        ))}
      </div>
    </div>
  );
}
