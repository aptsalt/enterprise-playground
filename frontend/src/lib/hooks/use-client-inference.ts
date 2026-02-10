"use client";

import { useCallback, useRef, useState } from "react";

interface SentimentResult {
  label: string;
  score: number;
}

interface TokenInfo {
  count: number;
  tokens: string[];
}

type PipelineStatus = "idle" | "loading" | "ready" | "error";

/**
 * Hook for client-side ML inference using Transformers.js.
 * Runs entirely in-browser via WebAssembly/WebGPU - zero server calls.
 */
export function useClientInference() {
  const [status, setStatus] = useState<PipelineStatus>("idle");
  const [sentiment, setSentiment] = useState<SentimentResult | null>(null);
  const [tokenInfo, setTokenInfo] = useState<TokenInfo>({ count: 0, tokens: [] });
  const classifierRef = useRef<unknown>(null);
  const tokenizerRef = useRef<unknown>(null);
  const loadingRef = useRef(false);

  const loadModels = useCallback(async () => {
    if (loadingRef.current || classifierRef.current) return;
    loadingRef.current = true;
    setStatus("loading");

    try {
      const { pipeline, AutoTokenizer } = await import("@huggingface/transformers");

      const [classifier, tokenizer] = await Promise.all([
        pipeline("sentiment-analysis", "Xenova/distilbert-base-uncased-finetuned-sst-2-english", {
          dtype: "q8",
        }),
        AutoTokenizer.from_pretrained("Xenova/gpt2"),
      ]);

      classifierRef.current = classifier;
      tokenizerRef.current = tokenizer;
      setStatus("ready");
    } catch (err) {
      console.error("[ClientInference] Failed to load models:", err);
      setStatus("error");
    } finally {
      loadingRef.current = false;
    }
  }, []);

  const analyzeSentiment = useCallback(async (text: string) => {
    if (!classifierRef.current || !text.trim()) {
      setSentiment(null);
      return;
    }

    try {
      const classifier = classifierRef.current as (text: string) => Promise<SentimentResult[]>;
      const results = await classifier(text);
      if (results.length > 0) {
        setSentiment(results[0]);
      }
    } catch {
      setSentiment(null);
    }
  }, []);

  const countTokens = useCallback(async (text: string) => {
    if (!tokenizerRef.current || !text) {
      setTokenInfo({ count: 0, tokens: [] });
      return;
    }

    try {
      const tokenizer = tokenizerRef.current as {
        encode: (text: string) => { input_ids: { data: bigint[] } };
        decode: (ids: bigint[], options?: { skip_special_tokens: boolean }) => string;
      };
      const encoded = tokenizer.encode(text);
      const ids = Array.from(encoded.input_ids.data);
      const tokens = ids.map((id) => tokenizer.decode([id], { skip_special_tokens: false }));
      setTokenInfo({ count: ids.length, tokens });
    } catch {
      setTokenInfo({ count: 0, tokens: [] });
    }
  }, []);

  return {
    status,
    sentiment,
    tokenInfo,
    loadModels,
    analyzeSentiment,
    countTokens,
  } as const;
}
