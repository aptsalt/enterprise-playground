import { Card, CardContent } from "@/components/ui/card";
import { formatMs } from "@/lib/utils/format";
import type { Metrics } from "@/lib/schemas/system";

export function MetricsGrid({ data }: { data?: Metrics | null }) {
  const cards = [
    { label: "Total Generations", value: data?.total_generations ?? 0, color: "text-indigo-600 dark:text-indigo-400" },
    { label: "Cache Hit Rate", value: data?.cache_hit_rate ?? "0%", color: "text-blue-600 dark:text-blue-400" },
    { label: "Avg Latency", value: typeof data?.avg_latency_ms === "number" ? formatMs(data.avg_latency_ms) : "-", color: "text-amber-600 dark:text-yellow-400" },
    { label: "RAG Generations", value: data?.rag_generations ?? 0, color: "text-cyan-600 dark:text-cyan-400" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {cards.map((c) => (
        <Card key={c.label}>
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground">{c.label}</p>
            <p className={`text-2xl font-bold ${c.color}`}>{String(c.value)}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
