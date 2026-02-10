import type { Meta, StoryObj } from "@storybook/react";
import { ConfidenceIndicator } from "@/components/ai/confidence-indicator";
import { TooltipProvider } from "@/components/ui/tooltip";

const meta: Meta<typeof ConfidenceIndicator> = {
  title: "AI/ConfidenceIndicator",
  component: ConfidenceIndicator,
  parameters: { layout: "centered" },
  decorators: [(Story) => <TooltipProvider><Story /></TooltipProvider>],
};

export default meta;
type Story = StoryObj<typeof ConfidenceIndicator>;

export const HighConfidence: Story = {
  args: { confidence: 0.95, routerMethod: "keyword", model: "14b" },
};

export const MediumConfidence: Story = {
  args: { confidence: 0.65, routerMethod: "llm_3b", model: "14b" },
};

export const LowConfidence: Story = {
  args: { confidence: 0.3, routerMethod: "llm_3b", model: "3b" },
};
