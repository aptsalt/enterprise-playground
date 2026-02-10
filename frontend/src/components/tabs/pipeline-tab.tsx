"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { PipelineStatusSchema } from "@/lib/schemas/system";
import { PhaseCard } from "@/components/pipeline/phase-card";

const PHASE_META: { key: string; label: string; color: string; description: string }[] = [
  { key: "scrape", label: "Scrape", color: "text-orange-400", description: "Playwright + BeautifulSoup capture" },
  { key: "map", label: "Map", color: "text-yellow-400", description: "Rule-based + 3B LLM structuring" },
  { key: "store", label: "Store / RAG", color: "text-cyan-400", description: "ChromaDB + nomic-embed-text" },
  { key: "route", label: "Route", color: "text-purple-400", description: "Keyword + 3B classifier" },
  { key: "generate", label: "Generate", color: "text-indigo-400", description: "14B Coder + RAG context" },
  { key: "cache", label: "Cache", color: "text-blue-400", description: "Semantic similarity matching" },
  { key: "train", label: "Fine-Tune", color: "text-red-400", description: "QLoRA + PEFT on your data" },
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
          End-to-end: Scrape → Structure → Embed → Route → Generate → Cache → Train
        </p>
      </div>

      <div className="flex items-center justify-center py-2">
        <div className="flex items-center gap-1">
          {PHASE_META.map((p, i) => (
            <div key={p.key} className="flex items-center gap-1">
              <span className={`text-xs font-medium ${p.color}`}>{p.label}</span>
              {i < PHASE_META.length - 1 && (
                <span className="text-muted-foreground">&rarr;</span>
              )}
            </div>
          ))}
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
          />
        ))}
      </div>
    </div>
  );
}
