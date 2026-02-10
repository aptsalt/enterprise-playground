"use client";

import { useApiQuery } from "@/lib/hooks/use-api-query";
import { AdapterSchema } from "@/lib/schemas/observatory";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { z } from "zod";

export function AdapterPanel() {
  const { data: adapters } = useApiQuery(
    ["adapters"],
    "/api/observatory/adapters",
    z.array(AdapterSchema),
  );

  if (!adapters || adapters.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          No adapters found. Train a LoRA adapter first.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {adapters.map((adapter) => (
        <AdapterCard key={adapter.name} adapter={adapter} />
      ))}
    </div>
  );
}

function AdapterCard({ adapter }: { adapter: z.infer<typeof AdapterSchema> }) {
  const statusColor = adapter.status === "ready"
    ? "text-green-400 border-green-500/50"
    : adapter.status === "training"
      ? "text-yellow-400 border-yellow-500/50"
      : "text-muted-foreground";

  const handleDeploy = async () => {
    const res = await fetch(`/api/observatory/adapters/${adapter.name}/deploy`, { method: "POST" });
    const data = await res.json();
    if (data.command) {
      navigator.clipboard.writeText(data.command).catch(() => {});
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          {adapter.name}
          <Badge variant="outline" className={statusColor}>
            {adapter.status ?? "unknown"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
          <span className="text-muted-foreground">Size</span>
          <span className="font-mono">{adapter.size_mb?.toFixed(1) ?? "-"} MB</span>
          <span className="text-muted-foreground">LoRA Rank</span>
          <span className="font-mono">{adapter.lora_rank ?? "-"}</span>
          <span className="text-muted-foreground">Checkpoints</span>
          <span className="font-mono">{adapter.checkpoint_count ?? 0}</span>
          <span className="text-muted-foreground">Base Model</span>
          <span className="font-mono text-[10px]">{adapter.base_model ?? "-"}</span>
        </div>
        {adapter.target_modules && (
          <div className="flex flex-wrap gap-1">
            {adapter.target_modules.map((m) => (
              <Badge key={m} variant="secondary" className="text-[10px]">{m}</Badge>
            ))}
          </div>
        )}
        <Button size="sm" className="w-full" onClick={handleDeploy}>
          Deploy
        </Button>
      </CardContent>
    </Card>
  );
}
