import { Card, CardContent } from "@/components/ui/card";
import { FeatureInfoDialog } from "@/components/ui/feature-info-dialog";
import { getFeatureIdForPhase } from "@/lib/data/feature-info";
import { formatNumber } from "@/lib/utils/format";

interface Props {
  label: string;
  color: string;
  description: string;
  count: number;
  phaseKey?: string;
}

export function PhaseCard({ label, color, description, count, phaseKey }: Props) {
  const featureId = phaseKey ? getFeatureIdForPhase(phaseKey) : undefined;

  const heading = (
    <h3 className={`text-sm font-bold ${color}`}>{label}</h3>
  );

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div>
            {featureId ? (
              <FeatureInfoDialog featureId={featureId}>
                {heading}
              </FeatureInfoDialog>
            ) : (
              heading
            )}
            <p className="mt-1 text-xs text-muted-foreground">{description}</p>
          </div>
          <span className="text-2xl font-bold">{formatNumber(count)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
