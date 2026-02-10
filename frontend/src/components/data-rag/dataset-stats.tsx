"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { DatasetStatsSchema } from "@/lib/schemas/system";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DatasetStats() {
  const { data } = useApiQuery(
    ["dataset-stats"],
    "/api/dataset/stats",
    DatasetStatsSchema,
    { refetchInterval: 30_000 },
  );

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Training Dataset</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">JSONL Files</p>
            <p className="text-2xl font-bold">{data?.training_files ?? 0}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total Examples</p>
            <p className="text-2xl font-bold">{data?.total_examples ?? 0}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
