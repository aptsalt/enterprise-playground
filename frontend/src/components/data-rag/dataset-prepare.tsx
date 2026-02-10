"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function DatasetPrepare() {
  const [minQuality, setMinQuality] = useState(3);
  const [preparing, setPreparing] = useState(false);
  const [result, setResult] = useState<{ train_size?: number; val_size?: number } | null>(null);

  const handlePrepare = async () => {
    setPreparing(true);
    try {
      const res = await fetch("/api/dataset/prepare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ min_quality: minQuality, split_ratio: 0.9 }),
      });
      const data = await res.json();
      setResult(data);
    } finally {
      setPreparing(false);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Prepare Dataset</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3">
          <label className="text-xs text-muted-foreground">Min Quality:</label>
          <input
            type="range"
            min={1}
            max={5}
            value={minQuality}
            onChange={(e) => setMinQuality(Number(e.target.value))}
            className="flex-1"
          />
          <Badge variant="outline">{minQuality}/5</Badge>
        </div>
        <Button size="sm" onClick={handlePrepare} disabled={preparing}>
          {preparing ? "Preparing..." : "Prepare Fine-Tuning Dataset"}
        </Button>
        {result && (
          <p className="text-xs text-muted-foreground">
            Train: {result.train_size ?? 0} / Val: {result.val_size ?? 0}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
