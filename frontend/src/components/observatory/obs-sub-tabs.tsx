"use client";

import { useDashboardStore, type ObsSubTab } from "@/lib/store/dashboard-store";
import { cn } from "@/lib/utils";

const SUB_TABS: { id: ObsSubTab; label: string }[] = [
  { id: "rag-chunking", label: "RAG & Chunking" },
  { id: "training", label: "Training Lifecycle" },
  { id: "adapters", label: "Adapter Registry" },
  { id: "pipeline-diagram", label: "Pipeline Diagram" },
  { id: "embeddings", label: "Embeddings" },
];

export function ObsSubTabs() {
  const active = useDashboardStore((s) => s.obsSubTab);
  const setActive = useDashboardStore((s) => s.setObsSubTab);

  return (
    <div className="flex gap-1 rounded-lg bg-muted p-1" role="tablist" aria-label="Observatory sub-tabs">
      {SUB_TABS.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActive(tab.id)}
          role="tab"
          aria-selected={active === tab.id}
          tabIndex={active === tab.id ? 0 : -1}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-ring",
            active === tab.id
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
