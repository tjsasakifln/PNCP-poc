'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import LandingNavbar from './landing/LandingNavbar';
import Footer from './Footer';
import type { BlogArticleMeta } from '@/lib/blog';

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

/* ---------- Share Buttons ---------- */

function ShareButtons({ title, url }: { title: string; url: string }) {
  const [copied, setCopied] = useState(false);

  const shareLinkedIn = () => {
    window.open(
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
      '_blank',
      'noopener,noreferrer',
    );
  };

  const shareWhatsApp = () => {
    window.open(
      `https://wa.me/?text=${encodeURIComponent(`${title} ${url}`)}`,
      '_blank',
      'noopener,noreferrer',
    );
  };

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      const textArea = document.createElement('textarea');
      textArea.value = url;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      className="flex flex-wrap items-center gap-3 pt-6 border-t border-[var(--border)]"
      data-testid="share-buttons"
    >
      <span className="text-sm text-ink-secondary">Compartilhar:</span>

      <button
        onClick={shareLinkedIn}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-ink-secondary hover:text-brand-blue border border-[var(--border)] rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]"
        aria-label="Compartilhar no LinkedIn"
        data-testid="share-linkedin"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
        </svg>
        LinkedIn
      </button>

      <button
        onClick={shareWhatsApp}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-ink-secondary hover:text-[var(--whatsapp)] border border-[var(--border)] rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]"
        aria-label="Compartilhar no WhatsApp"
        data-testid="share-whatsapp"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
        </svg>
        WhatsApp
      </button>

      <button
        onClick={copyLink}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-ink-secondary hover:text-brand-blue border border-[var(--border)] rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]"
        aria-label="Copiar link"
        data-testid="share-copy-link"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        {copied ? 'Copiado!' : 'Copiar link'}
      </button>
    </div>
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

  // AC2 + MKT-001 AC4: Article JSON-LD with author credentialing
  const blogPostingSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: article.title,
    description: article.description,
    author: {
      '@type': 'Organization',
      name: 'Equipe SmartLic',
      description: 'Especialistas em Inteligência de Licitações Públicas',
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
    dateModified: article.publishDate,
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
                  className="text-3xl sm:text-4xl lg:text-[2.75rem] font-bold text-ink leading-tight tracking-tight mb-4"
                  style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                >
                  {article.title}
                </h1>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-ink-secondary">
                  <time dateTime={article.publishDate}>
                    {formatDate(article.publishDate)}
                  </time>
                  <span aria-hidden="true">&middot;</span>
                  <span>{article.readingTime}</span>
                  <span aria-hidden="true">&middot;</span>
                  <span>
                    Equipe SmartLic — Especialistas em Inteligência de Licitações Públicas
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

              {/* Share Buttons */}
              <div className="mt-8">
                <ShareButtons title={article.title} url={canonicalUrl} />
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
