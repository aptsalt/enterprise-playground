import { z } from "zod";

export const TraceStepSchema = z.object({
  step_order: z.number(),
  step_name: z.string(),
  latency_ms: z.number(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});
export type TraceStep = z.infer<typeof TraceStepSchema>;

export const TraceSchema = z.object({
  id: z.string(),
  started_at: z.string(),
  prompt: z.string(),
  task_type: z.string().optional(),
  router_method: z.string().optional(),
  final_model: z.string().optional(),
  cache_hit: z.boolean().optional(),
  rag_chunks: z.number().optional(),
  total_steps: z.number().optional(),
  total_latency_ms: z.number().optional(),
  steps: z.array(TraceStepSchema).optional(),
});
export type Trace = z.infer<typeof TraceSchema>;

export const AgentStatsSchema = z.object({
  enabled: z.boolean().optional(),
  total_traces: z.number(),
  avg_latency_ms: z.number(),
  cache_hit_rate: z.string(),
  avg_confidence: z.number(),
  token_economy: z.object({
    total_input: z.number(),
    total_output: z.number(),
    total_saved: z.number(),
  }).optional(),
  last_24h_traces: z.number(),
  model_distribution: z.record(z.string(), z.number()).optional(),
  router_methods: z.record(z.string(), z.number()).optional(),
  step_avg_latencies: z.record(z.string(), z.object({
    avg_ms: z.number(),
    count: z.number(),
  })).optional(),
});
export type AgentStats = z.infer<typeof AgentStatsSchema>;
