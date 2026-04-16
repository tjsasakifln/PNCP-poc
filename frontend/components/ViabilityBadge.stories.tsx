import type { Meta, StoryObj } from "@storybook/react";
import ViabilityBadge from "./ViabilityBadge";

const meta: Meta<typeof ViabilityBadge> = {
  title: "Data Display/ViabilityBadge",
  component: ViabilityBadge,
  tags: ["autodocs"],
  argTypes: {
    level: { control: "select", options: ["alta", "media", "baixa", null] },
  },
};
export default meta;
type Story = StoryObj<typeof ViabilityBadge>;

export const Alta: Story = {
  args: {
    level: "alta",
    score: 82,
    factors: {
      modalidade: 90, modalidade_label: "Pregão Eletrônico — ideal",
      timeline: 75, timeline_label: "12 dias — prazo confortável",
      value_fit: 85, value_fit_label: "R$ 500k — faixa adequada",
      geography: 80, geography_label: "SC — região de atuação",
    },
  },
};

export const Media: Story = {
  args: {
    level: "media",
    score: 55,
    factors: {
      modalidade: 60, modalidade_label: "Concorrência — competitiva",
      timeline: 40, timeline_label: "5 dias — prazo apertado",
      value_fit: 70, value_fit_label: "R$ 2M — valor alto",
      geography: 50, geography_label: "MG — fora da região principal",
    },
  },
};

export const Baixa: Story = {
  args: {
    level: "baixa",
    score: 28,
    factors: {
      modalidade: 30, modalidade_label: "Inexigibilidade — restritiva",
      timeline: 20, timeline_label: "2 dias — insuficiente",
      value_fit: 25, value_fit_label: "R$ 50k — abaixo do porte",
      geography: 35, geography_label: "AM — sem presença",
    },
  },
};

export const WithMissingValue: Story = {
  args: { level: "media", score: 45, valueSource: "missing" },
};

export const NoLevel: Story = { args: { level: null } };
