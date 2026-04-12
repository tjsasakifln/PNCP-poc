import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  generateSectorUfParams,
  getSectorFromSlug,
  fetchAlertasPublicos,
  formatBRL,
  getUfPrep,
  ALL_UFS,
  UF_NAMES,
} from '@/lib/programmatic';
import { buildCanonical, getFreshnessLabel } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';


export const revalidate = 3600; // 1h ISR

export function generateStaticParams() {
  return generateSectorUfParams();
}

type Props = { params: Promise<{ setor: string; uf: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { setor, uf } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) return {};
  const ufUpper = uf.toUpperCase();
  const ufName = UF_NAMES[ufUpper] || ufUpper;
  const now = new Date();
  const month = now.toLocaleString('pt-BR', { month: 'long' });
  const year = now.getFullYear();

  // STORY-430 AC2: checar contagem de editais para noindex dinâmico
  const minBids = parseInt(process.env.MIN_ACTIVE_BIDS_FOR_INDEX ?? '5', 10);
  const data = await fetchAlertasPublicos(setor, ufUpper);
  const total = data?.total ?? (data?.bids?.length ?? 0);

  if (total < minBids) {
    return {
      title: `Alertas de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
      description: `Alertas de licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}. Dados do PNCP atualizados a cada hora.`,
      robots: { index: false, follow: false },
      // SEO-440: canonical self-referencial evita herdar o canonical da homepage (layout.tsx)
      alternates: { canonical: buildCanonical(`/alertas-publicos/${setor}/${uf}`) },
    };
  }

  return {
    title: `Alertas de Licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} — ${month.charAt(0).toUpperCase() + month.slice(1)} ${year}`,
    description: `Acompanhe as licitações mais recentes de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}. Dados atualizados do PNCP. Feed RSS disponível.`,
    alternates: {
      canonical: buildCanonical(`/alertas-publicos/${setor}/${uf}`),
      types: {
        'application/rss+xml': `/alertas-publicos/${setor}/${uf}/rss.xml`,
      },
    },
    openGraph: {
      title: `Alertas: ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
      description: `Licitações recentes de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} — dados ao vivo do PNCP`,
      type: 'website',
      locale: 'pt_BR',
    },
    robots: { index: true, follow: true },
  };
}

