import { describe, it, expect } from "vitest";
import { TraceSchema, AgentStatsSchema } from "@/lib/schemas/agent";

describe("TraceSchema", () => {
  it("parses trace with steps", () => {
    const result = TraceSchema.parse({
      id: "trace-001",
      started_at: "2025-01-15T10:30:00",
      prompt: "create banking dashboard",
      task_type: "playground",
      router_method: "keyword",
      final_model: "14b",
      cache_hit: false,
      rag_chunks: 3,
      total_steps: 5,
      total_latency_ms: 2500,
      steps: [
        { step_order: 1, step_name: "route", latency_ms: 50, metadata: { method: "keyword" } },
        { step_order: 2, step_name: "cache_check", latency_ms: 10 },
        { step_order: 3, step_name: "rag_query", latency_ms: 200 },
        { step_order: 4, step_name: "generate", latency_ms: 2200 },
        { step_order: 5, step_name: "cache_store", latency_ms: 40 },
      ],
    });
    expect(result.steps).toHaveLength(5);
    expect(result.steps![0].step_name).toBe("route");
  });

  it("parses trace without optional fields", () => {
    const result = TraceSchema.parse({
      id: "trace-002",
      started_at: "2025-01-15T10:31:00",
      prompt: "test",
    });
    expect(result.steps).toBeUndefined();
    expect(result.cache_hit).toBeUndefined();
  });
});

describe("AgentStatsSchema", () => {
  it("parses full stats", () => {
    const result = AgentStatsSchema.parse({
      total_traces: 42,
      avg_latency_ms: 1500,
      cache_hit_rate: "35%",
      avg_confidence: 0.87,
      last_24h_traces: 10,
      token_economy: { total_input: 5000, total_output: 3000, total_saved: 2000 },
      model_distribution: { "14b": 30, "3b": 7, cache: 5 },
      router_methods: { keyword: 25, llm_3b: 12, forced: 5 },
      step_avg_latencies: {
        route: { avg_ms: 45, count: 42 },
        generate: { avg_ms: 2100, count: 37 },
      },
    });
    expect(result.total_traces).toBe(42);
    expect(result.model_distribution?.["14b"]).toBe(30);
    expect(result.token_economy?.total_saved).toBe(2000);
  });

  it("handles empty distributions", () => {
    const result = AgentStatsSchema.parse({
      total_traces: 0,
      avg_latency_ms: 0,
      cache_hit_rate: "0%",
      avg_confidence: 0,
      last_24h_traces: 0,
    });
    expect(result.model_distribution).toBeUndefined();
    expect(result.router_methods).toBeUndefined();
  });
});
