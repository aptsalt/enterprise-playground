import { z } from "zod";

export const GenerateRequestSchema = z.object({
  prompt: z.string().min(1),
  workflow_id: z.string().nullable().default(null),
  style: z.string().default("default"),
  force_generate: z.boolean().default(false),
});
export type GenerateRequest = z.infer<typeof GenerateRequestSchema>;

export const StreamEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("status"), message: z.string() }),
  z.object({ type: z.literal("chunk"), content: z.string() }),
  z.object({ type: z.literal("rag"), chunks: z.number(), preview: z.array(z.string()).optional() }),
  z.object({ type: z.literal("cache_hit"), playground_id: z.string(), text: z.string().optional(), size: z.number().optional(), metadata: z.record(z.string(), z.unknown()).optional() }),
  z.object({ type: z.literal("done"), playground_id: z.string(), size: z.number().optional() }),
  z.object({ type: z.literal("error"), message: z.string() }),
]);
export type StreamEvent = z.infer<typeof StreamEventSchema>;
