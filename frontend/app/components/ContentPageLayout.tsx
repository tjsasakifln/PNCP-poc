import LandingNavbar from './landing/LandingNavbar';
import Footer from './Footer';
import Link from 'next/link';
import BreadcrumbNav from '@/components/seo/BreadcrumbNav';
import type { BreadcrumbItem } from '@/lib/seo';
import type { JourneyStep } from '@/lib/seo/relatedResolver';
import { JourneyLinks } from '@/app/components/navigation/JourneyLinks';

interface RelatedPage {
  href: string;
  title: string;
}

interface ContentPageLayoutProps {
  children: React.ReactNode;
  breadcrumbLabel: string;
  relatedPages: RelatedPage[];
  /** Optional full breadcrumb trail. If provided, overrides the 2-level default. */
  breadcrumbItems?: BreadcrumbItem[];
  /**
   * CONV-017 (#1332): Intent-progressive journey links.
   * When provided, replaces the legacy `relatedPages` sidebar section with
   * JourneyLinks structured as numbered steps. Up to 5 steps.
   */
  journeyLinks?: JourneyStep[];
  /** Template identifier for analytics when journeyLinks is used. */
  journeySourceTemplate?: string;
}

export default function ContentPageLayout({
  children,
  breadcrumbLabel,
  relatedPages,
  breadcrumbItems,
  journeyLinks,
  journeySourceTemplate = 'entity',
}: ContentPageLayoutProps) {
  const items: BreadcrumbItem[] =
    breadcrumbItems ?? [
      { label: 'Início', href: '/' },
      { label: breadcrumbLabel },
    ];

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12">
          <BreadcrumbNav
            items={items}
            className="mb-8"
            suppressSchema={!breadcrumbItems}
          />

          {/* Content Grid */}
          <div className="lg:grid lg:grid-cols-3 lg:gap-12">
            {/* Main Content */}
            <article className="lg:col-span-2 prose prose-base sm:prose-lg prose-gray dark:prose-invert max-w-none prose-headings:text-ink prose-headings:font-bold prose-headings:tracking-tight prose-p:text-ink-secondary prose-p:leading-relaxed prose-strong:text-ink prose-a:text-brand-blue prose-a:no-underline hover:prose-a:underline prose-li:text-ink-secondary prose-h2:border-b prose-h2:border-[var(--border)] prose-h2:pb-3">
              {children}
            </article>

            {/* Sidebar */}
            <aside className="mt-8 sm:mt-12 lg:mt-0">
              <div className="sticky top-24 space-y-6 sm:space-y-8">
                {/* CTA Card */}
                <div className="bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-4 sm:p-6 border border-brand-blue/20 shadow-sm">
                  <h3 className="font-semibold text-ink text-base sm:text-lg mb-2">
                    Avalie licitações automaticamente
                  </h3>
                  <p className="text-xs sm:text-sm text-ink-secondary mb-3 sm:mb-4 leading-relaxed">
                    O SmartLic analisa editais em segundos usando IA e 5
                    critérios de viabilidade.
                  </p>
                  <Link
                    href="/consultoria-b2g?source=conteudo"
                    className="block text-center bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2.5 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
                  >
                    Pedir diagnóstico à CONFENGE
                  </Link>
                </div>

                {/* Journey Links (CONV-017) — replaces legacy relatedPages when provided */}
                {journeyLinks && journeyLinks.length > 0 ? (
                  <div className="bg-surface-1 rounded-xl p-4 sm:p-6 border border-[var(--border)]">
                    <h3 className="font-semibold text-ink text-sm sm:text-base mb-3 sm:mb-4">
                      Navegação recomendada
                    </h3>
                    <ul className="space-y-3">
                      {journeyLinks.map((step) => (
                        <li key={step.position}>
                          <Link
                            href={step.href}
                            className="group flex items-start gap-2 text-xs sm:text-sm text-brand-blue hover:underline transition-colors rounded px-1"
                          >
                            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-100 text-[10px] font-bold text-blue-700 group-hover:bg-blue-200 transition-colors" aria-hidden="true">
                              {step.position}
                            </span>
                            <span className="flex-1 min-w-0">
                              <span className="block font-medium">{step.icon} {step.title}</span>
                              <span className="block text-gray-500 text-xs mt-0.5 line-clamp-2">{step.description}</span>
                            </span>
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  /* Legacy Related Pages (fallback) */
                  relatedPages.length > 0 && (
                    <div className="bg-surface-1 rounded-xl p-4 sm:p-6 border border-[var(--border)]">
                      <h3 className="font-semibold text-ink text-sm sm:text-base mb-3 sm:mb-4">
                        Conteúdo relacionado
                      </h3>
                      <ul className="space-y-2.5 sm:space-y-3">
                        {relatedPages.map((page) => (
                          <li key={page.href}>
                            <Link
                              href={page.href}
                              className="text-xs sm:text-sm text-brand-blue hover:underline transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 rounded px-1"
                            >
                              {page.title}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )
                )}

                {/* Features Link */}
                <div className="border-t border-[var(--border)] pt-4 sm:pt-6">
                  <p className="text-xs sm:text-sm text-ink-secondary mb-2">
                    Conheça todas as funcionalidades
                  </p>
                  <Link
                    href="/features"
                    className="text-xs sm:text-sm font-medium text-brand-blue hover:underline"
                  >
                    Ver recursos do SmartLic &rarr;
                  </Link>
                </div>
              </div>
            </aside>
          </div>

          {/* Full-width JourneyLinks below the grid when not in sidebar */}
          {journeyLinks && journeyLinks.length > 0 && (
            <div className="mt-8 max-w-2xl">
              <JourneyLinks
                journey={journeyLinks}
                sourceTemplate={journeySourceTemplate}
              />
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
