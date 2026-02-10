import type { Meta, StoryObj } from "@storybook/react";
import { PlaygroundCard } from "@/components/gallery/playground-card";

const meta: Meta<typeof PlaygroundCard> = {
  title: "Gallery/PlaygroundCard",
  component: PlaygroundCard,
  parameters: { layout: "centered" },
  decorators: [(Story) => <div className="w-72"><Story /></div>],
};

export default meta;
type Story = StoryObj<typeof PlaygroundCard>;

export const Default: Story = {
  args: {
    playground: {
      id: "pg-demo-001",
      prompt: "Create a TD banking account overview dashboard with balance cards",
      model: "qwen2.5-coder:14b",
      style: "banking",
      size: 4096,
      source: "generated",
      rag_chunks: 3,
      latency_ms: 2500,
      created: new Date().toISOString(),
      task_type: "playground",
    },
  },
};

export const CacheHit: Story = {
  args: {
    playground: {
      id: "pg-demo-002",
      prompt: "Mortgage calculator with amortization table",
      model: "qwen2.5-coder:14b",
      style: "default",
      size: 2048,
      source: "cache",
      rag_chunks: 0,
      latency_ms: 50,
      created: new Date(Date.now() - 3600_000).toISOString(),
      task_type: "playground",
    },
  },
};

export const WithRAG: Story = {
  args: {
    playground: {
      id: "pg-demo-003",
      prompt: "Credit card comparison with rewards breakdown",
      model: "qwen2.5-coder:14b",
      style: "dark",
      size: 6144,
      source: "generated",
      rag_chunks: 5,
      latency_ms: 3200,
      created: new Date(Date.now() - 86400_000).toISOString(),
      task_type: "playground",
    },
  },
};
