import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FeatureInfoDialog } from "@/components/ui/feature-info-dialog";
import { formatMs } from "@/lib/utils/format";

interface Props {
  title: string;
  model: Record<string, unknown>;
  color: string;
  featureId?: string;
}

export function ModelCard({ title, model, color, featureId }: Props) {
  const rows = [
    { label: "Role", value: model.role ?? "-" },
    { label: "VRAM", value: model.vram_gb ? `${model.vram_gb} GB` : "-" },
    { label: "Context", value: model.ctx_size ? `${model.ctx_size}` : "-" },
    { label: "Max Tokens", value: model.max_tokens ?? "-" },
    { label: "Temperature", value: model.temperature ?? "-" },
    { label: "Generations", value: model.count ?? 0 },
    { label: "Avg Latency", value: typeof model.avg_latency_ms === "number" ? formatMs(model.avg_latency_ms) : "-" },
  ];

  const titleElement = (
    <CardTitle className={`text-sm ${color}`}>{title}</CardTitle>
  );

  return (
    <Card>
      <CardHeader className="pb-2">
        {featureId ? (
          <FeatureInfoDialog featureId={featureId}>
            {titleElement}
          </FeatureInfoDialog>
        ) : (
          titleElement
        )}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
          {rows.map((r) => (
            <div key={r.label} className="flex justify-between text-xs">
              <span className="text-muted-foreground">{r.label}</span>
              <span className="font-mono">{String(r.value)}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
