import type { Meta, StoryObj } from "@storybook/react";
import { ErrorStateWithRetry } from "./ErrorStateWithRetry";

const meta: Meta<typeof ErrorStateWithRetry> = {
  title: "Feedback/ErrorStateWithRetry",
  component: ErrorStateWithRetry,
  tags: ["autodocs"],
};
export default meta;
type Story = StoryObj<typeof ErrorStateWithRetry>;

export const Default: Story = {
  args: {
    message: "Não foi possível carregar os dados. Verifique sua conexão.",
    onRetry: () => alert("Retry!"),
  },
};

export const WithTimestamp: Story = {
  args: {
    message: "Falha ao conectar com o servidor.",
    timestamp: new Date().toISOString(),
    onRetry: () => {},
  },
};

export const Retrying: Story = {
  args: {
    message: "Erro de conexão.",
    retrying: true,
    onRetry: () => {},
  },
};

export const Compact: Story = {
  args: {
    message: "Erro ao carregar alertas.",
    compact: true,
    onRetry: () => {},
  },
};
