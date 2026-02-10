import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const METHOD_COLORS: Record<string, string> = {
  keyword: "bg-green-500",
  llm_3b: "bg-purple-500",
  forced: "bg-yellow-500",
  stream: "bg-blue-500",
};

export function RouterMethods({ methods }: { methods?: Record<string, number> | null }) {
  const entries = Object.entries(methods ?? {});
  const total = entries.reduce((sum, [, count]) => sum + count, 0) || 1;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Router Methods</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {entries.map(([method, count]) => (
          <div key={method} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>{method}</span>
              <span className="text-muted-foreground">{count}</span>
            </div>
            <div className="h-2 rounded bg-muted">
              <div
                className={`h-full rounded ${METHOD_COLORS[method] ?? "bg-gray-500"}`}
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
