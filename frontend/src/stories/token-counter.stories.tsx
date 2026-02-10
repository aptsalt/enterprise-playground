import type { Meta, StoryObj } from "@storybook/react";
import { TokenCounter } from "@/components/ai/token-counter";
import { TooltipProvider } from "@/components/ui/tooltip";

const meta: Meta<typeof TokenCounter> = {
  title: "AI/TokenCounter",
  component: TokenCounter,
  parameters: { layout: "centered" },
  decorators: [(Story) => <TooltipProvider><Story /></TooltipProvider>],
};

export default meta;
type Story = StoryObj<typeof TokenCounter>;

export const Short: Story = {
  args: {
    count: 5,
    tokens: ["Create", " a", " banking", " dash", "board"],
  },
};

export const Long: Story = {
  args: {
    count: 42,
    tokens: Array.from({ length: 42 }, (_, i) => `token${i}`),
  },
};
