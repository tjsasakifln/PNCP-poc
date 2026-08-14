import { Metadata } from 'next';
import Link from 'next/link';
import { getAllCases } from '@/lib/cases';

const baseUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';

export const metadata: Metadata = {
  title: 'Casos de Sucesso em Licitações — Empresas Reais, Números Reais',
  description:
    'Veja como empresas B2G identificaram milhões em contratos públicos usando análise de viabilidade inteligente. Dados reais de engenharia, saúde e infraestrutura.',
  keywords: [
    'caso de sucesso licitação',
    'empresas que ganham licitações',
    'análise de viabilidade licitação',
    'como encontrar editais',
    'filtro inteligente licitações',
  ],
  alternates: { canonical: `${baseUrl}/casos` },
  openGraph: {
    title: 'Casos de Sucesso em Licitações | SmartLic',
    description:
      'Empresas reais. Números reais. Veja como análise de viabilidade inteligente transforma triagem de editais.',
    url: `${baseUrl}/casos`,
    type: 'website',
    locale: 'pt_BR',
    images: [{ url: `${baseUrl}/api/og?title=Casos+de+Sucesso&category=B2G`, width: 1200, height: 630 }],
  },
  twitter: { card: 'summary_large_image' },
};

const SECTOR_ICONS: Record<string, string> = {
  engenharia: '🏗️',
  saude: '🏥',
  informatica: '💻',
};

export default function CasosPage() {
  const cases = getAllCases();

  const itemListSchema = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: 'Casos de Sucesso SmartLic',
    description: 'Casos reais de empresas B2G que usaram análise de viabilidade para identificar oportunidades em licitações.',
    numberOfItems: cases.length,
    itemListElement: cases.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: `${baseUrl}/casos/${c.slug}`,
      name: c.title,
    })),
  };

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: baseUrl },
      { '@type': 'ListItem', position: 2, name: 'Casos de Sucesso', item: `${baseUrl}/casos` },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(itemListSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="mb-8">
          <ol className="flex items-center gap-2 text-sm text-ink-secondary">
            <li><Link href="/" className="hover:text-brand-blue transition-colors">Home</Link></li>
            <li aria-hidden="true">/</li>
            <li className="text-ink font-medium">Casos de Sucesso</li>
          </ol>
        </nav>

        {/* Hero */}
        <div className="mb-12">
          <h1 className="text-3xl sm:text-4xl font-bold font-display text-ink mb-4">
            Casos de Sucesso
          </h1>
          <p className="text-lg text-ink-secondary max-w-2xl">
            Empresas reais que usaram análise de viabilidade inteligente para encontrar
            contratos públicos compatíveis. Números verificados, resultados documentados.
          </p>
        </div>

        {/* Case Grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {cases.map((c) => (
            <Link
              key={c.slug}
              href={`/casos/${c.slug}`}
              className="group block p-6 bg-surface border border-border rounded-card hover:border-accent hover:shadow-md transition-all"
            >
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl" aria-hidden="true">
                  {SECTOR_ICONS[c.sectorSlug] || '📊'}
                </span>
                <span className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">
                  {c.sector}
                </span>
              </div>

              <h2 className="text-base font-semibold text-ink group-hover:text-brand-blue transition-colors mb-3 line-clamp-3">
                {c.title}
              </h2>

              <div className="flex flex-wrap gap-2 mb-4">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-brand-blue-subtle text-brand-navy">
                  {c.uf}
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                  Score {c.metrics.scoreMedio}/100
                </span>
              </div>

              <div className="space-y-1 text-sm text-ink-secondary">
                <p>
                  <span className="font-semibold text-brand-navy dark:text-brand-blue">
                    {c.metrics.valorIdentificado}
                  </span>{' '}
                  em oportunidades
                </p>
                <p>{c.metrics.editaisAnalisados} editais analisados em {c.metrics.tempoAnalise}</p>
                <p>Triagem: {c.metrics.reducaoTriagem}</p>
              </div>

              <span className="inline-block mt-4 text-sm font-medium text-brand-blue group-hover:underline">
                Ver caso completo →
              </span>
            </Link>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center p-8 bg-brand-blue-subtle border border-accent rounded-card">
          <h2 className="text-xl sm:text-2xl font-bold text-ink mb-3">
            Rode uma análise para o seu setor
          </h2>
          <p className="text-ink-secondary mb-6 max-w-lg mx-auto">
            sem login, dado verificável. Descubra quantos editais compatíveis
            estão abertos agora para a sua empresa.
          </p>
          <Link
            href="/consultoria-b2g?ref=casos-page"
            className="inline-flex items-center px-6 py-3 bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold rounded-button transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            Começar análise gratuita →
          </Link>
        </div>
      </main>
    </>
  );
}
