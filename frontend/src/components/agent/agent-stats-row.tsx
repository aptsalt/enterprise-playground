import { Card, CardContent } from "@/components/ui/card";
import { formatMs, formatNumber } from "@/lib/utils/format";
import type { AgentStats } from "@/lib/schemas/agent";

export function AgentStatsRow({ stats }: { stats?: AgentStats | null }) {
  const cards = [
    { label: "Total Traces", value: formatNumber(stats?.total_traces ?? 0), color: "text-indigo-400" },
    { label: "Avg Latency", value: formatMs(stats?.avg_latency_ms ?? 0), color: "text-yellow-400" },
    { label: "Cache Hit Rate", value: stats?.cache_hit_rate ?? "0%", color: "text-blue-400" },
    { label: "Avg Confidence", value: (stats?.avg_confidence ?? 0).toFixed(2), color: "text-green-400" },
    { label: "Tokens Saved", value: formatNumber(stats?.token_economy?.total_saved ?? 0), color: "text-cyan-400" },
    { label: "Last 24h", value: formatNumber(stats?.last_24h_traces ?? 0), color: "text-purple-400" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map((c) => (
        <Card key={c.label}>
          <CardContent className="p-3">
            <p className="text-[10px] text-muted-foreground">{c.label}</p>
            <p className={`text-xl font-bold ${c.color}`}>{c.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
