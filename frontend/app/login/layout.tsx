import { Metadata } from "next";
import { ErrorBoundary } from "../../components/ErrorBoundary";

// GTM-COPY-006 AC5: Per-page metadata for /login
export const metadata: Metadata = {
  title: "Acesse Suas Análises",
  description:
    "Entre na sua conta SmartLic para acessar análises de viabilidade, pipeline de oportunidades e relatórios de licitações.",
  alternates: {
    canonical: "https://smartlic.tech/login",
  },
  robots: {
    index: false,
    follow: true,
  },
};

/** DEBT-FE-007: ErrorBoundary wrapping for login page */
export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ErrorBoundary pageName="login">{children}</ErrorBoundary>;
}
