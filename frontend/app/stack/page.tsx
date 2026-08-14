import { Metadata } from 'next';
import Link from 'next/link';
import LandingNavbar from '../components/landing/LandingNavbar';
import Footer from '../components/Footer';
import { STACK_TOOLS, CATEGORY_LABELS, CATEGORY_COLORS } from '@/lib/stack-data';
import { buildCanonical, SITE_URL } from '@/lib/seo';

export const revalidate = 3600;

export const metadata: Metadata = {
  title: 'Tech Stack — SmartLic | Supabase, Next.js, FastAPI, Railway',
  description:
    'Conheça a stack tecnológica do SmartLic: Supabase, Railway, Next.js, FastAPI, Resend, OpenAI, Redis e Stripe. Métricas reais de produção de uma plataforma B2G SaaS.',
  alternates: { canonical: buildCanonical('/stack') },
  openGraph: {
    title: 'Tech Stack — SmartLic | Supabase, Next.js, FastAPI, Railway',
    description:
      'Stack completa de uma plataforma B2G SaaS em produção. 8 ferramentas com métricas reais.',
    type: 'website',
    url: buildCanonical('/stack'),
    siteName: 'SmartLic',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Tech Stack — SmartLic',
    description: 'Stack completa de uma plataforma B2G SaaS em produção com métricas reais.',
  },
};

export default function StackPage() {
  /* SoftwareApplication JSON-LD */
  const softwareLd = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'SmartLic',
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web',
    url: SITE_URL,
    description:
      'Plataforma de inteligência em licitações públicas com IA para classificação setorial e análise de viabilidade.',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'BRL',
      description: 'dado público verificável',
    },
  };

  /* HowTo JSON-LD */
  const howToLd = {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: 'Como construímos uma plataforma B2G SaaS',
    description:
      'Stack tecnológica completa para construir uma plataforma de inteligência em licitações públicas.',
    step: STACK_TOOLS.map((tool, i) => ({
      '@type': 'HowToStep',
      position: i + 1,
      name: `${CATEGORY_LABELS[tool.category]}: ${tool.name}`,
      text: tool.description,
      url: tool.url,
    })),
  };

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Tech Stack', item: buildCanonical('/stack') },
    ],
  };

  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-surface-0">
        {/* Hero */}
        <section className="bg-surface-1 border-b border-[var(--border)] py-16">
          <div className="mx-auto max-w-4xl px-4 text-center">
            <nav className="text-sm text-ink-muted mb-6">
              <Link href="/" className="hover:text-ink-primary transition-colors">Início</Link>
              <span className="mx-2">›</span>
              <span className="text-ink-primary">Tech Stack</span>
            </nav>
            <h1 className="text-4xl font-bold text-ink-primary">
              Tech Stack do SmartLic
            </h1>
            <p className="mt-4 text-lg text-ink-secondary max-w-2xl mx-auto">
              As {STACK_TOOLS.length} ferramentas que usamos para construir uma plataforma de
              inteligência em licitações com {'>'}7.000 páginas, 49 endpoints e classificação por IA —
              com métricas reais de produção.
            </p>
          </div>
        </section>

        {/* Stack grid */}
        <section className="mx-auto max-w-5xl px-4 py-12">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {STACK_TOOLS.map((tool) => (
              <div
                key={tool.id}
                className="p-6 rounded-xl border border-[var(--border)] hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold text-ink-primary">{tool.name}</h2>
                    <a
                      href={tool.url}
                      target="_blank"
                      rel="nofollow noopener noreferrer"
                      className="text-xs text-ink-muted hover:text-brand-blue transition-colors"
                      aria-label={`Site oficial do ${tool.name}`}
                    >
                      ↗
                    </a>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${CATEGORY_COLORS[tool.category]}`}>
                    {CATEGORY_LABELS[tool.category]}
                  </span>
                </div>
                <p className="text-sm text-ink-secondary mb-4">{tool.description}</p>
                <div className="flex flex-wrap gap-2">
                  {tool.metrics.map((m) => (
                    <div
                      key={m.label}
                      className="px-3 py-1.5 rounded-lg bg-surface-1 text-xs"
                    >
                      <span className="text-ink-muted">{m.label}:</span>{' '}
                      <span className="font-semibold text-ink-primary">{m.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Architecture summary */}
        <section className="mx-auto max-w-4xl px-4 py-8">
          <h2 className="text-2xl font-bold text-ink-primary mb-4">Por que essa stack?</h2>
          <div className="prose prose-lg max-w-none text-ink-secondary">
            <p>
              O SmartLic foi projetado para maximizar o tempo até o primeiro resultado útil.
              A combinação de <strong>Supabase</strong> (banco + auth + RLS em um produto) com{' '}
              <strong>Railway</strong> (deploy automático via GitHub push) e{' '}
              <strong>FastAPI + Next.js</strong> (tipagem ponta a ponta) permite que uma equipe
              enxuta opere uma plataforma com milhares de páginas e dezenas de endpoints.
            </p>
            <p>
              A classificação por IA via <strong>GPT-4.1-nano</strong> mantém custo abaixo de
              $0,01 por busca. O <strong>Redis</strong> absorve falhas de API upstream com circuit
              breaker e serve cache stale quando fontes de dados ficam indisponíveis. O{' '}
              <strong>Stripe</strong> elimina toda a complexidade de billing com webhook sync
              automático.
            </p>
          </div>
        </section>

        {/* Cross-links */}
        <section className="mx-auto max-w-4xl px-4 pb-12">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Link
              href="/sobre"
              className="p-4 rounded-xl border border-[var(--border)] hover:border-brand-blue/30 transition-colors text-center"
            >
              <p className="font-semibold text-ink-primary">Sobre o SmartLic</p>
              <p className="text-sm text-ink-muted mt-1">Metodologia e critérios</p>
            </Link>
            <Link
              href="/estatisticas"
              className="p-4 rounded-xl border border-[var(--border)] hover:border-brand-blue/30 transition-colors text-center"
            >
              <p className="font-semibold text-ink-primary">Estatísticas</p>
              <p className="text-sm text-ink-muted mt-1">Dados públicos das fontes oficiais</p>
            </Link>
            <Link
              href="/casos"
              className="p-4 rounded-xl border border-[var(--border)] hover:border-brand-blue/30 transition-colors text-center"
            >
              <p className="font-semibold text-ink-primary">Casos de Sucesso</p>
              <p className="text-sm text-ink-muted mt-1">Resultados reais de clientes</p>
            </Link>
          </div>

          {/* CTA */}
          <div className="mt-12 rounded-2xl bg-brand-blue p-8 text-center text-white">
            <h2 className="text-2xl font-bold">Veja a stack em ação</h2>
            <p className="mt-2 text-blue-100 max-w-lg mx-auto">
              Teste o SmartLic gratuitamente e veja como essa stack entrega resultados em segundos.
            </p>
            <Link
              href="/consultoria-b2g?source=stack"
              className="mt-6 inline-block rounded-lg bg-white text-brand-blue font-semibold px-6 py-3 hover:bg-blue-50 transition-colors"
            >
              dado público verificável →
            </Link>
          </div>
        </section>

        {/* JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareLd) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(howToLd) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }} />
      </main>
      <Footer />
    </>
  );
}
