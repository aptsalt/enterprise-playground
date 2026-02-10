"use client";

import { useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ComparisonResult {
  model: string;
  html: string;
  latency: number;
  tokens: number;
}

interface Props {
  prompt: string;
}

export function ABComparison({ prompt }: Props) {
  const [results, setResults] = useState<[ComparisonResult | null, ComparisonResult | null]>([null, null]);
  const [loading, setLoading] = useState(false);
  const [winner, setWinner] = useState<"a" | "b" | null>(null);

  const runComparison = useCallback(async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setWinner(null);
    setResults([null, null]);

    try {
      const [resA, resB] = await Promise.all([
        fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt, style: "default", force_generate: true }),
        }).then((r) => r.json()),
        fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: prompt }),
        }).then((r) => r.json()),
      ]);

      setResults([
        {
          model: "14B Generator",
          html: resA.text ?? resA.playground_id ?? "Generated playground",
          latency: resA.metadata?.latency_ms ?? 0,
          tokens: resA.metadata?.tokens ?? 0,
        },
        {
          model: "3B Router",
          html: resB.response ?? resB.playground_id ?? "Routed response",
          latency: resB.metadata?.latency_ms ?? 0,
          tokens: resB.metadata?.tokens ?? 0,
        },
      ]);
    } catch (err) {
      console.error("[ABComparison]", err);
    } finally {
      setLoading(false);
    }
  }, [prompt]);

  const selectWinner = useCallback(async (choice: "a" | "b") => {
    setWinner(choice);
    await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        playground_id: "ab-comparison",
        rating: "up",
        prompt,
        metadata: { winner: choice === "a" ? "14B" : "3B" },
      }),
    }).catch(() => {});
  }, [prompt]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm">A/B Model Comparison</CardTitle>
        <Button
          size="sm"
          variant="outline"
          onClick={runComparison}
          disabled={loading || !prompt.trim()}
        >
          {loading ? "Comparing..." : "Compare 14B vs 3B"}
        </Button>
      </CardHeader>
      <CardContent>
        {(results[0] || results[1]) && (
          <div className="grid gap-4 md:grid-cols-2">
            {results.map((result, i) => (
              <Card key={i} className={winner === (i === 0 ? "a" : "b") ? "border-green-500" : ""}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline">{result?.model ?? "Loading..."}</Badge>
                    {result && (
                      <span className="font-mono text-[10px] text-muted-foreground">
                        {result.latency}ms
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-32">
                    <pre className="whitespace-pre-wrap font-mono text-xs text-muted-foreground">
                      {result?.html ?? "Waiting..."}
                    </pre>
                  </ScrollArea>
                  {result && !winner && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="mt-2 w-full"
                      onClick={() => selectWinner(i === 0 ? "a" : "b")}
                    >
                      Pick as winner
                    </Button>
                  )}
                  {winner === (i === 0 ? "a" : "b") && (
                    <Badge className="mt-2 bg-green-500/20 text-green-400">Winner</Badge>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
        {!results[0] && !results[1] && (
          <p className="text-xs text-muted-foreground">
            Generate with both models side-by-side. Pick the better output to improve training data.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
