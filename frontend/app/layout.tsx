import type { Metadata } from "next";
import { DM_Sans, Fahkwang, DM_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "./components/ThemeProvider";
import { AnalyticsProvider } from "./components/AnalyticsProvider";
import { AuthProvider } from "./components/AuthProvider";
import { NProgressProvider } from "./components/NProgressProvider";
import { Toaster } from "sonner";
import { CookieConsentBanner } from "./components/CookieConsentBanner";

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

// Force rebuild to pick up NEXT_PUBLIC_APP_NAME from Railway (SmartLic.tech)
const appName = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic.tech";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://bidiq-frontend-production.up.railway.app"),
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
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: `${appName} - Busca Inteligente de Licitações`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: appName,
    description: "Busca inteligente de licitações no PNCP",
    images: ["/og-image.png"],
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
              (function() {
                try {
                  let theme = localStorage.getItem('bidiq-theme');
                  if (!theme) return;
                  if (theme === 'system') {
                    theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  }
                  if (theme === 'dark') {
                    document.documentElement.classList.add('dark');
                  }
                } catch(e) {}
              })();
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
          <AuthProvider>
            <ThemeProvider>
              <NProgressProvider>
                {children}
                <Toaster position="top-right" richColors closeButton />
                <CookieConsentBanner />
              </NProgressProvider>
            </ThemeProvider>
          </AuthProvider>
        </AnalyticsProvider>
      </body>
    </html>
  );
}
