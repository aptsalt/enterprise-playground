"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useApiQuery } from "@/lib/hooks/use-api-query";
import { RagStatsSchema } from "@/lib/schemas/rag";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function RagStatusCard() {
  const queryClient = useQueryClient();
  const { data: rag } = useApiQuery(["rag-stats"], "/api/rag/stats", RagStatsSchema);
  const [ingesting, setIngesting] = useState(false);

  const handleIngest = async () => {
    setIngesting(true);
    try {
      await fetch("/api/rag/ingest", { method: "POST" });
      await queryClient.invalidateQueries({ queryKey: ["rag-stats"] });
    } finally {
      setIngesting(false);
    }
  };

  const handleClear = async () => {
    await fetch("/api/rag/clear", { method: "POST" });
    await queryClient.invalidateQueries({ queryKey: ["rag-stats"] });
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          RAG Pipeline
          <Badge variant="outline" className="border-cyan-500/50 text-cyan-600 dark:text-cyan-400">
            ChromaDB
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-muted-foreground">Chunks</span>
            <p className="font-mono font-bold">{rag?.total_chunks ?? 0}</p>
          </div>
          <div>
            <span className="text-muted-foreground">Embed Model</span>
            <p className="font-mono">{rag?.embed_model ?? "nomic-embed-text"}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={handleIngest} disabled={ingesting}>
            {ingesting ? "Ingesting..." : "Ingest Workflows"}
          </Button>
          <Button size="sm" variant="destructive" onClick={handleClear}>
            Clear
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
