"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface EmbeddingPoint {
  id: string;
  x: number;
  y: number;
  category: string;
  content: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  accounts: "#4f46e5",
  credit_cards: "#06b6d4",
  mortgages: "#10b981",
  loans: "#f59e0b",
  investing: "#8b5cf6",
  insurance: "#ef4444",
  default: "#6b7280",
};

export function EmbeddingVisualizer() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<EmbeddingPoint[]>([]);
  const [selected, setSelected] = useState<EmbeddingPoint | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchEmbeddings = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/observatory/embedding-coords");
      if (!res.ok) throw new Error("Failed to fetch embeddings");
      const data: EmbeddingPoint[] = await res.json();
      setPoints(data);
    } catch {
      // Generate demo data if backend endpoint not available
      const demo: EmbeddingPoint[] = [];
      const categories = Object.keys(CATEGORY_COLORS).filter((c) => c !== "default");
      for (let i = 0; i < 120; i++) {
        const cat = categories[i % categories.length];
        const cx = (categories.indexOf(cat) % 3) * 0.3 + 0.15;
        const cy = Math.floor(categories.indexOf(cat) / 3) * 0.4 + 0.2;
        demo.push({
          id: `chunk-${i}`,
          x: cx + (Math.random() - 0.5) * 0.2,
          y: cy + (Math.random() - 0.5) * 0.2,
          category: cat,
          content: `${cat} workflow chunk #${i}: Sample content about ${cat} banking services and features.`,
        });
      }
      setPoints(demo);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEmbeddings();
  }, [fetchEmbeddings]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || points.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, rect.width, rect.height);

    // Draw grid
    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
      const x = (rect.width * i) / 10;
      const y = (rect.height * i) / 10;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, rect.height);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(rect.width, y);
      ctx.stroke();
    }

    // Draw points
    for (const point of points) {
      const px = point.x * rect.width;
      const py = point.y * rect.height;
      const color = CATEGORY_COLORS[point.category] ?? CATEGORY_COLORS.default;
      const isSelected = selected?.id === point.id;

      ctx.beginPath();
      ctx.arc(px, py, isSelected ? 6 : 4, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? "#ffffff" : color;
      ctx.globalAlpha = isSelected ? 1 : 0.7;
      ctx.fill();

      if (isSelected) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
  }, [points, selected]);

  const handleCanvasClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      const mx = (e.clientX - rect.left) / rect.width;
      const my = (e.clientY - rect.top) / rect.height;

      let closest: EmbeddingPoint | null = null;
      let minDist = 0.03;

      for (const point of points) {
        const dist = Math.hypot(point.x - mx, point.y - my);
        if (dist < minDist) {
          minDist = dist;
          closest = point;
        }
      }
      setSelected(closest);
    },
    [points],
  );

  const categories = [...new Set(points.map((p) => p.category))];

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm">Embedding Space (t-SNE 2D)</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-[10px]">
              {points.length} chunks
            </Badge>
            <Button size="sm" variant="outline" onClick={fetchEmbeddings} disabled={loading}>
              {loading ? "Loading..." : "Refresh"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <canvas
            ref={canvasRef}
            onClick={handleCanvasClick}
            className="h-80 w-full cursor-crosshair rounded border border-border bg-background"
            role="img"
            aria-label={`Embedding visualization with ${points.length} data points across ${categories.length} categories`}
          />
          <div className="mt-3 flex flex-wrap gap-2" role="list" aria-label="Category legend">
            {categories.map((cat) => (
              <div key={cat} className="flex items-center gap-1" role="listitem">
                <div
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.default }}
                />
                <span className="text-[10px] text-muted-foreground capitalize">{cat.replace("_", " ")}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Chunk Details</CardTitle>
        </CardHeader>
        <CardContent>
          {selected ? (
            <div className="space-y-3">
              <Badge
                style={{
                  backgroundColor: `${CATEGORY_COLORS[selected.category] ?? CATEGORY_COLORS.default}33`,
                  color: CATEGORY_COLORS[selected.category] ?? CATEGORY_COLORS.default,
                }}
                className="text-[10px]"
              >
                {selected.category.replace("_", " ")}
              </Badge>
              <p className="font-mono text-[10px] text-muted-foreground">{selected.id}</p>
              <div className="text-xs">
                <p className="mb-1 text-muted-foreground">Position: ({selected.x.toFixed(3)}, {selected.y.toFixed(3)})</p>
              </div>
              <ScrollArea className="h-48">
                <p className="text-xs text-muted-foreground">{selected.content}</p>
              </ScrollArea>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">
              Click a point in the scatter plot to view chunk details. Colors represent workflow categories.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
