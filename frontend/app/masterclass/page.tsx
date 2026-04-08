import { Metadata } from 'next';
import Link from 'next/link';
import { MASTERCLASSES } from '@/lib/masterclasses';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const revalidate = 86400; // ISR 24h

const PAGE_TITLE = 'Masterclasses Gratuitas sobre Licitações Públicas | SmartLic';
const PAGE_DESCRIPTION =
  'Série gratuita de masterclasses práticas sobre licitações públicas: como participar do seu primeiro edital, análise de viabilidade e inteligência setorial com dados do PNCP.';
const PAGE_URL = buildCanonical('/masterclass');

export const metadata: Metadata = {
  title: PAGE_TITLE,
  description: PAGE_DESCRIPTION,
  alternates: { canonical: PAGE_URL },
  openGraph: {
    title: PAGE_TITLE,
    description: PAGE_DESCRIPTION,
    url: PAGE_URL,
    type: 'website',
    siteName: 'SmartLic',
    images: [{ url: `${SITE_URL}/api/og?title=Masterclasses+Gratuitas&subtitle=Licitações+Públicas`, width: 1200, height: 630, alt: PAGE_TITLE }],
  },
  twitter: { card: 'summary_large_image', title: PAGE_TITLE, description: PAGE_DESCRIPTION },
};

const LEVEL_LABEL: Record<string, string> = {
  iniciante: 'Iniciante',
  intermediario: 'Intermediário',
  avancado: 'Avançado',
};

const LEVEL_COLOR: Record<string, string> = {
  iniciante: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  intermediario: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  avancado: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
};

export default function MasterclassListPage() {
  const itemListLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: 'Masterclasses Gratuitas sobre Licitações Públicas',
    description: PAGE_DESCRIPTION,
    url: PAGE_URL,
    numberOfItems: MASTERCLASSES.length,
    itemListElement: MASTERCLASSES.map((mc, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: buildCanonical(`/masterclass/${mc.tema}`),
      name: mc.title,
    })),
  };

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Início', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Masterclasses', item: PAGE_URL },
    ],
  };

  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-surface-0">
        {/* Hero */}
        <section className="bg-gradient-to-b from-brand-blue/5 to-surface-0 border-b border-[var(--border)] py-16">
          <div className="mx-auto max-w-4xl px-4 text-center">
            <nav className="text-sm text-ink-muted mb-6 flex items-center justify-center gap-2">
              <Link href="/" className="hover:text-ink-primary transition-colors">Início</Link>
              <span>›</span>
              <span className="text-ink-primary">Masterclasses</span>
            </nav>
            <div className="inline-flex items-center gap-2 rounded-full bg-brand-blue/10 px-4 py-1.5 text-sm font-medium text-brand-blue mb-4">
              Gratuito · Sem cartão
            </div>
            <h1 className="text-4xl font-bold text-ink-primary leading-tight">
              Masterclasses sobre Licitações Públicas
            </h1>
            <p className="mt-4 text-lg text-ink-secondary max-w-2xl mx-auto leading-relaxed">
              Série gratuita de aulas práticas para empresas B2G. Do primeiro edital à inteligência
              de mercado — aprenda com quem construiu uma plataforma de análise de licitações.
            </p>
            <p className="mt-3 text-sm text-ink-muted">
              {MASTERCLASSES.length} masterclasses disponíveis &middot;{' '}
              {MASTERCLASSES.reduce((acc, mc) => acc + mc.durationMinutes, 0)} minutos de conteúdo
            </p>
          </div>
        </section>

        {/* Grid */}
        <section className="mx-auto max-w-4xl px-4 py-14">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {MASTERCLASSES.map((mc) => (
              <Link
                key={mc.tema}
                href={`/masterclass/${mc.tema}`}
                className="group flex flex-col rounded-2xl border border-[var(--border)] bg-surface-1 p-6 hover:border-brand-blue/40 hover:shadow-md transition-all"
              >
                {/* Level + Duration */}
                <div className="flex items-center justify-between mb-4">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${LEVEL_COLOR[mc.level]}`}>
                    {LEVEL_LABEL[mc.level]}
                  </span>
                  <span className="text-xs text-ink-muted">{mc.durationMinutes} min</span>
                </div>

                {/* Title */}
                <h2 className="text-base font-bold text-ink-primary leading-snug group-hover:text-brand-blue transition-colors flex-1">
                  {mc.title}
                </h2>

                {/* Description */}
                <p className="mt-3 text-sm text-ink-secondary line-clamp-3 leading-relaxed">
                  {mc.description}
                </p>

                {/* Topics count */}
                <div className="mt-4 pt-4 border-t border-[var(--border)] flex items-center justify-between">
                  <span className="text-xs text-ink-muted">{mc.topics.length} tópicos</span>
                  <span className="text-xs font-semibold text-brand-blue group-hover:translate-x-1 transition-transform inline-block">
                    Assistir grátis →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-4xl px-4 pb-16">
          <div className="rounded-2xl bg-brand-blue p-8 sm:p-12 text-center text-white">
            <h2 className="text-2xl sm:text-3xl font-bold">
              Aplique o que aprendeu na prática
            </h2>
            <p className="mt-3 text-blue-100 max-w-lg mx-auto leading-relaxed">
              O SmartLic analisa automaticamente a viabilidade de cada edital para o seu setor —
              14 dias grátis, sem cartão de crédito.
            </p>
            <Link
              href="/signup?source=masterclass-listing"
              className="mt-6 inline-block rounded-lg bg-white text-brand-blue font-bold px-8 py-3 hover:bg-blue-50 transition-colors"
            >
              Começar gratuitamente →
            </Link>
          </div>
        </section>

        {/* JSON-LD */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(itemListLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }}
        />
      </main>
      <Footer />
    </>
  );
}
