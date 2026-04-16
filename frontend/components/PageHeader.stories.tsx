import type { Meta, StoryObj } from "@storybook/react";
import { PageHeader } from "./PageHeader";

const meta: Meta<typeof PageHeader> = {
  title: "Navigation/PageHeader",
  component: PageHeader,
  tags: ["autodocs"],
  parameters: {
    nextjs: { appDirectory: true },
  },
};
export default meta;
type Story = StoryObj<typeof PageHeader>;

export const Default: Story = {
  args: { title: "Pipeline" },
};

export const WithControls: Story = {
  args: {
    title: "Buscar",
    extraControls: <button className="text-sm text-brand-blue">Filtros avançados</button>,
  },
};
