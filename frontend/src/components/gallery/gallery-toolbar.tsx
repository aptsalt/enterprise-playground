"use client";

import { useDashboardStore } from "@/lib/store/dashboard-store";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

const STYLES = ["all", "default", "banking", "minimal", "dark"];
const SORTS = [
  { value: "newest", label: "Newest" },
  { value: "oldest", label: "Oldest" },
  { value: "largest", label: "Largest" },
  { value: "smallest", label: "Smallest" },
];

export function GalleryToolbar({ total }: { total: number }) {
  const filters = useDashboardStore((s) => s.galleryFilters);
  const setSearch = useDashboardStore((s) => s.setGallerySearch);
  const setStyle = useDashboardStore((s) => s.setGalleryStyle);
  const setSort = useDashboardStore((s) => s.setGallerySort);

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Input
        placeholder="Search playgrounds..."
        value={filters.search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-64"
        data-testid="gallery-search"
      />
      <Select value={filters.style} onValueChange={setStyle}>
        <SelectTrigger className="w-32">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {STYLES.map((s) => (
            <SelectItem key={s} value={s}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={filters.sort} onValueChange={setSort}>
        <SelectTrigger className="w-32">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {SORTS.map((s) => (
            <SelectItem key={s.value} value={s.value}>
              {s.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Badge variant="secondary">{total} playgrounds</Badge>
    </div>
  );
}
