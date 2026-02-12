import { z } from "zod";

export const RagStatsSchema = z.object({
  collection: z.string().optional(),
  total_chunks: z.number().optional(),
  embed_model: z.string().optional(),
}).passthrough();
export type RagStats = z.infer<typeof RagStatsSchema>;

export const RagChunkSchema = z.object({
  id: z.string().optional(),
  content: z.string(),
  metadata: z.record(z.string(), z.unknown()).optional(),
  distance: z.number().optional(),
});
export type RagChunk = z.infer<typeof RagChunkSchema>;

export const RagQueryResultSchema = z.object({
  query: z.string(),
  chunks: z.array(RagChunkSchema),
  count: z.number(),
});
export type RagQueryResult = z.infer<typeof RagQueryResultSchema>;

export const ChunkAnalyticsSchema = z.object({
  total: z.number(),
  avg_size: z.number(),
  min_size: z.number(),
  max_size: z.number(),
  histogram: z.array(z.object({
    label: z.string().optional(),
    range: z.string().optional(),
    min: z.number().optional(),
    max: z.number().optional(),
    count: z.number(),
  })).optional(),
  sources: z.record(z.string(), z.number()).optional(),
  workflows: z.record(z.string(), z.number()).optional(),
}).passthrough();
export type ChunkAnalytics = z.infer<typeof ChunkAnalyticsSchema>;
