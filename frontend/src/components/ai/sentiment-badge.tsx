"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Props {
  label: string;
  score: number;
}

export function SentimentBadge({ label, score }: Props) {
  const isPositive = label === "POSITIVE";
  const pct = Math.round(score * 100);

  return (
    <Badge
      variant="outline"
      className={cn(
        "text-[10px] font-mono gap-1",
        isPositive
          ? "border-green-500/50 text-green-600 dark:text-green-400"
          : "border-orange-500/50 text-orange-600 dark:text-orange-400",
      )}
      aria-label={`Sentiment: ${label.toLowerCase()}, confidence ${pct}%`}
    >
      {isPositive ? "+" : "-"} {pct}%
    </Badge>
  );
}
