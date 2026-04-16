import type { Meta, StoryObj } from "@storybook/react";
import { EmptyState } from "./EmptyState";

const meta: Meta<typeof EmptyState> = {
  title: "Feedback/EmptyState",
  component: EmptyState,
  tags: ["autodocs"],
};
export default meta;
type Story = StoryObj<typeof EmptyState>;

export const Pipeline: Story = {
  args: {
    icon: <svg className="w-8 h-8 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>,
    title: "Nenhuma oportunidade no pipeline",
    description: "Adicione licitações ao pipeline a partir dos resultados de busca.",
    steps: ["Faça uma busca por setor", "Clique em 'Adicionar ao Pipeline'", "Acompanhe o progresso aqui"],
    ctaLabel: "Fazer primeira busca",
    ctaHref: "/buscar",
  },
};

export const History: Story = {
  args: {
    icon: <svg className="w-8 h-8 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
    title: "Sem histórico de buscas",
    description: "Suas buscas anteriores aparecerão aqui.",
    ctaLabel: "Buscar licitações",
    ctaHref: "/buscar",
  },
};
