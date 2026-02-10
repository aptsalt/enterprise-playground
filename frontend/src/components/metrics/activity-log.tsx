import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { formatMs, formatDate } from "@/lib/utils/format";

export function ActivityLog({ activities }: { activities: Record<string, unknown>[] }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64">
          <div className="space-y-1.5">
            {activities.slice(0, 15).map((a, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded border border-border px-2 py-1.5 text-xs"
              >
                <span className="max-w-[50%] truncate">{String(a.prompt ?? a.task ?? "-")}</span>
                <div className="flex items-center gap-2">
                  {a.model ? (
                    <Badge variant="outline" className="text-[10px]">
                      {String(a.model)}
                    </Badge>
                  ) : null}
                  {typeof a.latency_ms === "number" ? (
                    <span className="font-mono text-muted-foreground">
                      {formatMs(a.latency_ms)}
                    </span>
                  ) : null}
                  {a.created ? (
                    <span className="text-muted-foreground">{formatDate(String(a.created))}</span>
                  ) : null}
                </div>
              </div>
            ))}
            {activities.length === 0 && (
              <p className="py-4 text-center text-muted-foreground">No activity yet</p>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
