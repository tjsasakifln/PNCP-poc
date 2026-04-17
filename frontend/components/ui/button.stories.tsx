import React from "react";
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

// ---------- From Button.examples.tsx (previously Button.examples.tsx — DEBT-006) ----------

export const WithIconAdd: Story = {
  name: "With Icon — Add (text + icon)",
  render: () => (
    <Button>
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
      Adicionar
    </Button>
  ),
};

export const WithIconDelete: Story = {
  name: "With Icon — Delete (destructive)",
  render: () => (
    <Button variant="destructive">
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
      Excluir
    </Button>
  ),
};

export const WithIconDownload: Story = {
  name: "With Icon — Download (outline)",
  render: () => (
    <Button variant="outline">
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      Exportar
    </Button>
  ),
};

export const LoadingSecondary: Story = {
  name: "Loading — Secondary",
  args: { children: "Carregando...", variant: "secondary", loading: true },
};

export const LoadingDestructive: Story = {
  name: "Loading — Destructive",
  args: { children: "Excluindo...", variant: "destructive", loading: true },
};

export const DisabledSecondary: Story = {
  name: "Disabled — Secondary",
  args: { children: "Indisponível", variant: "secondary", disabled: true },
};

export const AllVariantsSm: Story = {
  name: "Full Matrix — All Variants (size sm)",
  render: () => (
    <div className="flex flex-wrap items-center gap-3">
      {(["primary", "secondary", "destructive", "ghost", "outline", "link"] as const).map(variant => (
        <Button key={variant} variant={variant} size="sm">{variant}</Button>
      ))}
    </div>
  ),
};

export const AllVariantsLg: Story = {
  name: "Full Matrix — All Variants (size lg)",
  render: () => (
    <div className="flex flex-wrap items-center gap-3">
      {(["primary", "secondary", "destructive", "ghost", "outline", "link"] as const).map(variant => (
        <Button key={variant} variant={variant} size="lg">{variant}</Button>
      ))}
    </div>
  ),
};
