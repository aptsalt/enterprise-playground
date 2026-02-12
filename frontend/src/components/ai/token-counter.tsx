"use client";

import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Props {
  count: number;
  tokens: string[];
}

export function TokenCounter({ count, tokens }: Props) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge
          variant="secondary"
          className="cursor-help font-mono text-[10px] tabular-nums"
          aria-label={`${count} tokens`}
        >
          {count} tokens
        </Badge>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="max-w-xs">
        <p className="mb-1 text-xs font-medium">Token breakdown (GPT-2 tokenizer):</p>
        <div className="flex flex-wrap gap-0.5">
          {tokens.slice(0, 50).map((token, i) => (
            <span
              key={i}
              className={`rounded px-0.5 text-[10px] font-mono ${
                i % 2 === 0
                  ? "bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300"
                  : "bg-cyan-500/10 text-cyan-600 dark:bg-cyan-500/20 dark:text-cyan-300"
              }`}
            >
              {token.replace(/ /g, "\u00B7")}
            </span>
          ))}
          {tokens.length > 50 && (
            <span className="text-[10px] text-muted-foreground">
              +{tokens.length - 50} more
            </span>
          )}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
