"use client";

import { useState } from "react";
import { useApiQuery } from "@/lib/hooks/use-api-query";
import { ChunkAnalyticsSchema } from "@/lib/schemas/rag";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { z } from "zod";

const ChunkListSchema = z.object({
  chunks: z.array(z.object({
    id: z.string().optional(),
    content: z.string(),
    metadata: z.record(z.string(), z.unknown()).optional(),
  })),
  total: z.number(),
});

export function RagChunkingPanel() {
  const { data: analytics } = useApiQuery(
    ["chunk-analytics"],
    "/api/observatory/chunk-analytics",
    ChunkAnalyticsSchema,
  );
  const [offset, setOffset] = useState(0);
  const { data: chunkData } = useApiQuery(
    ["chunks", String(offset)],
    `/api/observatory/chunks?offset=${offset}&limit=20`,
    ChunkListSchema,
  );

  const maxHistCount = Math.max(...(analytics?.histogram?.map((h) => h.count) ?? [1]));

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Chunks", value: analytics?.total ?? 0 },
          { label: "Avg Size", value: `${analytics?.avg_size ?? 0} chars` },
          { label: "Min Size", value: `${analytics?.min_size ?? 0} chars` },
          { label: "Max Size", value: `${analytics?.max_size ?? 0} chars` },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="p-3">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className="text-xl font-bold">{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {analytics?.histogram && analytics.histogram.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Chunk Size Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-2" style={{ height: 160 }}>
              {analytics.histogram.map((bin, i) => (
                <div key={i} className="flex flex-1 flex-col items-center" style={{ height: "100%" }}>
                  <div className="flex flex-1 w-full items-end">
                    <div
                      className="w-full rounded-t bg-primary/60"
                      style={{ height: `${(bin.count / maxHistCount) * 100}%`, minHeight: bin.count > 0 ? 4 : 0 }}
                    />
                  </div>
                  <span className="mt-1 text-[10px] font-mono font-medium">{bin.count}</span>
                  <span className="text-[9px] text-muted-foreground">{bin.label ?? bin.range ?? ""}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {analytics?.workflows && Object.keys(analytics.workflows).length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Chunks per Workflow</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(analytics.workflows).map(([name, count]) => (
                <Badge key={name} variant="outline" className="text-xs">
                  {name}: {count}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm">Chunk Browser</CardTitle>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 20))}
            >
              Prev
            </Button>
            <span className="text-xs text-muted-foreground">
              {offset + 1}-{offset + (chunkData?.chunks.length ?? 0)} of {chunkData?.total ?? 0}
            </span>
            <Button
              size="sm"
              variant="outline"
              disabled={offset + 20 >= (chunkData?.total ?? 0)}
              onClick={() => setOffset(offset + 20)}
            >
              Next
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-64">
            <div className="space-y-2">
              {(chunkData?.chunks ?? []).map((chunk, i) => (
                <ChunkItem key={chunk.id ?? i} chunk={chunk} />
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

function ChunkItem({ chunk }: { chunk: { id?: string; content: string; metadata?: Record<string, unknown> } }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded border border-border p-2">
      <div className="flex items-start justify-between gap-2">
        <p className={`text-xs text-muted-foreground ${expanded ? "" : "line-clamp-2"}`}>
          {chunk.content}
        </p>
        <Button
          size="sm"
          variant="ghost"
          className="shrink-0 text-[10px]"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Less" : "More"}
        </Button>
      </div>
      {chunk.id && (
        <p className="mt-1 text-[10px] font-mono text-muted-foreground/60">{chunk.id}</p>
      )}
    </div>
  );
}
