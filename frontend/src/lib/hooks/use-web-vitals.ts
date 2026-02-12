"use client";

import { useEffect } from "react";

interface WebVitalMetric {
  name: string;
  value: number;
  rating: "good" | "needs-improvement" | "poor";
  id: string;
}

export function useWebVitals() {
  useEffect(() => {
    const reportVital = (metric: WebVitalMetric) => {
      if (typeof window !== "undefined" && window.performance) {
        performance.mark(`web-vital-${metric.name}`, {
          detail: { value: metric.value, rating: metric.rating },
        });
      }
      if (process.env.NODE_ENV === "development") {
        const color =
          metric.rating === "good"
            ? "\x1b[32m"
            : metric.rating === "needs-improvement"
              ? "\x1b[33m"
              : "\x1b[31m";
        console.log(
          `%c[WebVital] ${metric.name}: ${metric.value.toFixed(1)}ms (${metric.rating})`,
          `color: ${color === "\x1b[32m" ? "green" : color === "\x1b[33m" ? "orange" : "red"}`,
        );
      }
    };

    import("web-vitals").then(({ onCLS, onLCP, onFCP, onTTFB, onINP }) => {
      onCLS(reportVital);
      onLCP(reportVital);
      onFCP(reportVital);
      onTTFB(reportVital);
      onINP(reportVital);
    });
  }, []);
}
