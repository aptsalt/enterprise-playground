import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { VramInfo } from "@/lib/schemas/system";

export function VramGauge({ vram }: { vram?: VramInfo | null }) {
  const pct = vram?.utilization_pct ?? 0;
  const used = vram?.used_mb ?? 0;
  const total = vram?.total_mb ?? 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">VRAM Usage</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-3">
        <div
          className="relative flex h-32 w-32 items-center justify-center rounded-full"
          style={{
            background: `conic-gradient(oklch(0.55 0.16 45) ${pct * 3.6}deg, oklch(0.91 0.006 75) ${pct * 3.6}deg)`,
          }}
        >
          <div className="flex h-24 w-24 flex-col items-center justify-center rounded-full bg-card">
            <span className="text-xl font-bold">{pct.toFixed(0)}%</span>
            <span className="text-[10px] text-muted-foreground">VRAM</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <span className="text-muted-foreground">GPU</span>
          <span className="font-mono">{vram?.gpu_name ?? "-"}</span>
          <span className="text-muted-foreground">Used</span>
          <span className="font-mono">{(used / 1024).toFixed(1)} GB</span>
          <span className="text-muted-foreground">Total</span>
          <span className="font-mono">{(total / 1024).toFixed(1)} GB</span>
        </div>
      </CardContent>
    </Card>
  );
}
