"use client";

import { useDashboardStore } from "@/lib/store/dashboard-store";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { cn } from "@/lib/utils";

export function TopNav() {
  const health = useDashboardStore((s) => s.health);
  const vram = useDashboardStore((s) => s.vram);

  const vramPct = vram?.utilization_pct ?? 0;
  const gpuName = vram?.gpu_name ?? "GPU";

  return (
    <header
      className="flex items-center justify-between border-b border-border bg-card px-4 py-2.5"
      role="banner"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary" aria-hidden="true">
          <span className="text-sm font-bold text-primary-foreground">EP</span>
        </div>
        <div>
          <h1 className="text-sm font-semibold leading-none">Enterprise Playground</h1>
          <p className="text-xs text-muted-foreground">Dual-Model AI Generator</p>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="hidden items-center gap-2 sm:flex" role="status" aria-label={`VRAM usage: ${vramPct.toFixed(0)}%`}>
          <span className="text-xs text-muted-foreground">{gpuName}</span>
          <div className="w-32">
            <Progress
              value={vramPct}
              className="h-2"
              aria-label={`VRAM: ${vramPct.toFixed(0)}%`}
            />
          </div>
          <span className="text-xs font-mono text-muted-foreground">
            {vramPct.toFixed(0)}%
          </span>
        </div>

        <div className="flex items-center gap-3" role="status" aria-label="Model status">
          <ModelDot label="14B" ready={health?.generator_ready} />
          <ModelDot label="3B" ready={health?.router_ready} />
          <Badge
            variant="outline"
            className={cn(
              "text-xs",
              health?.ollama_available
                ? "border-green-500/50 text-green-400"
                : "border-red-500/50 text-red-400",
            )}
          >
            {health?.ollama_available ? "Ollama" : "Offline"}
          </Badge>
        </div>

        <ThemeToggle />
      </div>
    </header>
  );
}

function ModelDot({ label, ready }: { label: string; ready?: boolean }) {
  return (
    <div className="flex items-center gap-1.5" aria-label={`${label} model: ${ready === undefined ? "checking" : ready ? "ready" : "offline"}`}>
      <div
        className={cn(
          "h-2 w-2 rounded-full",
          ready === undefined
            ? "bg-muted-foreground animate-pulse"
            : ready
              ? "bg-green-500"
              : "bg-red-500",
        )}
        aria-hidden="true"
      />
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  );
}
