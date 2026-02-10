import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Point {
  step: number;
  loss: number;
}

interface Props {
  trainLoss: Point[];
  evalLoss: Point[];
}

export function LossChart({ trainLoss, evalLoss }: Props) {
  if (trainLoss.length === 0 && evalLoss.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Loss Curve</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="py-8 text-center text-xs text-muted-foreground">No training data yet</p>
        </CardContent>
      </Card>
    );
  }

  const allPoints = [...trainLoss, ...evalLoss];
  const maxStep = Math.max(...allPoints.map((p) => p.step), 1);
  const maxLoss = Math.max(...allPoints.map((p) => p.loss), 0.1);
  const width = 500;
  const height = 200;
  const pad = 40;

  const toX = (step: number) => pad + ((step / maxStep) * (width - pad * 2));
  const toY = (loss: number) => height - pad - ((loss / maxLoss) * (height - pad * 2));

  const toPath = (points: Point[]) =>
    points.map((p, i) => `${i === 0 ? "M" : "L"} ${toX(p.step)} ${toY(p.loss)}`).join(" ");

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Loss Curve</CardTitle>
      </CardHeader>
      <CardContent>
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full" preserveAspectRatio="xMidYMid meet">
          {/* Grid lines */}
          {[0.25, 0.5, 0.75, 1].map((frac) => (
            <line
              key={frac}
              x1={pad}
              y1={toY(maxLoss * frac)}
              x2={width - pad}
              y2={toY(maxLoss * frac)}
              stroke="currentColor"
              className="text-border"
              strokeDasharray="4"
            />
          ))}
          {/* Train loss */}
          {trainLoss.length > 1 && (
            <path d={toPath(trainLoss)} fill="none" stroke="#4f46e5" strokeWidth="2" />
          )}
          {/* Eval loss */}
          {evalLoss.length > 1 && (
            <path d={toPath(evalLoss)} fill="none" stroke="#f59e0b" strokeWidth="2" strokeDasharray="6" />
          )}
          {/* Legend */}
          <circle cx={pad} cy={12} r={4} fill="#4f46e5" />
          <text x={pad + 10} y={16} className="fill-muted-foreground text-[10px]">Train</text>
          <circle cx={pad + 60} cy={12} r={4} fill="#f59e0b" />
          <text x={pad + 70} y={16} className="fill-muted-foreground text-[10px]">Eval</text>
        </svg>
      </CardContent>
    </Card>
  );
}
