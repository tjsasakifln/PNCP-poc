import type { Meta, StoryObj } from "@storybook/react";
import { Label } from "./Label";

const meta: Meta<typeof Label> = {
  title: "UI/Label",
  component: Label,
  tags: ["autodocs"],
};
export default meta;
type Story = StoryObj<typeof Label>;

export const Default: Story = { args: { children: "Email", htmlFor: "email" } };
export const Required: Story = { args: { children: "Senha", htmlFor: "password", required: true } };
