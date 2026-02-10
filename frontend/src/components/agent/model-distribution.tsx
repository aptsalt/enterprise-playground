import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const MODEL_COLORS: Record<string, string> = {
  "14b": "bg-indigo-500",
  "3b": "bg-purple-500",
  cache: "bg-blue-500",
};

export function ModelDistribution({ distribution }: { distribution?: Record<string, number> | null }) {
  const entries = Object.entries(distribution ?? {});
  const total = entries.reduce((sum, [, count]) => sum + count, 0) || 1;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Model Distribution</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {entries.map(([model, count]) => (
          <div key={model} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>{model}</span>
              <span className="text-muted-foreground">{((count / total) * 100).toFixed(0)}%</span>
            </div>
            <div className="h-2 rounded bg-muted">
              <div
                className={`h-full rounded ${MODEL_COLORS[model] ?? "bg-gray-500"}`}
                style={{ width: `${(count / total) * 100}%` }}
              />
            </div>
          </div>
        ))}
        {entries.length === 0 && (
          <p className="text-xs text-muted-foreground">No data</p>
        )}
      </CardContent>
    </Card>
  );
}
