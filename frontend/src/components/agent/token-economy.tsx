import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils/format";

interface Economy {
  total_input: number;
  total_output: number;
  total_saved: number;
}

export function TokenEconomy({ economy }: { economy?: Economy | null }) {
  const input = economy?.total_input ?? 0;
  const output = economy?.total_output ?? 0;
  const saved = economy?.total_saved ?? 0;
  const total = input + output + saved || 1;
  const efficiency = ((saved / total) * 100).toFixed(1);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Token Economy</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <p className="text-[10px] text-muted-foreground">Input</p>
            <p className="text-lg font-bold text-indigo-400">{formatNumber(input)}</p>
          </div>
          <div>
            <p className="text-[10px] text-muted-foreground">Output</p>
            <p className="text-lg font-bold text-purple-400">{formatNumber(output)}</p>
          </div>
          <div>
            <p className="text-[10px] text-muted-foreground">Saved</p>
            <p className="text-lg font-bold text-green-400">{formatNumber(saved)}</p>
          </div>
        </div>
        <div>
          <div className="mb-1 flex justify-between text-xs">
            <span className="text-muted-foreground">Efficiency</span>
            <span>{efficiency}%</span>
          </div>
          <div className="h-2 rounded bg-muted">
            <div
              className="h-full rounded bg-green-500/60"
              style={{ width: `${Math.min(100, Number(efficiency))}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
