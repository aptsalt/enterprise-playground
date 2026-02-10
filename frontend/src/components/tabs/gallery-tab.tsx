"use client";

import { GalleryToolbar } from "@/components/gallery/gallery-toolbar";
import { GalleryGrid } from "@/components/gallery/gallery-grid";
import { useApiQuery } from "@/lib/hooks/use-api-query";
import { PlaygroundListSchema } from "@/lib/schemas/playground";

export function GalleryTab() {
  const { data: playgrounds, isLoading } = useApiQuery(
    ["playgrounds"],
    "/api/playgrounds",
    PlaygroundListSchema,
    { refetchInterval: 30_000 },
  );

  return (
    <div className="space-y-4 p-4 lg:p-6">
      <GalleryToolbar total={playgrounds?.length ?? 0} />
      <GalleryGrid playgrounds={playgrounds ?? []} isLoading={isLoading} />
    </div>
  );
}
