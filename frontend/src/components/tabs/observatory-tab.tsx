"use client";

import { useDashboardStore } from "@/lib/store/dashboard-store";
import { ObsSubTabs } from "@/components/observatory/obs-sub-tabs";
import { RagChunkingPanel } from "@/components/observatory/rag-chunking-panel";
import { TrainingPanel } from "@/components/observatory/training-panel";
import { AdapterPanel } from "@/components/observatory/adapter-panel";
import { PipelineDiagram } from "@/components/observatory/pipeline-diagram";
import { EmbeddingVisualizer } from "@/components/ai/embedding-visualizer";

export function ObservatoryTab() {
  const subTab = useDashboardStore((s) => s.obsSubTab);

  return (
    <div className="space-y-4 p-4 lg:p-6">
      <div>
        <h2 className="text-lg font-semibold">ML Observatory</h2>
        <p className="text-sm text-muted-foreground">Deep observability into RAG, training, and model lifecycle</p>
      </div>
      <ObsSubTabs />
      {subTab === "rag-chunking" && <RagChunkingPanel />}
      {subTab === "training" && <TrainingPanel />}
      {subTab === "adapters" && <AdapterPanel />}
      {subTab === "pipeline-diagram" && <PipelineDiagram />}
      {subTab === "embeddings" && <EmbeddingVisualizer />}
    </div>
  );
}
