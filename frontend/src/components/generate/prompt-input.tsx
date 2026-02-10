"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { SentimentBadge } from "@/components/ai/sentiment-badge";
import { TokenCounter } from "@/components/ai/token-counter";
import { useClientInference } from "@/lib/hooks/use-client-inference";
import type { GenerateRequest } from "@/lib/schemas/generate";

const STYLES = ["default", "banking", "minimal", "dark"];

interface Props {
  onGenerate: (req: GenerateRequest) => void;
  isStreaming: boolean;
}

export function PromptInput({ onGenerate, isStreaming }: Props) {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState("default");
  const { status, sentiment, tokenInfo, loadModels, analyzeSentiment, countTokens } =
    useClientInference();

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const handleChange = useCallback(
    (value: string) => {
      setPrompt(value);
      if (status === "ready") {
        countTokens(value);
        if (value.length > 10) {
          analyzeSentiment(value);
        }
      }
    },
    [status, countTokens, analyzeSentiment],
  );

  const handleSubmit = () => {
    if (!prompt.trim() || isStreaming) return;
    onGenerate({ prompt: prompt.trim(), style, workflow_id: null, force_generate: false });
  };

  return (
    <Card className="p-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Input
            placeholder="Describe the playground you want to generate..."
            value={prompt}
            onChange={(e) => handleChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            className="flex-1 pr-24"
            data-testid="prompt-input"
            aria-label="Generation prompt"
          />
          <div className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1">
            {status === "loading" && (
              <Badge variant="secondary" className="text-[10px] animate-pulse">
                Loading AI...
              </Badge>
            )}
            {status === "ready" && tokenInfo.count > 0 && (
              <TokenCounter count={tokenInfo.count} tokens={tokenInfo.tokens} />
            )}
            {status === "ready" && sentiment && (
              <SentimentBadge label={sentiment.label} score={sentiment.score} />
            )}
          </div>
        </div>
        <Select value={style} onValueChange={setStyle}>
          <SelectTrigger className="w-36" aria-label="Generation style">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STYLES.map((s) => (
              <SelectItem key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          onClick={handleSubmit}
          disabled={!prompt.trim() || isStreaming}
          className="min-w-[100px]"
        >
          {isStreaming ? "Generating..." : "Generate"}
        </Button>
      </div>
    </Card>
  );
}
