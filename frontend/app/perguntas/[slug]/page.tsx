import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { QUESTIONS, getQuestionBySlug, getAllQuestionSlugs, CATEGORY_META, getQuestionsByCategory } from '@/lib/questions';
import { GLOSSARY_TERMS } from '@/lib/glossary-terms';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const revalidate = 86400;

export function generateStaticParams() {
  return getAllQuestionSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const question = getQuestionBySlug(slug);
  if (!question) return {};

  return {
    title: `${question.title}`,
    description: question.metaDescription,
    alternates: { canonical: buildCanonical(`/perguntas/${slug}`) },
    openGraph: {
      title: `${question.title} | SmartLic`,
      description: question.metaDescription,
      url: buildCanonical(`/perguntas/${slug}`),
      type: 'article',
      siteName: 'SmartLic',
    },
    twitter: {
      card: 'summary_large_image',
      title: `${question.title} | SmartLic`,
      description: question.metaDescription,
    },
  };
}

export default async function PerguntaPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const question = getQuestionBySlug(slug);
  if (!question) notFound();

  // Related glossary terms
  const relatedTermObjects = question.relatedTerms
    .map((termSlug) => GLOSSARY_TERMS.find((t) => t.slug === termSlug))
    .filter(Boolean);

  // Related questions from same category (excluding self)
  const relatedQuestions = getQuestionsByCategory(question.category)
    .filter((q) => q.slug !== slug)
    .slice(0, 5);

  /* QAPage JSON-LD — primary schema for AI Overviews */
  const qaPageLd = {
    '@context': 'https://schema.org',
    '@type': 'QAPage',
    mainEntity: {
      '@type': 'Question',
      name: question.title,
      text: question.title,
      answerCount: 1,
      acceptedAnswer: {
        '@type': 'Answer',
        text: question.answer,
        author: {
          '@type': 'Organization',
          name: 'SmartLic',
          url: SITE_URL,
        },
      },
    },
  };

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Perguntas', item: buildCanonical('/perguntas') },
      { '@type': 'ListItem', position: 3, name: question.title.slice(0, 60), item: buildCanonical(`/perguntas/${slug}`) },
    ],
  };

  /* FAQPage JSON-LD — rich snippets para perguntas relacionadas da sidebar */
  const faqPageLd = relatedQuestions.length > 0
    ? {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: relatedQuestions.map((q) => ({
          '@type': 'Question',
          name: q.title,
          acceptedAnswer: {
            '@type': 'Answer',
            text: q.answer.slice(0, 500),
          },
        })),
      }
    : null;

  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-surface-0">
        {/* Hero */}
        <section className="bg-surface-1 border-b border-[var(--border)] py-12">
          <div className="mx-auto max-w-4xl px-4">
            <nav className="text-sm text-ink-muted mb-4">
              <Link href="/" className="hover:text-ink-primary transition-colors">Início</Link>
              <span className="mx-2">›</span>
              <Link href="/perguntas" className="hover:text-ink-primary transition-colors">Perguntas</Link>
              <span className="mx-2">›</span>
              <span className="text-ink-primary">{CATEGORY_META[question.category].label}</span>
            </nav>
            <h1 className="text-3xl font-bold text-ink-primary">{question.title}</h1>
            <div className="flex flex-wrap gap-2 mt-4">
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-brand-blue/10 text-brand-blue">
                {CATEGORY_META[question.category].label}
              </span>
              {question.legalBasis && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700">
                  {question.legalBasis}
                </span>
              )}
            </div>
          </div>
        </section>

        {/* Content grid */}
        <div className="mx-auto max-w-4xl px-4 py-12 grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Main content */}
          <article className="lg:col-span-2">
            <div className="prose prose-lg max-w-none text-ink-secondary leading-relaxed">
              {question.answer.split('\n\n').map((paragraph, i) => (
                <p key={i}>{paragraph}</p>
              ))}
            </div>

            {/* Related articles */}
            {question.relatedArticles.length > 0 && (
              <div className="mt-8 p-4 rounded-xl bg-surface-1 border border-[var(--border)]">
                <h3 className="font-semibold text-ink-primary mb-3">Artigos relacionados</h3>
                <ul className="space-y-2">
                  {question.relatedArticles.map((articleSlug) => (
                    <li key={articleSlug}>
                      <Link
                        href={`/blog/${articleSlug}`}
                        className="text-sm text-brand-blue hover:underline"
                      >
                        {articleSlug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} →
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </article>

          {/* Sidebar */}
          <aside className="space-y-6">
            {/* Related glossary terms */}
            {relatedTermObjects.length > 0 && (
              <div className="p-4 rounded-xl border border-[var(--border)]">
                <h3 className="font-semibold text-ink-primary mb-3">Termos do Glossário</h3>
                <ul className="space-y-2">
                  {relatedTermObjects.map((term) => (
                    <li key={term!.slug}>
                      <Link
                        href={`/glossario/${term!.slug}`}
                        className="text-sm text-brand-blue hover:underline"
                      >
                        {term!.term}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Related questions */}
            {relatedQuestions.length > 0 && (
              <div className="p-4 rounded-xl border border-[var(--border)]">
                <h3 className="font-semibold text-ink-primary mb-3">Perguntas relacionadas</h3>
                <ul className="space-y-2">
                  {relatedQuestions.map((q) => (
                    <li key={q.slug}>
                      <Link
                        href={`/perguntas/${q.slug}`}
                        className="text-sm text-brand-blue hover:underline"
                      >
                        {q.title}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Cross-links */}
            <div className="p-4 rounded-xl border border-[var(--border)]">
              <h3 className="font-semibold text-ink-primary mb-3">Ferramentas</h3>
              <ul className="space-y-2">
                <li>
                  <Link href="/calculadora" className="text-sm text-brand-blue hover:underline">
                    Calculadora de Oportunidades →
                  </Link>
                </li>
                <li>
                  <Link href="/glossario" className="text-sm text-brand-blue hover:underline">
                    Glossário de Licitações →
                  </Link>
                </li>
                <li>
                  <Link href="/perguntas" className="text-sm text-brand-blue hover:underline">
                    ← Todas as perguntas
                  </Link>
                </li>
              </ul>
            </div>
          </aside>
        </div>

        {/* JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(qaPageLd) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }} />
        {faqPageLd && (
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqPageLd) }} />
        )}
      </main>
      <Footer />
    </>
  );
}
