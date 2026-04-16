import type { Meta, StoryObj } from "@storybook/react";
import { Pagination } from "./Pagination";

const meta: Meta<typeof Pagination> = {
  title: "UI/Pagination",
  component: Pagination,
  tags: ["autodocs"],
};
export default meta;
type Story = StoryObj<typeof Pagination>;

export const Default: Story = {
  args: {
    totalItems: 100,
    currentPage: 1,
    pageSize: 20,
    onPageChange: () => {},
    onPageSizeChange: () => {},
  },
};

export const MiddlePage: Story = {
  args: { ...Default.args, currentPage: 3 },
};

export const SmallDataset: Story = {
  args: { ...Default.args, totalItems: 8, pageSize: 10 },
};

export const FiftyPerPage: Story = {
  args: { ...Default.args, pageSize: 50, totalItems: 200 },
};