export default async function AlertasPage({ params }: Props) {
  const { setor, uf } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) notFound();

  const ufUpper = uf.toUpperCase();
  if (!ALL_UFS.includes(ufUpper)) notFound();

  const ufName = UF_NAMES[ufUpper] || ufUpper;
  const data = await fetchAlertasPublicos(setor, ufUpper);
  const bids = data?.bids || [];
  const freshness = data?.last_updated ? getFreshnessLabel(data.last_updated) : '';

  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Alertas Públicos', url: '/alertas-publicos' },
    { name: sector.name, url: `/alertas-publicos/${setor}/${uf}` },
    { name: ufName, url: `/alertas-publicos/${setor}/${uf}` },
  ];

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'DataFeed',
    name: `Alertas de Licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
    description: `Licitações recentes de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} — dados ao vivo do PNCP`,
    url: `https://smartlic.tech/alertas-publicos/${setor}/${uf}`,
    dateModified: data?.last_updated || new Date().toISOString(),
    provider: { '@type': 'Organization', name: 'SmartLic', url: 'https://smartlic.tech' },
  };

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: breadcrumbs.map((item, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: item.name,
      item: `https://smartlic.tech${item.url}`,
    })),
  };

  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-surface-0">
        {/* JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }} />

        {/* Hero */}
        <section className="bg-gradient-to-br from-brand-navy to-brand-blue text-white py-12 px-4">
          <div className="max-w-5xl mx-auto">
            {/* Breadcrumb */}
            <nav className="text-sm text-white/60 mb-4">
              {breadcrumbs.map((item, i) => (
                <span key={i}>
                  {i > 0 && ' › '}
                  {i < breadcrumbs.length - 1 ? (
                    <Link href={item.url} className="hover:text-white/80">{item.name}</Link>
                  ) : (
                    <span className="text-white/80">{item.name}</span>
                  )}
                </span>
              ))}
            </nav>
            <h1 className="text-3xl sm:text-4xl font-bold mb-3">
              {bids.length > 0
                ? `${data?.total || bids.length} licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`
                : `Alertas de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`
              }
            </h1>
            <p className="text-white/80 text-lg mb-4">
              Editais publicados nos últimos 10 dias no PNCP. Atualizado a cada hora.
            </p>
            <div className="flex flex-wrap gap-4 items-center">
              {freshness && (
                <span className="text-sm bg-white/10 px-3 py-1 rounded-full">{freshness}</span>
              )}
              <Link
                href={`/alertas-publicos/${setor}/${uf}/rss.xml`}
                className="text-sm bg-orange-500/20 text-orange-200 px-3 py-1 rounded-full hover:bg-orange-500/30"
              >
                RSS Feed →
              </Link>
            </div>
          </div>
        </section>

        {/* Bid listing */}
        <section className="max-w-5xl mx-auto py-10 px-4">
          {bids.length === 0 ? (
            <div className="text-center py-16 bg-yellow-50 dark:bg-yellow-900/10 rounded-xl border border-yellow-200 dark:border-yellow-800">
              <p className="text-yellow-800 dark:text-yellow-200 font-medium mb-2">
                Nenhuma licitação de {sector.name} publicada {getUfPrep(ufUpper)} {ufName} nos últimos 10 dias.
              </p>
              <p className="text-sm text-yellow-600 dark:text-yellow-400">
                Volte em breve — novos editais são publicados diariamente no PNCP.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {bids.map((bid, i) => (
                <article
                  key={bid.pncp_id || i}
                  className="p-5 rounded-xl border border-border bg-surface-1 hover:shadow-md transition-shadow"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-3">
                    <h2 className="text-base font-semibold text-ink leading-snug max-w-2xl">
                      {bid.titulo}
                    </h2>
                    {bid.valor != null && bid.valor > 0 && (
                      <span className="text-brand-blue font-bold whitespace-nowrap">
                        {formatBRL(bid.valor)}
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-secondary">
                    <span>{bid.orgao}</span>
                    {bid.municipio && <span>{bid.municipio}</span>}
                    {bid.modalidade && (
                      <span className="bg-surface-0 px-2 py-0.5 rounded text-xs font-medium">
                        {bid.modalidade}
                      </span>
                    )}
                    <span>{bid.data_publicacao}</span>
                    {bid.data_abertura && (
                      <span className="text-orange-600 dark:text-orange-400">
                        Abertura: {bid.data_abertura}
                      </span>
                    )}
                  </div>
                  {bid.link_pncp && (
                    <a
                      href={bid.link_pncp}
                      target="_blank"
                      rel="nofollow noopener noreferrer"
                      className="inline-block mt-2 text-sm text-brand-blue hover:underline"
                    >
                      Ver no PNCP →
                    </a>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        {/* CTA */}
        <section className="max-w-5xl mx-auto py-8 px-4">
          <div className="rounded-2xl bg-gradient-to-br from-brand-navy to-brand-blue p-8 sm:p-12 text-center text-white">
            <h3 className="text-2xl font-bold mb-3">
              Filtre e analise todas as licitações de {sector.name}
            </h3>
            <p className="text-white/80 mb-6">
              Score de viabilidade, alertas por email, exportação Excel. 14 dias grátis.
            </p>
            <Link
              href={`/signup?ref=alertas-${setor}-${uf}`}
              className="inline-block px-8 py-4 bg-white text-brand-navy font-bold rounded-xl hover:bg-gray-100 transition-colors text-lg shadow-lg"
            >
              Analisar Oportunidades →
            </Link>
          </div>
        </section>

        {/* Cross-links */}
        <section className="max-w-5xl mx-auto py-8 px-4">
          <h3 className="text-lg font-bold text-ink mb-4">
            Mais sobre {sector.name} {getUfPrep(ufUpper)} {ufName}
          </h3>
          <div className="flex flex-wrap gap-3">
            <Link
              href={`/blog/licitacoes/${setor}/${uf}`}
              className="px-4 py-2 text-sm rounded-lg border border-border hover:border-brand-blue transition-colors"
            >
              Análise de mercado →
            </Link>
            <Link
              href={`/licitacoes/${setor}`}
              className="px-4 py-2 text-sm rounded-lg border border-border hover:border-brand-blue transition-colors"
            >
              Landing {sector.name} →
            </Link>
            <Link
              href={`/calculadora?setor=${setor}&uf=${uf}`}
              className="px-4 py-2 text-sm rounded-lg border border-border hover:border-brand-blue transition-colors"
            >
              Calculadora B2G →
            </Link>
          </div>
        </section>

        <Footer />
      </main>
    </>
  );
}
