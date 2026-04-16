'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import LandingNavbar from './landing/LandingNavbar';
import Footer from './Footer';
import ShareButtons from '@/components/share/ShareButtons';
import type { BlogArticleMeta } from '@/lib/blog';
import { getAuthorBySlug, DEFAULT_AUTHOR_SLUG } from '@/lib/authors';

/**
 * STORY-261 AC1/AC2/AC3/AC14: Blog article layout component
 *
 * Features: reading progress bar, JSON-LD BlogPosting + BreadcrumbList,
 * breadcrumbs, share buttons, related articles sidebar, serif titles.
 */

interface BlogArticleLayoutProps {
  children: React.ReactNode;
  article: BlogArticleMeta;
  relatedArticles: BlogArticleMeta[];
}

/* ---------- Reading Progress Bar ---------- */

function ReadingProgressBar() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight =
        document.documentElement.scrollHeight - window.innerHeight;
      setProgress(docHeight > 0 ? (scrollTop / docHeight) * 100 : 0);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    // eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: progress bar width computed from scroll position at runtime
    <div
      className="fixed top-0 left-0 z-[60] h-[3px] bg-brand-blue transition-[width] duration-150 ease-out"
      style={{ width: `${progress}%` }}
      role="progressbar"
      aria-valuenow={Math.round(progress)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Progresso de leitura"
      data-testid="reading-progress-bar"
    />
  );
}

/* ---------- Helpers ---------- */

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T12:00:00');
  return date.toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

/* ---------- Main Layout ---------- */

