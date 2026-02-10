"use client";

import { StatsRow } from "@/components/generate/stats-row";
import { PromptInput } from "@/components/generate/prompt-input";
import { StreamPanel } from "@/components/generate/stream-panel";
import { RecentTable } from "@/components/generate/recent-table";
import { ABComparison } from "@/components/ai/ab-comparison";
import { useSSEGenerate } from "@/lib/hooks/use-sse-generate";
import { useState } from "react";

export function GenerateTab() {
  const sse = useSSEGenerate();
  const [lastPrompt, setLastPrompt] = useState("");

  const handleGenerate: typeof sse.start = (req) => {
    setLastPrompt(req.prompt);
    sse.start(req);
  };

  return (
    <div className="space-y-4 p-4 lg:p-6">
      <StatsRow />
      <PromptInput onGenerate={handleGenerate} isStreaming={sse.state === "streaming"} />
      {sse.state !== "idle" && <StreamPanel sse={sse} />}
      {sse.state === "done" && <ABComparison prompt={lastPrompt} />}
      <RecentTable />
    </div>
  );
}
