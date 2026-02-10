"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import type { RagChunk } from "@/lib/schemas/rag";

export function RagQueryTester() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<RagChunk[]>([]);
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("/api/rag/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 5 }),
      });
      const data = await res.json();
      setResults(data.chunks ?? []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">RAG Query Tester</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input
            placeholder="Test a RAG query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleQuery()}
          />
          <Button size="sm" onClick={handleQuery} disabled={loading}>
            {loading ? "..." : "Query"}
          </Button>
        </div>
        {results.length > 0 && (
          <ScrollArea className="h-48">
            <div className="space-y-2">
              {results.map((r, i) => (
                <div key={i} className="rounded border border-border bg-muted/50 p-2">
                  <div className="mb-1 flex items-center gap-2">
                    <Badge variant="outline" className="text-[10px]">
                      #{i + 1}
                    </Badge>
                    {r.distance !== undefined && (
                      <span className="text-[10px] text-muted-foreground">
                        dist: {r.distance.toFixed(3)}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-3">{r.content}</p>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
