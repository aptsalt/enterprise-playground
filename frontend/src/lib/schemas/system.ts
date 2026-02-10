import { z } from "zod";

export const HealthSchema = z.object({
  status: z.string(),
  ollama_available: z.boolean(),
  generator_model: z.string(),
  router_model: z.string(),
  models_loaded: z.array(z.string()),
  generator_ready: z.boolean(),
  router_ready: z.boolean(),
});
export type Health = z.infer<typeof HealthSchema>;

export const VramSchema = z.object({
  total_mb: z.number().optional(),
  used_mb: z.number().optional(),
  free_mb: z.number().optional(),
  utilization_pct: z.number().optional(),
  gpu_name: z.string().optional(),
}).passthrough();
export type VramInfo = z.infer<typeof VramSchema>;

export const StatsSchema = z.object({
  vram: VramSchema.optional(),
  models: z.record(z.string(), z.unknown()).optional(),
  workflows_count: z.number().optional(),
  playgrounds_count: z.number().optional(),
  cache_entries: z.number().optional(),
}).passthrough();
export type Stats = z.infer<typeof StatsSchema>;

export const PipelinePhaseSchema = z.object({
  label: z.string().optional(),
  count: z.number(),
  description: z.string().optional(),
});

export const PipelineStatusSchema = z.object({
  phases: z.record(z.string(), PipelinePhaseSchema),
});
export type PipelineStatus = z.infer<typeof PipelineStatusSchema>;

export const ModelInfoSchema = z.object({
  name: z.string().optional(),
  role: z.string().optional(),
  parameters: z.string().optional(),
  vram_gb: z.number().optional(),
  ctx_size: z.number().optional(),
  max_tokens: z.number().optional(),
  temperature: z.number().optional(),
  count: z.number().optional(),
  avg_latency_ms: z.number().optional(),
}).passthrough();

export const MetricsSchema = z.object({
  models: z.record(z.string(), ModelInfoSchema).optional(),
  total_generations: z.number().optional(),
  cache_hit_rate: z.string().optional(),
  avg_latency_ms: z.number().optional(),
  rag_generations: z.number().optional(),
  vram: VramSchema.optional(),
  fine_tuning: z.record(z.string(), z.unknown()).optional(),
  recent_activity: z.array(z.record(z.string(), z.unknown())).optional(),
}).passthrough();
export type Metrics = z.infer<typeof MetricsSchema>;

export const DatasetStatsSchema = z.object({
  training_files: z.number(),
  total_examples: z.number(),
  data_dir: z.string().optional(),
});
export type DatasetStats = z.infer<typeof DatasetStatsSchema>;
