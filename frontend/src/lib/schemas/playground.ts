import { z } from "zod";

const RawPlaygroundSchema = z.object({
  playground_id: z.string().optional(),
  id: z.string().optional(),
  prompt: z.string(),
  model: z.string().optional(),
  style: z.string().optional(),
  html_size_bytes: z.number().optional(),
  size: z.number().optional(),
  source: z.string().optional(),
  cache_hit: z.boolean().optional(),
  routed_as: z.string().optional(),
  rag_chunks: z.number().optional(),
  had_workflow_context: z.boolean().optional(),
  latency_ms: z.number().optional(),
  generated_at: z.string().optional(),
  created: z.string().optional(),
  task_type: z.string().optional(),
  router_confidence: z.number().optional(),
  exists: z.boolean().optional(),
}).passthrough();

export const PlaygroundSchema = RawPlaygroundSchema.transform((raw) => ({
  id: raw.playground_id ?? raw.id ?? "",
  prompt: raw.prompt,
  model: raw.model,
  style: raw.style,
  size: raw.html_size_bytes ?? raw.size,
  source: raw.source ?? (raw.cache_hit ? "cache" : "gen"),
  rag_chunks: raw.rag_chunks ?? (raw.had_workflow_context ? 1 : undefined),
  latency_ms: raw.latency_ms,
  created: raw.generated_at ?? raw.created,
  task_type: raw.task_type ?? raw.routed_as,
}));
export type Playground = z.infer<typeof PlaygroundSchema>;

export const PlaygroundListSchema = z.array(RawPlaygroundSchema).transform((list) =>
  list.map((raw) => ({
    id: raw.playground_id ?? raw.id ?? "",
    prompt: raw.prompt,
    model: raw.model,
    style: raw.style,
    size: raw.html_size_bytes ?? raw.size,
    source: raw.source ?? (raw.cache_hit ? "cache" : "gen"),
    rag_chunks: raw.rag_chunks ?? (raw.had_workflow_context ? 1 : undefined),
    latency_ms: raw.latency_ms,
    created: raw.generated_at ?? raw.created,
    task_type: raw.task_type ?? raw.routed_as,
  })),
);

export const WorkflowSchema = z.object({
  workflow_id: z.string(),
  name: z.string(),
  category: z.string(),
  total_pages: z.number().optional(),
  url: z.string().optional(),
});
export type Workflow = z.infer<typeof WorkflowSchema>;

export const WorkflowListSchema = z.array(WorkflowSchema);
