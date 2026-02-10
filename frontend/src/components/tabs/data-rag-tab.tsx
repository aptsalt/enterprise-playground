"use client";

import { RagStatusCard } from "@/components/data-rag/rag-status-card";
import { RagQueryTester } from "@/components/data-rag/rag-query-tester";
import { DatasetStats } from "@/components/data-rag/dataset-stats";
import { DatasetPrepare } from "@/components/data-rag/dataset-prepare";
import { WorkflowBrowser } from "@/components/data-rag/workflow-browser";

export function DataRagTab() {
  return (
    <div className="grid gap-4 p-4 lg:grid-cols-2 lg:p-6">
      <div className="space-y-4">
        <RagStatusCard />
        <RagQueryTester />
        <DatasetPrepare />
      </div>
      <div className="space-y-4">
        <DatasetStats />
        <WorkflowBrowser />
      </div>
    </div>
  );
}
