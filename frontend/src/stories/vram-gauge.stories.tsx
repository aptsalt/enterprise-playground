import type { Meta, StoryObj } from "@storybook/react";
import { VramGauge } from "@/components/metrics/vram-gauge";

const meta: Meta<typeof VramGauge> = {
  title: "Metrics/VramGauge",
  component: VramGauge,
  parameters: { layout: "centered" },
  decorators: [(Story) => <div className="w-64"><Story /></div>],
};

export default meta;
type Story = StoryObj<typeof VramGauge>;

export const Normal: Story = {
  args: {
    vram: {
      total_mb: 16384,
      used_mb: 10752,
      free_mb: 5632,
      utilization_pct: 65.6,
      gpu_name: "NVIDIA RTX 4090",
    },
  },
};

export const HighUsage: Story = {
  args: {
    vram: {
      total_mb: 16384,
      used_mb: 14500,
      free_mb: 1884,
      utilization_pct: 88.5,
      gpu_name: "NVIDIA RTX 4090",
    },
  },
};

export const NoData: Story = {
  args: { vram: null },
};
