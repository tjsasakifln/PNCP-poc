import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BidIQ Uniformes",
  description: "Busca inteligente de licitações de uniformes no PNCP",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
