import { Card, CardContent } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils/format";

interface Props {
  label: string;
  color: string;
  description: string;
  count: number;
}

export function PhaseCard({ label, color, description, count }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className={`text-sm font-semibold ${color}`}>{label}</h3>
            <p className="mt-1 text-xs text-muted-foreground">{description}</p>
          </div>
          <span className="text-2xl font-bold">{formatNumber(count)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
