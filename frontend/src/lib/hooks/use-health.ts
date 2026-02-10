"use client";

import { useEffect } from "react";
import { useDashboardStore } from "@/lib/store/dashboard-store";
import { HealthSchema, StatsSchema } from "@/lib/schemas/system";

export function useHealth() {
  const setHealth = useDashboardStore((s) => s.setHealth);
  const setVram = useDashboardStore((s) => s.setVram);

  useEffect(() => {
    let active = true;

    async function poll() {
      try {
        const [healthRes, statsRes] = await Promise.all([
          fetch("/api/health"),
          fetch("/api/stats"),
        ]);
        if (!active) return;

        if (healthRes.ok) {
          const data = HealthSchema.parse(await healthRes.json());
          setHealth(data);
        }
        if (statsRes.ok) {
          const stats = StatsSchema.parse(await statsRes.json());
          if (stats.vram) setVram(stats.vram);
        }
      } catch {
        // Silent fail on poll
      }
    }

    poll();
    const id = setInterval(poll, 30_000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [setHealth, setVram]);
}
