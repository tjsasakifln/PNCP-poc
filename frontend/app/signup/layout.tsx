import { Metadata } from "next";

// GTM-COPY-006 AC5: Per-page metadata for /signup
export const metadata: Metadata = {
  title: "Comece a Filtrar Licitações por Viabilidade",
  description:
    "Crie sua conta SmartLic e descubra quais licitações valem seu tempo. 30 dias de acesso completo no Beta, sem cartão de crédito.",
  alternates: {
    canonical: "https://smartlic.tech/signup",
  },
};

export default function SignupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
