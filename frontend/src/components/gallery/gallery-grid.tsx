"use client";

import { useMemo } from "react";
import { useDashboardStore } from "@/lib/store/dashboard-store";
import { PlaygroundCard } from "@/components/gallery/playground-card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Playground } from "@/lib/schemas/playground";

interface Props {
  playgrounds: Playground[];
  isLoading: boolean;
}

export function GalleryGrid({ playgrounds, isLoading }: Props) {
  const filters = useDashboardStore((s) => s.galleryFilters);

  const filtered = useMemo(() => {
    let result = [...playgrounds];

    if (filters.search) {
      const q = filters.search.toLowerCase();
      result = result.filter((p) => p.prompt.toLowerCase().includes(q));
    }

    if (filters.style !== "all") {
      result = result.filter((p) => p.style === filters.style);
    }

    switch (filters.sort) {
      case "oldest":
        result.reverse();
        break;
      case "largest":
        result.sort((a, b) => (b.size ?? 0) - (a.size ?? 0));
        break;
      case "smallest":
        result.sort((a, b) => (a.size ?? 0) - (b.size ?? 0));
        break;
    }

    return result.slice(0, 50);
  }, [playgrounds, filters]);

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-64" />
        ))}
      </div>
    );
  }

  if (filtered.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground">
        No playgrounds match your filters.
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" data-testid="gallery-grid">
      {filtered.map((pg) => (
        <PlaygroundCard key={pg.id} playground={pg} />
      ))}
    </div>
  );
}
