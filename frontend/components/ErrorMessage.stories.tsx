import type { Meta, StoryObj } from "@storybook/react";
import ErrorMessage from "./ErrorMessage";

const meta: Meta<typeof ErrorMessage> = {
  title: "Feedback/ErrorMessage",
  component: ErrorMessage,
  tags: ["autodocs"],
};
export default meta;
type Story = StoryObj<typeof ErrorMessage>;

export const Default: Story = {
  args: { message: "Ocorreu um erro inesperado. Tente novamente." },
};

export const NetworkError: Story = {
  args: { message: "Falha de conexão com o servidor. Verifique sua internet." },
};
