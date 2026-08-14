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
import { NavigationShell } from "../components/NavigationShell";
import { TrialProgressBar } from "../components/TrialProgressBar";
import { BackendStatusProvider } from "./components/BackendStatusIndicator";
import { DegradationBanner } from "./components/DegradationBanner";
import { SWRProvider } from "../components/SWRProvider";
import { UserProvider } from "../contexts/UserContext";
import { FoundersTopBanner } from "../components/banners/FoundersTopBanner";
import { headers } from "next/headers";
import { StructuredData } from "./components/StructuredData";
import { GoogleAnalytics } from "./components/GoogleAnalytics";
import { ClarityAnalytics } from "./components/ClarityAnalytics";
import { WebVitalsReporter } from "./components/WebVitalsReporter";
import { ExitIntentPopup } from "./components/ExitIntentPopup";
import NetworkAnalyticsBanner from "../components/NetworkAnalyticsBanner";

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
  // FE-020: Fahkwang is used in headings/display text only; skip preload to
  // avoid blocking the critical path. DM Sans is the primary body font.
  preload: false,
});

const dmMono = DM_Mono({
  weight: ["400", "500"],
  subsets: ["latin"],
  variable: "--font-data",
  display: "swap",
  // FE-020: DM Mono is used in data/code displays; skip preload since it is
  // not needed for initial rendering of any above-the-fold content.
  preload: false,
});

import { APP_NAME } from "../lib/config";

/* GTM-006 AC6: Explicit viewport configuration */
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://smartlic.tech"),
  // GTM-COPY-006 AC1: Decision-strategy positioning (max 60 chars)
  title: {
    default: `SmartLic — Inteligência pública de licitações da CONFENGE`,
    template: `%s | ${APP_NAME}`,
  },
  description: "Consulte empresas, contratos, licitações, órgãos e municípios com dados públicos verificáveis. Braço de inbound da CONFENGE — sem assinatura e sem trial.",
  // GTM-COPY-006 AC3: Decision-territory keywords (not generic search)
  keywords: [
    "como avaliar licitação antes de participar",
    "filtrar licitações por viabilidade",
    "quais licitações vale a pena participar",
    "análise de viabilidade de licitação",
    "priorizar editais por chance de vitória",
    "como não perder tempo com licitação errada",
    "filtro estratégico de licitações",
    "inteligência de decisão em licitações",
    "avaliação objetiva de editais públicos",
  ],
  icons: {
    icon: "/favicon.ico",
  },
  // GTM-COPY-006 AC4: OG tags aligned with new positioning
  openGraph: {
    title: `SmartLic — Máquina de Receita Previsível para Empresas B2G`,
    description: "Veja editais que sua empresa perderia — e os que ela pode vencer. Filtro estratégico com IA para empresas B2G.",
    siteName: APP_NAME,
    url: "https://smartlic.tech",
    type: "website",
    locale: "pt_BR",
    images: [
      {
        url: "/api/og",
        width: 1200,
        height: 630,
        alt: `${APP_NAME} — Inteligência de decisão em licitações públicas`,
      },
    ],
  },
  // GTM-COPY-006 AC4: Twitter cards aligned
  twitter: {
    card: "summary_large_image",
    title: `SmartLic — Máquina de Receita Previsível para Empresas B2G`,
    description: "Veja editais que sua empresa perderia — e os que ela pode vencer. Filtro estratégico com IA para empresas B2G.",
    images: ["/api/og"],
    // No Twitter/X profile — omit creator/site handles
  },
  // SEO-P0-004 (#990): Global canonical default uses relative '/' so that
  // per-page generateMetadata() can override with route-specific canonicals.
  // metadataBase resolves relative URLs to https://smartlic.tech automatically.
  // SEO-P0-001 (#988): hreflang pt-BR signals single-language Brazilian Portuguese site.
  alternates: {
    canonical: "/",
    languages: {
      'pt-BR': '/',
      'x-default': '/',
    },
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
  verification: {
    google: 'Aw8-Y5ify3ORrRN69yYgmAehSdO-3G5O65yW5Y3VEto',
  },
};

