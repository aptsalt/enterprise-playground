"use client";

import { useCallback, useRef, useState } from "react";
import { StreamEventSchema, type StreamEvent, type GenerateRequest } from "@/lib/schemas/generate";

type SSEState = "idle" | "streaming" | "done" | "error";

interface SSEResult {
  state: SSEState;
  chunks: string[];
  html: string;
  ragChunks: number;
  ragPreview: string[];
  playgroundId: string | null;
  error: string | null;
  start: (req: GenerateRequest) => void;
  reset: () => void;
}

export function useSSEGenerate(): SSEResult {
  const [state, setState] = useState<SSEState>("idle");
  const [chunks, setChunks] = useState<string[]>([]);
  const [html, setHtml] = useState("");
  const [ragChunks, setRagChunks] = useState(0);
  const [ragPreview, setRagPreview] = useState<string[]>([]);
  const [playgroundId, setPlaygroundId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState("idle");
    setChunks([]);
    setHtml("");
    setRagChunks(0);
    setRagPreview([]);
    setPlaygroundId(null);
    setError(null);
  }, []);

  const start = useCallback(async (req: GenerateRequest) => {
    reset();
    const controller = new AbortController();
    abortRef.current = controller;
    setState("streaming");

    try {
      const res = await fetch("/api/generate/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        setState("error");
        setError(`HTTP ${res.status}`);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw || raw === "[DONE]") continue;

          try {
            const parsed = JSON.parse(raw);
            const event: StreamEvent = StreamEventSchema.parse(parsed);

            switch (event.type) {
              case "chunk":
                accumulated += event.content;
                setChunks((c) => [...c, event.content]);
                setHtml(accumulated);
                break;
              case "rag":
                setRagChunks(event.chunks);
                if (event.preview) setRagPreview(event.preview);
                break;
              case "cache_hit":
                setPlaygroundId(event.playground_id);
                if (event.text) {
                  accumulated = event.text;
                  setHtml(event.text);
                }
                setState("done");
                return;
              case "done":
                setPlaygroundId(event.playground_id);
                setState("done");
                return;
              case "error":
                setState("error");
                setError(event.message);
                return;
            }
          } catch {
            // Skip unparseable lines
          }
        }
      }

      if (state === "streaming") setState("done");
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setState("error");
        setError((err as Error).message);
      }
    }
  }, [reset]);

  return { state, chunks, html, ragChunks, ragPreview, playgroundId, error, start, reset };
}
