"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FeedbackButtons } from "@/components/ai/feedback-buttons";
import { ConfidenceIndicator } from "@/components/ai/confidence-indicator";

interface SSEData {
  state: string;
  html: string;
  ragChunks: number;
  ragPreview: string[];
  playgroundId: string | null;
  error: string | null;
}

export function StreamPanel({ sse }: { sse: SSEData }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm">Output</CardTitle>
          <div className="flex items-center gap-2">
            {sse.state === "streaming" && (
              <Badge variant="outline" className="animate-pulse border-indigo-500 text-indigo-600 dark:text-indigo-400">
                Streaming
              </Badge>
            )}
            {sse.state === "done" && sse.playgroundId && (
              <>
                <ConfidenceIndicator
                  confidence={0.85}
                  routerMethod="keyword"
                  model="14b"
                />
                <FeedbackButtons
                  playgroundId={sse.playgroundId}
                  prompt={sse.html.slice(0, 100)}
                />
                <a
                  href={`/playground/${sse.playgroundId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-indigo-600 dark:text-indigo-400 underline"
                >
                  Open Playground
                </a>
              </>
            )}
            {sse.state === "error" && (
              <Badge variant="destructive">{sse.error}</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-80">
            <pre
              className="whitespace-pre-wrap font-mono text-xs text-muted-foreground"
              role="log"
              aria-live="polite"
              aria-label="Generation output"
            >
              {sse.html || "Waiting for response..."}
            </pre>
          </ScrollArea>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">RAG Context</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-2 text-xs text-muted-foreground" aria-live="polite">
            {sse.ragChunks} chunks injected
          </p>
          <ScrollArea className="h-72">
            <div className="space-y-2" role="list" aria-label="RAG context chunks">
              {sse.ragPreview.map((chunk, i) => (
                <div
                  key={i}
                  role="listitem"
                  className="rounded border border-border bg-muted/50 p-2 text-xs text-muted-foreground"
                >
                  {chunk}
                </div>
              ))}
              {sse.ragPreview.length === 0 && (
                <p className="text-xs text-muted-foreground/60">No RAG context yet</p>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
