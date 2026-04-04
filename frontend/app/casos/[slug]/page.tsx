import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getAllCaseSlugs, getCaseBySlug } from '@/lib/cases';
import BlogInlineCTA from '@/app/blog/components/BlogInlineCTA';

const baseUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';

export const revalidate = 86400; // ISR 24h

export function generateStaticParams() {
  return getAllCaseSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const c = getCaseBySlug(slug);
  if (!c) return { title: 'Caso não encontrado | SmartLic' };

  return {
    title: `${c.title} | SmartLic`,
    description: c.description,
    keywords: c.keywords,
    alternates: { canonical: `${baseUrl}/casos/${c.slug}` },
    openGraph: {
      title: c.title,
      description: c.description,
      url: `${baseUrl}/casos/${c.slug}`,
      type: 'article',
      locale: 'pt_BR',
      publishedTime: c.publishDate,
      modifiedTime: c.lastModified || c.publishDate,
      tags: c.keywords,
      images: [
        {
          url: `${baseUrl}/api/og?title=${encodeURIComponent(c.title)}&category=Caso+de+Sucesso`,
          width: 1200,
          height: 630,
        },
      ],
    },
    twitter: { card: 'summary_large_image' },
  };
}

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const c = getCaseBySlug(slug);
  if (!c) notFound();

  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: c.title,
    description: c.description,
    datePublished: c.publishDate,
    dateModified: c.lastModified || c.publishDate,
    author: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: baseUrl,
    },
    publisher: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: baseUrl,
    },
    mainEntityOfPage: `${baseUrl}/casos/${c.slug}`,
  };

  const reviewSchema = {
    '@context': 'https://schema.org',
    '@type': 'Review',
    reviewRating: {
      '@type': 'Rating',
      ratingValue: c.metrics.scoreMedio.toString(),
      bestRating: '100',
      worstRating: '0',
    },
    itemReviewed: {
      '@type': 'SoftwareApplication',
      name: 'SmartLic',
      applicationCategory: 'BusinessApplication',
      url: baseUrl,
    },
    author: {
      '@type': 'Organization',
      name: c.company,
    },
    reviewBody: c.description,
  };

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: baseUrl },
      { '@type': 'ListItem', position: 2, name: 'Casos de Sucesso', item: `${baseUrl}/casos` },
      { '@type': 'ListItem', position: 3, name: c.sector, item: `${baseUrl}/casos/${c.slug}` },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(reviewSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="mb-8">
          <ol className="flex items-center gap-2 text-sm text-ink-secondary">
            <li>
              <Link href="/" className="hover:text-brand-blue transition-colors">Home</Link>
            </li>
            <li aria-hidden="true">/</li>
            <li>
              <Link href="/casos" className="hover:text-brand-blue transition-colors">Casos</Link>
            </li>
            <li aria-hidden="true">/</li>
            <li className="text-ink font-medium truncate max-w-[200px]">{c.sector}</li>
          </ol>
        </nav>

        {/* Header */}
        <header className="mb-10">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-brand-blue-subtle text-brand-navy">
              {c.sector}
            </span>
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
              Score médio: {c.metrics.scoreMedio}/100
            </span>
            <span className="text-xs text-ink-muted">{c.uf}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold font-display text-ink leading-tight">
            {c.title}
          </h1>
          <p className="mt-3 text-ink-secondary">{c.companyProfile}</p>
        </header>

        {/* Metrics Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10 p-6 bg-surface border border-border rounded-card">
          <MetricCard label="Editais analisados" value={c.metrics.editaisAnalisados.toString()} />
          <MetricCard label="Valor identificado" value={c.metrics.valorIdentificado} />
          <MetricCard label="Tempo de análise" value={c.metrics.tempoAnalise} />
          <MetricCard label="Redução triagem" value={c.metrics.reducaoTriagem} />
        </div>

        {/* Problema */}
        <section className="mb-8">
          <h2 className="text-xl font-bold text-ink mb-3 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 flex items-center justify-center text-sm font-bold">1</span>
            O Problema
          </h2>
          <p className="text-ink-secondary leading-relaxed">{c.problem}</p>
        </section>

        {/* Processo */}
        <section className="mb-8">
          <h2 className="text-xl font-bold text-ink mb-3 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 flex items-center justify-center text-sm font-bold">2</span>
            O Processo
          </h2>
          <p className="text-ink-secondary leading-relaxed">{c.process}</p>
        </section>

        {/* CTA inline ~40% */}
        <BlogInlineCTA
          slug={c.slug}
          campaign="b2g"
          ctaHref={`/signup?ref=case-${c.slug}`}
          ctaText="Rode uma análise para o seu setor →"
          ctaMessage={`${c.company} encontrou ${c.metrics.valorIdentificado} em ${c.metrics.tempoAnalise}. Descubra o que está disponível para você.`}
        />

        {/* Resultado */}
        <section className="mb-8 mt-8">
          <h2 className="text-xl font-bold text-ink mb-3 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 flex items-center justify-center text-sm font-bold">3</span>
            O Resultado
          </h2>
          <p className="text-ink-secondary leading-relaxed">{c.result}</p>
        </section>

        {/* Editais perdidos highlight */}
        {c.metrics.editaisPerdidosSemFiltro > 0 && (
          <div className="p-4 bg-warning-subtle border border-warning/20 rounded-card mb-10">
            <p className="text-sm font-medium text-warning">
              Sem monitoramento automatizado, esta empresa estava perdendo em média{' '}
              <strong>{c.metrics.editaisPerdidosSemFiltro} editais compatíveis</strong> por período
              de análise — oportunidades que simplesmente passavam despercebidas.
            </p>
          </div>
        )}

        {/* Bottom CTA */}
        <div className="text-center p-8 bg-brand-blue-subtle border border-accent rounded-card">
          <h2 className="text-xl font-bold text-ink mb-3">
            Rode uma análise para o seu setor
          </h2>
          <p className="text-ink-secondary mb-6 max-w-lg mx-auto">
            14 dias grátis, sem cartão de crédito. Descubra quantos editais compatíveis
            estão abertos agora para a sua empresa.
          </p>
          <Link
            href={`/signup?ref=case-${c.slug}`}
            className="inline-flex items-center px-6 py-3 bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold rounded-button transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            Começar análise gratuita →
          </Link>
        </div>

        {/* Related links */}
        <div className="mt-10 flex flex-wrap gap-3">
          <Link
            href={`/licitacoes/${c.sectorSlug}`}
            className="text-sm text-brand-blue hover:underline"
          >
            Ver licitações de {c.sector} →
          </Link>
          <Link
            href={`/blog/licitacoes/${c.sectorSlug}/${c.uf.toLowerCase()}`}
            className="text-sm text-brand-blue hover:underline"
          >
            Panorama de {c.sector} em {c.uf} →
          </Link>
          <Link href="/casos" className="text-sm text-brand-blue hover:underline">
            Ver todos os casos →
          </Link>
          <Link href="/calculadora" className="text-sm text-brand-blue hover:underline">
            Calculadora de oportunidades →
          </Link>
        </div>
      </main>
    </>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <p className="text-lg sm:text-xl font-bold font-data text-brand-navy dark:text-brand-blue">
        {value}
      </p>
      <p className="text-xs text-ink-secondary mt-1">{label}</p>
    </div>
  );
}
