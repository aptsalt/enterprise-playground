"use client";

import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Props {
  confidence: number;
  routerMethod: string;
  model: string;
}

export function ConfidenceIndicator({ confidence, routerMethod, model }: Props) {
  const pct = Math.round(confidence * 100);
  const rating = pct >= 80 ? "high" : pct >= 50 ? "medium" : "low";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className="flex items-center gap-1.5 cursor-help"
          role="meter"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Router confidence: ${pct}%`}
        >
          <div className="h-1.5 w-12 rounded-full bg-muted overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                rating === "high" && "bg-green-500",
                rating === "medium" && "bg-yellow-500",
                rating === "low" && "bg-red-500",
              )}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-[10px] font-mono text-muted-foreground">
            {pct}%
          </span>
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        <div className="space-y-1 text-xs">
          <p>
            <span className="text-muted-foreground">Router:</span>{" "}
            {routerMethod === "keyword" ? "Keyword match (0 tokens)" : "LLM 3B (~50 tokens)"}
          </p>
          <p>
            <span className="text-muted-foreground">Model:</span>{" "}
            {model === "14b" ? "Generator 14B (code)" : "Router 3B (text)"}
          </p>
          <p>
            <span className="text-muted-foreground">Confidence:</span>{" "}
            {rating === "high" ? "High" : rating === "medium" ? "Medium" : "Low"} ({pct}%)
          </p>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
