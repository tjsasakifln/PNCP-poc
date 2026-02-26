import { Metadata } from "next";

// GTM-COPY-006 AC5: Per-page metadata for /planos
export const metadata: Metadata = {
  title: "Investimento SmartLic Pro — Quanto Custa Filtrar com Inteligência",
  description:
    "SmartLic Pro a partir de R$ 297/mês. Avaliação de viabilidade, exportação Excel e pipeline de oportunidades. Sem contrato. 30 dias de acesso completo no Beta.",
  alternates: {
    canonical: "https://smartlic.tech/planos",
  },
};

export default function PlanosLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
