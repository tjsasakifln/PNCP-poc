import type { Meta, StoryObj } from "@storybook/react";
import { Skeleton } from "./Skeleton";

const meta: Meta<typeof Skeleton> = {
  title: "Loading/Skeleton",
  component: Skeleton,
  tags: ["autodocs"],
  argTypes: {
    variant: { control: "select", options: ["text", "card", "list", "avatar", "block"] },
    count: { control: { type: "number", min: 1, max: 10 } },
  },
};
export default meta;
type Story = StoryObj<typeof Skeleton>;

export const Text: Story = { args: { variant: "text" } };
export const TextMultiple: Story = { args: { variant: "text", count: 4 } };
export const Card: Story = { args: { variant: "card" } };
export const List: Story = { args: { variant: "list", count: 5 } };
export const Avatar: Story = { args: { variant: "avatar" } };
export const Block: Story = {
  args: { variant: "block" },
  decorators: [(Story) => <div style={{ height: 200 }}><Story /></div>],
};
