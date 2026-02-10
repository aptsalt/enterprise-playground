import { describe, it, expect } from "vitest";
import { HealthSchema, PipelineStatusSchema, VramSchema } from "@/lib/schemas/system";

describe("HealthSchema", () => {
  it("parses valid health response", () => {
    const result = HealthSchema.parse({
      status: "ok",
      ollama_available: true,
      generator_model: "qwen2.5-coder:14b",
      router_model: "qwen2.5:3b",
      models_loaded: ["qwen2.5-coder:14b", "qwen2.5:3b"],
      generator_ready: true,
      router_ready: true,
    });
    expect(result.status).toBe("ok");
    expect(result.generator_ready).toBe(true);
    expect(result.models_loaded).toHaveLength(2);
  });

  it("requires all fields", () => {
    expect(() => HealthSchema.parse({ status: "ok" })).toThrow();
  });
});

describe("PipelineStatusSchema", () => {
  it("parses phases with counts", () => {
    const result = PipelineStatusSchema.parse({
      phases: {
        scrape: { count: 10, label: "Scrape" },
        map: { count: 8 },
        generate: { count: 25 },
      },
    });
    expect(result.phases.scrape.count).toBe(10);
    expect(result.phases.generate.count).toBe(25);
  });
});

describe("VramSchema", () => {
  it("handles full VRAM data", () => {
    const result = VramSchema.parse({
      total_mb: 16384,
      used_mb: 10752,
      free_mb: 5632,
      utilization_pct: 65.6,
      gpu_name: "NVIDIA RTX 4090",
    });
    expect(result.utilization_pct).toBe(65.6);
  });

  it("handles empty/partial VRAM data", () => {
    const result = VramSchema.parse({});
    expect(result.total_mb).toBeUndefined();
    expect(result.utilization_pct).toBeUndefined();
  });

  it("passes through extra fields", () => {
    const result = VramSchema.parse({ extra_field: "value" });
    expect(result).toHaveProperty("extra_field");
  });
});
