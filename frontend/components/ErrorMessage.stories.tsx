import type { Meta, StoryObj } from "@storybook/react";
import { ErrorMessage } from "./ErrorMessage";

const meta: Meta<typeof ErrorMessage> = {
  title: "Feedback/ErrorMessage",
  component: ErrorMessage,
  tags: ["autodocs"],
};
export default meta;
type Story = StoryObj<typeof ErrorMessage>;

export const Default: Story = {
  args: {
    title: "Erro inesperado",
    body: "Ocorreu um erro inesperado. Tente novamente.",
    telemetryKey: "error_default",
  },
};

export const NetworkError: Story = {
  args: {
    title: "Falha de conexão",
    body: "Falha de conexão com o servidor. Verifique sua internet.",
    telemetryKey: "error_network",
  },
};
