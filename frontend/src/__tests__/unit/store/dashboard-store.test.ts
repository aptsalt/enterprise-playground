import { describe, it, expect, beforeEach } from "vitest";
import { useDashboardStore } from "@/lib/store/dashboard-store";

describe("dashboardStore", () => {
  beforeEach(() => {
    useDashboardStore.setState({
      activeTab: "generate",
      obsSubTab: "rag-chunking",
      galleryFilters: { search: "", style: "all", sort: "newest" },
      isGenerating: false,
      health: null,
      vram: null,
    });
  });

  it("sets active tab", () => {
    useDashboardStore.getState().setActiveTab("gallery");
    expect(useDashboardStore.getState().activeTab).toBe("gallery");
  });

  it("sets observatory sub-tab", () => {
    useDashboardStore.getState().setObsSubTab("training");
    expect(useDashboardStore.getState().obsSubTab).toBe("training");
  });

  it("sets gallery search", () => {
    useDashboardStore.getState().setGallerySearch("banking");
    expect(useDashboardStore.getState().galleryFilters.search).toBe("banking");
    // Other filters remain unchanged
    expect(useDashboardStore.getState().galleryFilters.style).toBe("all");
    expect(useDashboardStore.getState().galleryFilters.sort).toBe("newest");
  });

  it("sets gallery style", () => {
    useDashboardStore.getState().setGalleryStyle("dark");
    expect(useDashboardStore.getState().galleryFilters.style).toBe("dark");
  });

  it("sets gallery sort", () => {
    useDashboardStore.getState().setGallerySort("largest");
    expect(useDashboardStore.getState().galleryFilters.sort).toBe("largest");
  });

  it("sets isGenerating", () => {
    useDashboardStore.getState().setIsGenerating(true);
    expect(useDashboardStore.getState().isGenerating).toBe(true);
  });

  it("sets health", () => {
    const health = {
      status: "ok",
      ollama_available: true,
      generator_model: "qwen2.5-coder:14b",
      router_model: "qwen2.5:3b",
      models_loaded: ["qwen2.5-coder:14b"],
      generator_ready: true,
      router_ready: false,
    };
    useDashboardStore.getState().setHealth(health);
    expect(useDashboardStore.getState().health?.generator_ready).toBe(true);
    expect(useDashboardStore.getState().health?.router_ready).toBe(false);
  });

  it("sets vram", () => {
    const vram = {
      total_mb: 16384,
      used_mb: 10752,
      free_mb: 5632,
      utilization_pct: 65.6,
      gpu_name: "RTX 4090",
    };
    useDashboardStore.getState().setVram(vram);
    expect(useDashboardStore.getState().vram?.utilization_pct).toBe(65.6);
  });
});
