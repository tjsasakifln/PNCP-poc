import { Metadata } from "next";
import { ErrorBoundary } from "../../components/ErrorBoundary";

// GTM-COPY-006 AC5: Per-page metadata for /planos
export const metadata: Metadata = {
  title: "Investimento SmartLic Pro — Quanto Custa Filtrar com Inteligência",
  description:
    "SmartLic Pro a partir de R$ 297/mês. Avaliação de viabilidade, exportação Excel e pipeline de oportunidades. Sem contrato. 14 dias de acesso completo.",
  alternates: {
    canonical: "https://smartlic.tech/planos",
  },
};

/** DEBT-FE-007: ErrorBoundary wrapping for planos page */
export default function PlanosLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ErrorBoundary pageName="planos">{children}</ErrorBoundary>;
}
