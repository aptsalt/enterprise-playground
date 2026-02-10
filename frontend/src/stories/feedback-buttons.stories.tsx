import type { Meta, StoryObj } from "@storybook/react";
import { FeedbackButtons } from "@/components/ai/feedback-buttons";

const meta: Meta<typeof FeedbackButtons> = {
  title: "AI/FeedbackButtons",
  component: FeedbackButtons,
  parameters: { layout: "centered" },
};

export default meta;
type Story = StoryObj<typeof FeedbackButtons>;

export const Default: Story = {
  args: {
    playgroundId: "pg-001",
    prompt: "Create a banking dashboard",
  },
};
