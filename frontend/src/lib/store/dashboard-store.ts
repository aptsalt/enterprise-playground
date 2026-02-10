import { create } from "zustand";
import type { Health, VramInfo } from "@/lib/schemas/system";

export type TabId = "generate" | "gallery" | "pipeline" | "data-rag" | "metrics" | "observatory" | "agent";
export type ObsSubTab = "rag-chunking" | "training" | "adapters" | "pipeline-diagram" | "embeddings";

interface GalleryFilters {
  search: string;
  style: string;
  sort: string;
}

interface DashboardState {
  activeTab: TabId;
  obsSubTab: ObsSubTab;
  galleryFilters: GalleryFilters;
  isGenerating: boolean;
  health: Health | null;
  vram: VramInfo | null;

  setActiveTab: (tab: TabId) => void;
  setObsSubTab: (sub: ObsSubTab) => void;
  setGallerySearch: (search: string) => void;
  setGalleryStyle: (style: string) => void;
  setGallerySort: (sort: string) => void;
  setIsGenerating: (v: boolean) => void;
  setHealth: (h: Health) => void;
  setVram: (v: VramInfo) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  activeTab: "generate",
  obsSubTab: "rag-chunking",
  galleryFilters: { search: "", style: "all", sort: "newest" },
  isGenerating: false,
  health: null,
  vram: null,

  setActiveTab: (tab) => set({ activeTab: tab }),
  setObsSubTab: (sub) => set({ obsSubTab: sub }),
  setGallerySearch: (search) =>
    set((s) => ({ galleryFilters: { ...s.galleryFilters, search } })),
  setGalleryStyle: (style) =>
    set((s) => ({ galleryFilters: { ...s.galleryFilters, style } })),
  setGallerySort: (sort) =>
    set((s) => ({ galleryFilters: { ...s.galleryFilters, sort } })),
  setIsGenerating: (v) => set({ isGenerating: v }),
  setHealth: (h) => set({ health: h }),
  setVram: (v) => set({ vram: v }),
}));
