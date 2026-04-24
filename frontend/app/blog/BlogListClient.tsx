'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import type { BlogArticleMeta, BlogCategory } from '@/lib/blog';

/**
 * STORY-261 AC4: Client-side blog article list with category filtering.
 */

const CATEGORIES: Array<{ label: string; value: BlogCategory | 'all' }> = [
  { label: 'Todos', value: 'all' },
  { label: 'Empresas B2G', value: 'Empresas B2G' },
  { label: 'Consultorias', value: 'Consultorias de Licitação' },
  { label: 'Guias', value: 'Guias' },
];

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T12:00:00');
  return date.toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export default function BlogListClient({
  articles,
}: {
  articles: BlogArticleMeta[];
}) {
  const [activeCategory, setActiveCategory] = useState<
    BlogCategory | 'all'
  >('all');

  const filtered =
    activeCategory === 'all'
      ? articles
      : articles.filter((a) => a.category === activeCategory);

  // Sort: most recent first
  const sorted = [...filtered].sort(
    (a, b) =>
      new Date(b.publishDate).getTime() - new Date(a.publishDate).getTime(),
  );

  return (
    <>
      {/* Filter Tabs */}
      <div
        className="flex flex-wrap gap-2 mb-8 sm:mb-10"
        role="tablist"
        aria-label="Filtrar por categoria"
      >
        {CATEGORIES.map((cat) => (
          <button
            key={cat.value}
            role="tab"
            aria-selected={activeCategory === cat.value}
            onClick={() => setActiveCategory(cat.value)}
            className={`px-4 py-2 text-sm font-medium rounded-full border transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] ${
              activeCategory === cat.value
                ? 'bg-brand-navy text-white border-brand-navy'
                : 'bg-surface-0 text-ink-secondary border-[var(--border)] hover:border-brand-blue/30 hover:text-brand-blue'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Article Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {sorted.map((article, index) => (
          <React.Fragment key={article.slug}>
            {/* SEO-480: <article> wrapper for semantic HTML + crawler discovery */}
            <article className="contents" data-testid="blog-article-card">
              <Link
                href={`/blog/${article.slug}`}
                className="group block bg-surface-0 border border-[var(--border)] rounded-xl p-5 sm:p-6 hover:border-brand-blue/30 hover:shadow-md transition-all"
              >
                <span className="inline-block px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-brand-blue bg-brand-blue-subtle rounded-full mb-3">
                  {article.category}
                </span>
                <h3 className="text-base sm:text-lg font-bold text-ink group-hover:text-brand-blue transition-colors line-clamp-2 mb-2">
                  {article.title}
                </h3>
                <p className="text-sm text-ink-secondary line-clamp-2 mb-3">
                  {article.description}
                </p>
                <div className="flex items-center gap-3 text-xs text-ink-muted">
                  <time dateTime={article.publishDate}>
                    {formatDate(article.publishDate)}
                  </time>
                  <span aria-hidden="true">&middot;</span>
                  <span>{article.readingTime}</span>
                </div>
              </Link>
            </article>

            {/* CTA Banner every 6 articles */}
            {(index + 1) % 6 === 0 && index < sorted.length - 1 && (
              <div
                className="sm:col-span-2 lg:col-span-3 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-6 sm:p-8 text-center border border-brand-blue/20"
              >
                <p className="text-lg font-bold text-ink mb-2">
                  Experimente o SmartLic gratuitamente
                </p>
                <p className="text-sm text-ink-secondary mb-4 max-w-lg mx-auto">
                  Descubra quais licitações valem seu tempo com avaliação de
                  viabilidade por IA.
                </p>
                <Link
                  href="/signup?source=blog-listing-cta"
                  className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 py-2.5 rounded-button text-sm transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  Comece Grátis
                </Link>
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Empty state */}
      {sorted.length === 0 && (
        <div className="text-center py-12">
          <p className="text-ink-secondary">
            Nenhum artigo encontrado nesta categoria.
          </p>
        </div>
      )}
    </>
  );
}
