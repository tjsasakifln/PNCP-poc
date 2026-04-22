import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import type { PillarMeta } from '@/lib/pillars';
import TableOfContents from './TableOfContents';

/**
 * STORY-SEO-008 AC2/AC4: Pillar page layout for /guia/[slug]
 *
 * Features:
 *   - JSON-LD Article + BreadcrumbList + ItemList (spokes) + FAQPage
 *   - Sticky Table of Contents (desktop sidebar, collapsed mobile)
 *   - Answer-first intro + category badge
 *   - Sources section (E-E-A-T authority links)
 *   - Related articles (spokes) block at the bottom
 *   - Inline CTA for 14-day trial
 */

interface PillarPageLayoutProps {
  pillar: PillarMeta;
  children: React.ReactNode;
  /** Section IDs + titles for TOC (in order). H2s of the article. */
  sections: { id: string; title: string }[];
}

const SITE = 'https://smartlic.tech';

export default function PillarPageLayout({ pillar, children, sections }: PillarPageLayoutProps) {
  const canonicalUrl = `${SITE}/guia/${pillar.slug}`;

  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: pillar.title,
    description: pillar.description,
    author: {
      '@type': 'Organization',
      name: 'Equipe SmartLic',
      url: SITE,
    },
    publisher: {
      '@type': 'Organization',
      name: 'SmartLic',
      logo: {
        '@type': 'ImageObject',
        url: `${SITE}/logo.png`,
      },
    },
    datePublished: pillar.publishDate,
    dateModified: pillar.lastModified,
    mainEntityOfPage: { '@type': 'WebPage', '@id': canonicalUrl },
    wordCount: pillar.wordCount,
    articleSection: 'Guias',
    inLanguage: 'pt-BR',
    citation: pillar.authorityLinks.map((a) => ({ '@type': 'CreativeWork', name: a.text, url: a.url })),
  };

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Início', item: SITE },
      { '@type': 'ListItem', position: 2, name: 'Guias', item: `${SITE}/guia` },
      { '@type': 'ListItem', position: 3, name: pillar.shortTitle, item: canonicalUrl },
    ],
  };

  const itemListSchema = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `Artigos relacionados — ${pillar.shortTitle}`,
    itemListElement: pillar.spokes.map((spoke, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: `${SITE}/blog/${spoke.slug}`,
      name: spoke.title,
    })),
  };

  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: pillar.faq.map((f) => ({
      '@type': 'Question',
      name: f.question,
      acceptedAnswer: { '@type': 'Answer', text: f.answer },
    })),
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <main className="flex-1">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(itemListSchema) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
        />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12">
          {/* Visual Breadcrumb */}
          <nav
            aria-label="Breadcrumb"
            className="mb-8 flex items-center gap-2 text-sm text-ink-secondary flex-wrap"
            data-testid="breadcrumb"
          >
            <Link href="/" className="hover:text-brand-blue transition-colors px-1 rounded">
              Início
            </Link>
            <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
            <Link href="/guia" className="hover:text-brand-blue transition-colors px-1 rounded">
              Guias
            </Link>
            <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
            <span className="font-medium text-ink" aria-current="page">
              {pillar.shortTitle}
            </span>
          </nav>

          {/* Grid: Main content + Sticky TOC */}
          <div className="lg:grid lg:grid-cols-[1fr_260px] lg:gap-12">
            {/* Main Article */}
            <article className="min-w-0">
              <header className="mb-8 sm:mb-10">
                <span className="inline-block px-3 py-1 text-xs font-semibold uppercase tracking-wider text-brand-blue bg-brand-blue-subtle rounded-full mb-4">
                  Pillar Page &middot; Guia Completo
                </span>
                <h1 className="text-3xl sm:text-4xl lg:text-[2.75rem] font-bold text-ink leading-tight tracking-tight mb-4 font-serif">
                  {pillar.title}
                </h1>
                <p className="text-lg text-ink-secondary leading-relaxed">
                  {pillar.description}
                </p>
              </header>

              <div className="prose prose-lg prose-gray dark:prose-invert max-w-none prose-headings:text-ink prose-headings:font-bold prose-headings:tracking-tight prose-p:text-ink-secondary prose-p:leading-relaxed prose-strong:text-ink prose-a:text-brand-blue prose-a:no-underline hover:prose-a:underline prose-li:text-ink-secondary prose-h2:border-b prose-h2:border-[var(--border)] prose-h2:pb-3 prose-h2:mt-12 prose-h2:scroll-mt-24 prose-h3:scroll-mt-24 prose-blockquote:border-l-brand-blue prose-blockquote:bg-surface-1 prose-blockquote:rounded-r-lg prose-blockquote:py-1 prose-blockquote:px-4">
                {children}
              </div>

              {/* Inline CTA */}
              <aside className="my-12 rounded-xl border border-brand-blue/30 bg-brand-blue-subtle p-6 sm:p-8 not-prose">
                <h3 className="text-xl sm:text-2xl font-bold text-ink mb-2">
                  Automatize a triagem de editais
                </h3>
                <p className="text-ink-secondary mb-4">
                  O SmartLic monitora PNCP, Compras.gov e Portal de Compras Públicas 24/7 e usa IA para classificar relevância setorial por empresa. Teste grátis por 14 dias, sem cartão.
                </p>
                <Link
                  href="/signup?ref=pillar-inline-cta"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-brand-blue text-white font-semibold rounded-lg hover:bg-brand-blue/90 transition-colors"
                  data-testid="pillar-inline-cta"
                >
                  Começar teste grátis de 14 dias
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </aside>

              {/* Related Articles (Spokes) */}
              <section className="mt-12 pt-8 border-t border-[var(--border)]">
                <h2 className="text-2xl font-bold text-ink mb-6 font-serif">
                  Artigos Relacionados
                </h2>
                <ul className="grid sm:grid-cols-2 gap-4" data-testid="pillar-spokes">
                  {pillar.spokes.map((spoke) => (
                    <li key={spoke.slug} className="group">
                      <Link
                        href={`/blog/${spoke.slug}`}
                        className="block p-4 rounded-lg border border-[var(--border)] bg-surface-1 hover:border-brand-blue/40 hover:shadow-sm transition-all"
                      >
                        <h3 className="font-semibold text-ink group-hover:text-brand-blue transition-colors text-base leading-snug mb-1">
                          {spoke.title}
                        </h3>
                        <p className="text-sm text-ink-secondary leading-relaxed">
                          {spoke.description}
                        </p>
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>

              {/* Sources / Authority Links */}
              <section className="mt-10 pt-6 border-t border-[var(--border)]">
                <h2 className="text-lg font-semibold text-ink mb-3 font-serif">
                  Fontes Oficiais
                </h2>
                <ul className="space-y-2 text-sm">
                  {pillar.authorityLinks.map((link) => (
                    <li key={link.url}>
                      <a
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand-blue hover:underline"
                      >
                        {link.text}
                      </a>
                    </li>
                  ))}
                </ul>
              </section>

              {/* FAQ (visible + FAQPage schema above covers the schema.org side) */}
              <section className="mt-10 pt-6 border-t border-[var(--border)]" data-testid="pillar-faq">
                <h2 className="text-2xl font-bold text-ink mb-6 font-serif">
                  Perguntas Frequentes
                </h2>
                <dl className="space-y-6">
                  {pillar.faq.map((f, i) => (
                    <div key={i}>
                      <dt className="text-base font-semibold text-ink mb-2">{f.question}</dt>
                      <dd className="text-ink-secondary leading-relaxed">{f.answer}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            </article>

            {/* Sticky TOC — desktop only */}
            <aside className="hidden lg:block">
              <TableOfContents sections={sections} />
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
