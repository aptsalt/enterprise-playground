"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { StatsSchema } from "@/lib/schemas/system";
import { RagStatsSchema } from "@/lib/schemas/rag";
import { Card, CardContent } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils/format";

export function StatsRow() {
  const { data: stats } = useApiQuery(["stats"], "/api/stats", StatsSchema, {
    refetchInterval: 30_000,
  });
  const { data: rag } = useApiQuery(["rag-stats"], "/api/rag/stats", RagStatsSchema, {
    refetchInterval: 60_000,
  });

  const cards = [
    { label: "Playgrounds", value: stats?.playgrounds_count ?? 0, color: "text-indigo-400" },
    { label: "Cache Entries", value: stats?.cache_entries ?? 0, color: "text-blue-400" },
    { label: "RAG Chunks", value: rag?.total_chunks ?? 0, color: "text-cyan-400" },
    { label: "Workflows", value: stats?.workflows_count ?? 0, color: "text-emerald-400" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {cards.map((c) => (
        <Card key={c.label}>
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground">{c.label}</p>
            <p className={`text-2xl font-bold ${c.color}`}>
              {formatNumber(c.value)}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
