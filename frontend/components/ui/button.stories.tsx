import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./button";

const meta: Meta<typeof Button> = {
  title: "UI/Button",
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["primary", "secondary", "destructive", "ghost", "link", "outline"],
    },
    size: { control: "select", options: ["sm", "default", "lg"] },
    loading: { control: "boolean" },
    disabled: { control: "boolean" },
  },
};
export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = { args: { children: "Buscar Licitações", variant: "primary" } };
export const Secondary: Story = { args: { children: "Cancelar", variant: "secondary" } };
export const Destructive: Story = { args: { children: "Excluir", variant: "destructive" } };
export const Ghost: Story = { args: { children: "Voltar", variant: "ghost" } };
export const Link: Story = { args: { children: "Saiba mais", variant: "link" } };
export const Outline: Story = { args: { children: "Exportar", variant: "outline" } };
export const Small: Story = { args: { children: "Filtrar", variant: "primary", size: "sm" } };
export const Large: Story = { args: { children: "Assinar SmartLic Pro", variant: "primary", size: "lg" } };
export const Loading: Story = { args: { children: "Processando...", variant: "primary", loading: true } };
export const Disabled: Story = { args: { children: "Indisponível", variant: "primary", disabled: true } };
export const IconButton: Story = {
  args: {
    size: "icon" as const,
    "aria-label": "Fechar",
    variant: "ghost",
    children: "✕",
  },
};
