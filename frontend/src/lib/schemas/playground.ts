import { z } from "zod";

export const PlaygroundSchema = z.object({
  id: z.string(),
  prompt: z.string(),
  model: z.string().optional(),
  style: z.string().optional(),
  size: z.number().optional(),
  source: z.string().optional(),
  rag_chunks: z.number().optional(),
  latency_ms: z.number().optional(),
  created: z.string().optional(),
  task_type: z.string().optional(),
});
export type Playground = z.infer<typeof PlaygroundSchema>;

export const PlaygroundListSchema = z.array(PlaygroundSchema);

export const WorkflowSchema = z.object({
  workflow_id: z.string(),
  name: z.string(),
  category: z.string(),
  total_pages: z.number().optional(),
  url: z.string().optional(),
});
export type Workflow = z.infer<typeof WorkflowSchema>;

export const WorkflowListSchema = z.array(WorkflowSchema);
