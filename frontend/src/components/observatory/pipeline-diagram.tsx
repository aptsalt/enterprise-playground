"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const MERMAID_CHART = `
graph LR
    A[Raw Data] --> B[Scrape & Parse]
    B --> C[Structure Workflows]
    C --> D[Embed in ChromaDB]
    D --> E[RAG Retrieval]
    E --> F[QLoRA Training]
    F --> G[LoRA Adapter]
    G --> H[Merge & Deploy]

    style A fill:#1e1b4b,stroke:#4f46e5
    style B fill:#1e1b4b,stroke:#f97316
    style C fill:#1e1b4b,stroke:#eab308
    style D fill:#1e1b4b,stroke:#06b6d4
    style E fill:#1e1b4b,stroke:#8b5cf6
    style F fill:#1e1b4b,stroke:#ef4444
    style G fill:#1e1b4b,stroke:#10b981
    style H fill:#1e1b4b,stroke:#3b82f6
`;

export function PipelineDiagram() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rendered, setRendered] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function renderMermaid() {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          themeVariables: {
            darkMode: true,
            background: "#0f1117",
            primaryColor: "#4f46e5",
            primaryTextColor: "#e2e8f0",
            lineColor: "#475569",
          },
        });

        if (containerRef.current && !cancelled) {
          const { svg } = await mermaid.render("pipeline-mermaid", MERMAID_CHART);
          containerRef.current.innerHTML = svg;
          setRendered(true);
        }
      } catch {
        if (containerRef.current && !cancelled) {
          containerRef.current.innerHTML = '<p class="text-sm text-muted-foreground">Failed to load diagram</p>';
        }
      }
    }
    renderMermaid();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">QLoRA Fine-Tuning Pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div ref={containerRef} className="flex justify-center overflow-x-auto py-4">
            {!rendered && <p className="text-sm text-muted-foreground">Loading diagram...</p>}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { label: "Base Model", value: "Qwen2.5-Coder-14B-Instruct", color: "text-indigo-400" },
          { label: "Quantization", value: "4-bit QLoRA (NF4)", color: "text-purple-400" },
          { label: "LoRA Config", value: "r=32, alpha=64", color: "text-cyan-400" },
        ].map((item) => (
          <Card key={item.label}>
            <CardContent className="p-3">
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className={`text-sm font-medium ${item.color}`}>{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
