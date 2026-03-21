import { Metadata } from "next";
import { ErrorBoundary } from "../../components/ErrorBoundary";

// GTM-COPY-006 AC5: Per-page metadata for /signup
export const metadata: Metadata = {
  title: "Comece a Filtrar Licitações por Viabilidade",
  description:
    "Crie sua conta SmartLic e descubra quais licitações valem seu tempo. 14 dias de acesso completo, sem cartão de crédito.",
  alternates: {
    canonical: "https://smartlic.tech/signup",
  },
};

/** DEBT-FE-007: ErrorBoundary wrapping for signup page */
export default function SignupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ErrorBoundary pageName="signup">{children}</ErrorBoundary>;
}
