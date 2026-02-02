import type { Metadata } from "next";
import { DM_Sans, Fahkwang, DM_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "./components/ThemeProvider";
import { AnalyticsProvider } from "./components/AnalyticsProvider";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const fahkwang = Fahkwang({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const dmMono = DM_Mono({
  weight: ["400", "500"],
  subsets: ["latin"],
  variable: "--font-data",
  display: "swap",
});

const appName = process.env.NEXT_PUBLIC_APP_NAME || "Smart PNCP";

export const metadata: Metadata = {
  title: `${appName} - Busca Inteligente de Licitações`,
  description: "Ferramenta de busca avançada no PNCP com filtros por setor, região e período",
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    title: appName,
    description: "Busca inteligente de licitações no PNCP",
    siteName: appName,
    type: "website",
    locale: "pt_BR",
  },
  twitter: {
    card: "summary_large_image",
    title: appName,
    description: "Busca inteligente de licitações no PNCP",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning className={`${dmSans.variable} ${fahkwang.variable} ${dmMono.variable}`}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const theme = localStorage.getItem('bidiq-theme');
                if (!theme) return;
                if (theme === 'dark' || theme === 'dim') {
                  document.documentElement.classList.add('dark');
                }
                if (theme === 'paperwhite') {
                  document.documentElement.style.setProperty('--canvas', '#F5F0E8');
                } else if (theme === 'sepia') {
                  document.documentElement.style.setProperty('--canvas', '#EDE0CC');
                } else if (theme === 'dim') {
                  document.documentElement.style.setProperty('--canvas', '#2A2A2E');
                  document.documentElement.style.setProperty('--ink', '#e0e0e0');
                } else if (theme === 'dark') {
                  document.documentElement.style.setProperty('--canvas', '#121212');
                  document.documentElement.style.setProperty('--ink', '#e0e0e0');
                }
              } catch(e) {}
            `,
          }}
        />
      </head>
      <body>
        {/* Skip navigation link for accessibility - WCAG 2.4.1 Bypass Blocks */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50
                     focus:px-6 focus:py-3 focus:bg-brand-blue focus:text-white focus:rounded-button
                     focus:font-semibold focus:shadow-lg"
        >
          Pular para conteúdo principal
        </a>
        <AnalyticsProvider>
          <ThemeProvider>{children}</ThemeProvider>
        </AnalyticsProvider>
      </body>
    </html>
  );
}
