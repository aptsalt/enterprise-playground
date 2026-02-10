import { z } from "zod";

export const TrainingStatusSchema = z.object({
  status: z.string(),
  message: z.string().optional(),
  adapter_dir: z.string().optional(),
  global_step: z.number().optional(),
  epoch: z.number().optional(),
  loss: z.number().optional(),
}).passthrough();
export type TrainingStatus = z.infer<typeof TrainingStatusSchema>;

export const TrainingLogsSchema = z.object({
  loss_curve: z.array(z.object({
    step: z.number(),
    loss: z.number(),
  })).optional(),
  eval_losses: z.array(z.object({
    step: z.number(),
    loss: z.number(),
  })).optional(),
});
export type TrainingLogs = z.infer<typeof TrainingLogsSchema>;

export const DatasetAnalyticsSchema = z.object({
  train_count: z.number().optional(),
  val_count: z.number().optional(),
  avg_instruction_len: z.number().optional(),
  avg_output_len: z.number().optional(),
  quality_distribution: z.record(z.string(), z.number()).optional(),
}).passthrough();
export type DatasetAnalytics = z.infer<typeof DatasetAnalyticsSchema>;

export const AdapterSchema = z.object({
  name: z.string(),
  status: z.string().optional(),
  size_mb: z.number().optional(),
  lora_rank: z.number().optional(),
  checkpoint_count: z.number().optional(),
  base_model: z.string().optional(),
  modified: z.string().optional(),
  target_modules: z.array(z.string()).optional(),
}).passthrough();
export type Adapter = z.infer<typeof AdapterSchema>;

export const AdapterDetailSchema = AdapterSchema.extend({
  files: z.array(z.string()).optional(),
  file_count: z.number().optional(),
  deploy_command: z.string().optional(),
});
export type AdapterDetail = z.infer<typeof AdapterDetailSchema>;

export const TrainingExampleSchema = z.object({
  instruction: z.string(),
  output: z.string(),
  quality: z.number().optional(),
  source: z.string().optional(),
});
export type TrainingExample = z.infer<typeof TrainingExampleSchema>;

export const TrainingExamplesResponseSchema = z.object({
  examples: z.array(TrainingExampleSchema),
  total: z.number(),
});

export const DatasetPrepareResponseSchema = z.object({
  status: z.string(),
  total_examples: z.number().optional(),
  filtered: z.number().optional(),
  train_size: z.number().optional(),
  val_size: z.number().optional(),
  quality_distribution: z.record(z.string(), z.number()).optional(),
}).passthrough();
export type DatasetPrepareResponse = z.infer<typeof DatasetPrepareResponseSchema>;
