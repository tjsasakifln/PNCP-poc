import type { Metadata, Viewport } from "next";
import { DM_Sans, Fahkwang, DM_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "./components/ThemeProvider";
import { AnalyticsProvider } from "./components/AnalyticsProvider";
import { AuthProvider } from "./components/AuthProvider";
import { NProgressProvider } from "./components/NProgressProvider";
import { Toaster } from "sonner";
import { CookieConsentBanner } from "./components/CookieConsentBanner";
import { SessionExpiredBanner } from "./components/SessionExpiredBanner";
import { PaymentFailedBanner } from "../components/billing/PaymentFailedBanner";
import { StructuredData } from "./components/StructuredData";
import { GoogleAnalytics } from "./components/GoogleAnalytics";

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

/* GTM-006 AC6: Explicit viewport configuration */
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://smartlic.tech"),
  // Google AI Search optimized: conversational, specific, problem-focused
  title: {
    default: `${appName} - Como Encontrar e Vencer Licitações Públicas Facilmente`,
    template: `%s | ${appName}`,
  },
  description: "Encontre oportunidades de licitações públicas filtradas por setor, região e valor. Descubra quais editais valem a pena com avaliação por IA e exporte relatórios completos. Sistema usado por 500+ empresas para aumentar taxa de aprovação em concorrências públicas.",
  keywords: [
    // Conversational long-tail keywords for AI search
    "como encontrar licitações públicas",
    "buscar editais de licitação por setor",
    "alertas de novas licitações",
    "filtrar licitações por valor",
    "relatórios de licitações PNCP",
    "oportunidades de compras governamentais",
    "análise de licitações por região",
    "sistema de busca de editais",
    "como vencer licitações públicas",
  ],
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    title: `${appName} - Encontre e Vença Licitações Públicas com Inteligência Artificial`,
    description: "Descubra as melhores oportunidades de licitações públicas com busca inteligente por setor, análise de viabilidade por IA e relatórios completos. Economize horas de trabalho manual e aumente sua taxa de aprovação em concorrências governamentais.",
    siteName: appName,
    url: "https://smartlic.tech",
    type: "website",
    locale: "pt_BR",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: `${appName} - Plataforma de Busca Inteligente de Licitações Públicas`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: `${appName} - Como Encontrar Licitações Públicas Lucrativas`,
    description: "Busca inteligente de editais por setor, região e valor. Notificações, análise de viabilidade e relatórios completos. Usado por 500+ empresas.",
    images: ["/og-image.png"],
    creator: "@smartlic",
    site: "@smartlic",
  },
  // Additional metadata for AI search optimization
  alternates: {
    canonical: "https://smartlic.tech",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  // Verification for search engines
  verification: {
    google: 'Aw8-Y5ify3ORrRN69yYgmAehSdO-3G5O65yW5Y3VEto', // From Google Search Console
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
        {/* Google Analytics 4 with LGPD/GDPR compliance */}
        <GoogleAnalytics />
        {/* Schema.org Structured Data for Google AI Search */}
        <StructuredData />
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
                <SessionExpiredBanner />
                <PaymentFailedBanner />
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