export default function BlogArticleLayout({
  children,
  article,
  relatedArticles,
}: BlogArticleLayoutProps) {
  const canonicalUrl = `https://smartlic.tech/blog/${article.slug}`;

  // AC2 + MKT-001 AC4 + S7: Article JSON-LD with Person author (E-E-A-T)
  const resolvedAuthor = getAuthorBySlug(article.authorSlug || DEFAULT_AUTHOR_SLUG);
  const blogPostingSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: article.title,
    description: article.description,
    author: resolvedAuthor
      ? {
          '@type': 'Person',
          name: resolvedAuthor.name,
          url: `https://smartlic.tech/blog/author/${resolvedAuthor.slug}`,
          jobTitle: resolvedAuthor.role,
          sameAs: resolvedAuthor.sameAs,
        }
      : {
          '@type': 'Organization',
          name: 'Equipe SmartLic',
          url: 'https://smartlic.tech',
        },
    publisher: {
      '@type': 'Organization',
      name: 'SmartLic',
      logo: {
        '@type': 'ImageObject',
        url: 'https://smartlic.tech/logo.png',
      },
    },
    datePublished: article.publishDate,
    dateModified: article.lastModified || article.publishDate,
    ...(article.sources?.length && {
      citation: article.sources.map((s: string) => ({
        '@type': 'CreativeWork',
        name: s,
      })),
    }),
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': canonicalUrl,
    },
    wordCount: article.wordCount,
    articleSection: article.category,
    inLanguage: 'pt-BR',
  };

  // MKT-001 AC4: Organization schema
  const organizationSchema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'SmartLic',
    url: 'https://smartlic.tech',
    logo: 'https://smartlic.tech/logo.png',
    description:
      'Plataforma de inteligência em licitações públicas. Automação de análise, classificação por IA e análise de viabilidade para empresas B2G e consultorias.',
    sameAs: ['https://www.linkedin.com/company/smartlic'],
  };

  // AC3: BreadcrumbList JSON-LD
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Início',
        item: 'https://smartlic.tech',
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Blog',
        item: 'https://smartlic.tech/blog',
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: article.category,
        item: `https://smartlic.tech/blog?category=${encodeURIComponent(article.category)}`,
      },
      {
        '@type': 'ListItem',
        position: 4,
        name: article.title,
        item: canonicalUrl,
      },
    ],
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <ReadingProgressBar />
      <LandingNavbar />

      <main className="flex-1">
        {/* Structured Data — MKT-001 AC4: Article + FAQPage + BreadcrumbList + Organization */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(blogPostingSchema),
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(breadcrumbSchema),
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(organizationSchema),
          }}
        />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12">
          {/* AC3: Visual Breadcrumb */}
          <nav
            aria-label="Breadcrumb"
            className="mb-8 flex items-center gap-2 text-sm text-ink-secondary flex-wrap"
            data-testid="breadcrumb"
          >
            <Link
              href="/"
              className="hover:text-brand-blue transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 rounded px-1"
            >
              Início
            </Link>
            <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
            <Link
              href="/blog"
              className="hover:text-brand-blue transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 rounded px-1"
            >
              Blog
            </Link>
            <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
            <Link
              href={`/blog?category=${encodeURIComponent(article.category)}`}
              className="hover:text-brand-blue transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 rounded px-1"
            >
              {article.category}
            </Link>
            <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
            <span className="font-medium text-ink" aria-current="page">
              {article.title}
            </span>
          </nav>

          {/* Content Grid */}
          <div className="lg:grid lg:grid-cols-3 lg:gap-12">
            {/* Main Content */}
            <article className="lg:col-span-2">
              {/* Article Header — AC14: serif titles, institutional elegance */}
              <header className="mb-8 sm:mb-10">
                <span className="inline-block px-3 py-1 text-xs font-semibold uppercase tracking-wider text-brand-blue bg-brand-blue-subtle rounded-full mb-4">
                  {article.category}
                </span>
                <h1
                  className="text-3xl sm:text-4xl lg:text-[2.75rem] font-bold text-ink leading-tight tracking-tight mb-4 font-serif"
                >
                  {article.title}
                </h1>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-ink-secondary">
                  <time dateTime={article.publishDate}>
                    {formatDate(article.publishDate)}
                  </time>
                  {article.lastModified && article.lastModified !== article.publishDate && (
                    <>
                      <span aria-hidden="true">&middot;</span>
                      <span>
                        Atualizado em{' '}
                        <time dateTime={article.lastModified}>
                          {formatDate(article.lastModified)}
                        </time>
                      </span>
                    </>
                  )}
                  <span aria-hidden="true">&middot;</span>
                  <span>{article.readingTime}</span>
                  <span aria-hidden="true">&middot;</span>
                  <span>
                    {resolvedAuthor ? (
                      <Link href={`/blog/author/${resolvedAuthor.slug}`} className="text-brand-blue hover:underline">
                        {resolvedAuthor.name}
                      </Link>
                    ) : (
                      'Equipe SmartLic'
                    )}
                    {' — '}
                    {resolvedAuthor?.shortBio || 'Especialistas em Inteligência de Licitações Públicas'}
                  </span>
                </div>
              </header>

              {/* Article Body — AC14: prose-lg for generous spacing */}
              <div className="prose prose-lg prose-gray dark:prose-invert max-w-none prose-headings:text-ink prose-headings:font-bold prose-headings:tracking-tight prose-p:text-ink-secondary prose-p:leading-relaxed prose-strong:text-ink prose-a:text-brand-blue prose-a:no-underline hover:prose-a:underline prose-li:text-ink-secondary prose-h2:border-b prose-h2:border-[var(--border)] prose-h2:pb-3 prose-blockquote:border-l-brand-blue prose-blockquote:bg-surface-1 prose-blockquote:rounded-r-lg prose-blockquote:py-1 prose-blockquote:px-4">
                {children}
              </div>

              {/* Tags */}
              {article.tags.length > 0 && (
                <div className="mt-8 flex flex-wrap gap-2" data-testid="article-tags">
                  {article.tags.map((tag) => (
                    <Link
                      key={tag}
                      href={`/blog?tag=${encodeURIComponent(tag)}`}
                      className="px-3 py-1 text-xs font-medium text-ink-secondary bg-surface-1 border border-[var(--border)] rounded-full hover:text-brand-blue hover:border-brand-blue/30 transition-colors"
                    >
                      {tag}
                    </Link>
                  ))}
                </div>
              )}

              {/* Sources — SEO E-E-A-T */}
              {article.sources && article.sources.length > 0 && (
                <section className="mt-8 pt-6 border-t border-[var(--border)]">
                  <h2 className="text-sm font-semibold text-ink mb-3">Fontes e Referências</h2>
                  <ol className="list-decimal list-inside space-y-1">
                    {article.sources.map((source, i) => (
                      <li key={i} className="text-sm text-ink-secondary">{source}</li>
                    ))}
                  </ol>
                </section>
              )}

              {/* Share Buttons */}
              <div className="mt-8">
                <ShareButtons
                  title={article.title}
                  url={canonicalUrl}
                  description={article.description}
                  trackingContext={{ source: 'blog', slug: article.slug, category: article.category }}
                />
              </div>
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
                    href="/signup?source=blog-article"
                    className="block text-center bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2.5 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
                  >
                    Comece Grátis
                  </Link>
                </div>

                {/* SEO-PLAYBOOK Fundação §5 + P7: Calculator cross-link */}
                <div className="bg-surface-1 rounded-xl p-4 sm:p-6 border border-[var(--border)]">
                  <h3 className="font-semibold text-ink text-sm sm:text-base mb-2">
                    Quanto sua empresa perde por mês?
                  </h3>
                  <p className="text-xs sm:text-sm text-ink-secondary mb-3 leading-relaxed">
                    Descubra o valor de editais que passam despercebidos no seu setor.
                  </p>
                  <Link
                    href="/calculadora"
                    className="text-xs sm:text-sm font-medium text-brand-blue hover:underline"
                  >
                    Calcular oportunidades perdidas &rarr;
                  </Link>
                </div>

                {/* Related Articles — AC13 */}
                {relatedArticles.length > 0 && (
                  <div
                    className="bg-surface-1 rounded-xl p-4 sm:p-6 border border-[var(--border)]"
                    data-testid="related-articles"
                  >
                    <h3 className="font-semibold text-ink text-sm sm:text-base mb-3 sm:mb-4">
                      Artigos Relacionados
                    </h3>
                    <ul className="space-y-3">
                      {relatedArticles.slice(0, 3).map((related) => (
                        <li key={related.slug}>
                          <Link
                            href={`/blog/${related.slug}`}
                            className="block group"
                          >
                            <span className="text-xs text-brand-blue font-medium uppercase tracking-wider">
                              {related.category}
                            </span>
                            <p className="text-sm text-ink group-hover:text-brand-blue transition-colors mt-0.5 line-clamp-2">
                              {related.title}
                            </p>
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Categories */}
                <div className="bg-surface-1 rounded-xl p-4 sm:p-6 border border-[var(--border)]">
                  <h3 className="font-semibold text-ink text-sm sm:text-base mb-3 sm:mb-4">
                    Categorias
                  </h3>
                  <ul className="space-y-2">
                    <li>
                      <Link
                        href="/blog?category=Empresas+B2G"
                        className="text-sm text-ink-secondary hover:text-brand-blue transition-colors"
                      >
                        Empresas B2G
                      </Link>
                    </li>
                    <li>
                      <Link
                        href="/blog?category=Consultorias+de+Licita%C3%A7%C3%A3o"
                        className="text-sm text-ink-secondary hover:text-brand-blue transition-colors"
                      >
                        Consultorias de Licitação
                      </Link>
                    </li>
                  </ul>
                </div>

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
        </div>
      </main>

      <Footer />
    </div>
  );
}
