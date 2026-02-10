import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatMs } from "@/lib/utils/format";

interface StepData {
  avg_ms: number;
  count: number;
}

export function StepLatency({ latencies }: { latencies?: Record<string, StepData> | null }) {
  const entries = Object.entries(latencies ?? {});
  const maxMs = Math.max(...entries.map(([, d]) => d.avg_ms), 1);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Step Latency Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {entries.map(([step, data]) => (
          <div key={step} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>{step}</span>
              <span className="font-mono text-muted-foreground">{formatMs(data.avg_ms)}</span>
            </div>
            <div className="h-2 rounded bg-muted">
              <div
                className="h-full rounded bg-indigo-500/60"
                style={{ width: `${(data.avg_ms / maxMs) * 100}%` }}
              />
            </div>
          </div>
        ))}
        {entries.length === 0 && (
          <p className="text-xs text-muted-foreground">No latency data</p>
        )}
      </CardContent>
    </Card>
  );
}