// ISSUE-1798: Layout is now async to read x-nonce header for CSP nonce.
// This makes the page tree render dynamically (Cache-Control: private by Next.js),
// but the middleware overrides Cache-Control for public routes (s-maxage=3600).
// Phase 1 (report-only): the enforcing CSP still has 'unsafe-inline', so there
// is no behavior change — only the CSP-Report-Only header uses the nonce.
export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // ISSUE-1798: Read per-request nonce from middleware for CSP report-only mode.
  const h = await headers();
  const nonce = h.get("x-nonce") || "";
  return (
    <html lang="pt-BR" suppressHydrationWarning className={`${dmSans.variable} ${fahkwang.variable} ${dmMono.variable}`}>
      <head>
        {/* Google Analytics 4 with LGPD/GDPR compliance */}
        <GoogleAnalytics />
        {/* Microsoft Clarity — heatmaps & session recordings */}
        <ClarityAnalytics />
        {/* Schema.org Structured Data for Google AI Search */}
        <StructuredData />
        {/* STORY-261 AC11: RSS feed discovery */}
        <link rel="alternate" type="application/rss+xml" title="SmartLic Blog" href="/blog/rss.xml" />
        {/* SEO: PWA manifest (completes sw.js + offline.html signal chain) */}
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#0a1e3f" />
        {/* SEO-P0-001 (#988): Geo-targeting + content-language signals for HCU classifier.
            Suppresses off-intent SERP exposure in non-BR markets (US/CA/UK/MX 0% CTR traffic).
            Pairs with GSC International Targeting → Country = Brazil (set via Search Console UI). */}
        <meta name="content-language" content="pt-BR" />
        <meta name="geo.region" content="BR" />
        <meta name="geo.country" content="Brazil" />
        <meta name="geo.placename" content="Brasil" />
        <meta httpEquiv="Content-Language" content="pt-BR" />
        {/* SEO: Preconnect to critical origins for faster TTFB */}
        <link rel="preconnect" href="https://fqqyovlzdzimiwfofdjk.supabase.co" />
        <link rel="dns-prefetch" href="https://fqqyovlzdzimiwfofdjk.supabase.co" />
        {/* Issue #994: Preconnect to backend API to shave LCP on first data fetch */}
        <link rel="preconnect" href="https://api.smartlic.tech" />
        <link rel="dns-prefetch" href="https://api.smartlic.tech" />
        {/* ISSUE-1798: nonce attribute for CSP report-only mode — read from x-nonce middleware header */}
        <script
          nonce={nonce}
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var legacy = localStorage.getItem('bidiq-theme');
                  if (legacy) { localStorage.setItem('smartlic-theme', legacy); localStorage.removeItem('bidiq-theme'); }
                  let theme = localStorage.getItem('smartlic-theme');
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
        {/* STORY-SEO-006: Real User Monitoring for Core Web Vitals → GA4 */}
        <WebVitalsReporter />
        {/* Skip navigation link for accessibility - WCAG 2.4.1 Bypass Blocks */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50
                     focus:px-6 focus:py-3 focus:bg-brand-blue focus:text-white focus:rounded-button
                     focus:font-semibold focus:shadow-lg"
        >
          Pular para conteúdo principal
        </a>
          <AuthProvider>
            <AnalyticsProvider>
            <SWRProvider>
            <UserProvider>
            <ThemeProvider>
              <NProgressProvider>
                <BackendStatusProvider>
                  <DegradationBanner />
                  <SessionExpiredBanner />
                  <PaymentFailedBanner />
                  <FoundersTopBanner />
                  <NetworkAnalyticsBanner />
                  <TrialProgressBar />
                  <NavigationShell>
                    {children}
                  </NavigationShell>
                  {/* GTM-POLISH-002 AC4: bottom-center for proper mobile stacking */}
                  {/* TD-FE-030: max-w-[90vw] mobile, mobileOffset=80 clears BottomNav (h-16=64px + 16px gap) */}
                  <Toaster
                    position="bottom-center"
                    richColors
                    closeButton
                    toastOptions={{
                      classNames: {
                        toast: "max-w-[90vw] sm:max-w-md",
                      },
                    }}
                    mobileOffset={{ bottom: 80 }}
                  />
                  <CookieConsentBanner />
                  <ExitIntentPopup />
                </BackendStatusProvider>
              </NProgressProvider>
            </ThemeProvider>
            </UserProvider>
            </SWRProvider>
            </AnalyticsProvider>
          </AuthProvider>
      </body>
    </html>
  );
}
