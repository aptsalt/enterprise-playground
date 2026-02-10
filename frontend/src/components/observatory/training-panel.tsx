"use client";

import { useState } from "react";
import { useApiQuery } from "@/lib/hooks/use-api-query";
import { TrainingStatusSchema, TrainingLogsSchema, DatasetAnalyticsSchema, TrainingExamplesResponseSchema } from "@/lib/schemas/observatory";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { LossChart } from "@/components/observatory/loss-chart";

export function TrainingPanel() {
  const { data: status } = useApiQuery(
    ["training-status"],
    "/api/observatory/training/status",
    TrainingStatusSchema,
  );
  const { data: logs } = useApiQuery(
    ["training-logs"],
    "/api/observatory/training/logs",
    TrainingLogsSchema,
  );
  const { data: analytics } = useApiQuery(
    ["dataset-analytics"],
    "/api/observatory/dataset/analytics",
    DatasetAnalyticsSchema,
  );

  const [exFile, setExFile] = useState<"train" | "val">("train");
  const [exOffset, setExOffset] = useState(0);
  const { data: examples } = useApiQuery(
    ["training-examples", exFile, String(exOffset)],
    `/api/observatory/training/examples?file=${exFile}&offset=${exOffset}&limit=10`,
    TrainingExamplesResponseSchema,
  );

  const progressPct = status?.global_step && status.epoch
    ? Math.min(100, (status.epoch / 3) * 100)
    : 0;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between text-sm">
            Training Status
            <Badge
              variant="outline"
              className={status?.status === "running" ? "border-green-500/50 text-green-400" : ""}
            >
              {status?.status ?? "idle"}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-xs text-muted-foreground">{status?.message ?? "No training in progress"}</p>
          <Progress value={progressPct} className="h-2" />
          <div className="flex gap-4 text-xs">
            <span>Step: {status?.global_step ?? 0}</span>
            <span>Loss: {status?.loss?.toFixed(4) ?? "-"}</span>
          </div>
        </CardContent>
      </Card>

      {analytics?.quality_distribution && Object.keys(analytics.quality_distribution).length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Dataset Quality Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-2" style={{ height: 80 }}>
              {Object.entries(analytics.quality_distribution).map(([level, count]) => {
                const maxCount = Math.max(...Object.values(analytics.quality_distribution ?? {}));
                return (
                  <div key={level} className="flex flex-1 flex-col items-center gap-1">
                    <div
                      className="w-full rounded-t bg-purple-500/60"
                      style={{ height: `${maxCount > 0 ? (count / maxCount) * 100 : 0}%` }}
                    />
                    <span className="text-[10px] text-muted-foreground">Q{level}: {count}</span>
                  </div>
                );
              })}
            </div>
            <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
              <span>Train: {analytics.train_count ?? 0}</span>
              <span>Val: {analytics.val_count ?? 0}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <LossChart
        trainLoss={logs?.loss_curve ?? []}
        evalLoss={logs?.eval_losses ?? []}
      />

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm">Training Examples</CardTitle>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={exFile === "train" ? "default" : "outline"}
              onClick={() => { setExFile("train"); setExOffset(0); }}
            >
              Train
            </Button>
            <Button
              size="sm"
              variant={exFile === "val" ? "default" : "outline"}
              onClick={() => { setExFile("val"); setExOffset(0); }}
            >
              Val
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-64">
            <div className="space-y-3">
              {(examples?.examples ?? []).map((ex, i) => (
                <div key={i} className="rounded border border-border p-2">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-[10px]">#{exOffset + i + 1}</Badge>
                    {ex.quality !== undefined && (
                      <Badge variant="secondary" className="text-[10px]">Q{ex.quality}</Badge>
                    )}
                  </div>
                  <p className="text-xs font-medium">{ex.instruction}</p>
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-3">{ex.output}</p>
                </div>
              ))}
            </div>
          </ScrollArea>
          <div className="mt-2 flex items-center justify-between">
            <Button
              size="sm"
              variant="outline"
              disabled={exOffset === 0}
              onClick={() => setExOffset(Math.max(0, exOffset - 10))}
            >
              Prev
            </Button>
            <span className="text-xs text-muted-foreground">
              {exOffset + 1}-{exOffset + (examples?.examples.length ?? 0)} of {examples?.total ?? 0}
            </span>
            <Button
              size="sm"
              variant="outline"
              disabled={exOffset + 10 >= (examples?.total ?? 0)}
              onClick={() => setExOffset(exOffset + 10)}
            >
              Next
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
