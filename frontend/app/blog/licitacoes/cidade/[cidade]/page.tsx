import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import SchemaMarkup from '@/components/blog/SchemaMarkup';
import BlogCTA from '@/components/blog/BlogCTA';
import BreadcrumbNav from '@/components/seo/BreadcrumbNav';
import HistoricalContractsFallback from '@/components/blog/HistoricalContractsFallback';
import { CITIES, getCityBySlug, fetchCidadeStats, getCitiesByUf } from '@/lib/cities';
import { UF_NAMES, formatBRL } from '@/lib/programmatic';
import {
  fetchContratosCidadeStats,
  buildContractsContext,
  generateCidadeFAQsWithFallback,
} from '@/lib/contracts-fallback';
import { SECTORS } from '@/lib/sectors';

/**
 * SEO Frente 4: City programmatic SEO pages.
 *
 * Route: /blog/licitacoes/cidade/{cidade}
 * ISR 24h. One page per city listed in `lib/cities.ts`.
 *
 * Renders gracefully when the backend endpoint returns 404 or fails:
 * displays a generic fallback and lets the build succeed.
 */

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return CITIES.map((c) => ({ cidade: c.slug }));
}

function getMonthYear(): string {
  const now = new Date();
  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ];
  return `${months[now.getMonth()]} ${now.getFullYear()}`;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ cidade: string }>;
}): Promise<Metadata> {
  const { cidade } = await params;
  const city = getCityBySlug(cidade);
  if (!city) return { title: 'Cidade não encontrada | SmartLic' };

  const stats = await fetchCidadeStats(city.slug);
  const total = stats?.total_editais ?? 0;
  const ufName = UF_NAMES[city.uf] || city.uf;
  const year = new Date().getFullYear();
  const canonicalUrl = `https://smartlic.tech/blog/licitacoes/cidade/${city.slug}`;

  const title = `Licitações em ${city.name}/${city.uf}${
    total > 0 ? ` — ${total} editais abertos ${year}` : ` — Editais ${year}`
  } | SmartLic`;
  const description =
    `Encontre licitações abertas em ${city.name} (${ufName}). ` +
    `${total > 0 ? `${total} editais ativos nos últimos 10 dias. ` : ''}` +
    `Dados consolidados de PNCP, PCP e ComprasGov. Filtre por modalidade, valor e prazo. Teste grátis.`;

  return {
    title,
    description,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title,
      description,
      url: canonicalUrl,
      type: 'article',
      locale: 'pt_BR',
    },
    twitter: {
      card: 'summary_large_image',
      title: `Licitações em ${city.name}/${city.uf} | SmartLic`,
      description,
    },
  };
}

export default async function LicitacoesCidadePage({
  params,
}: {
  params: Promise<{ cidade: string }>;
}) {
  const { cidade } = await params;
  const city = getCityBySlug(cidade);
  if (!city) notFound();

  const stats = await fetchCidadeStats(city.slug);
  const ufName = UF_NAMES[city.uf] || city.uf;
  const monthYear = getMonthYear();
  const url = `https://smartlic.tech/blog/licitacoes/cidade/${city.slug}`;
  const total = stats?.total_editais ?? 0;
  const hasData = !!stats && total > 0;

  const breadcrumbs = [
    { label: 'Início', href: '/' },
    { label: 'Blog', href: '/blog' },
    { label: 'Licitações', href: '/blog/licitacoes' },
    { label: `${city.name}/${city.uf}` },
  ];

  // Schema breadcrumbs (absolute URLs, expected by SchemaMarkup)
  const schemaBreadcrumbs = [
    { name: 'SmartLic', url: 'https://smartlic.tech' },
    { name: 'Blog', url: 'https://smartlic.tech/blog' },
    { name: 'Licitações', url: 'https://smartlic.tech/blog/licitacoes' },
    { name: `${city.name}/${city.uf}`, url },
  ];

  // Zero-state fallback: when there are no open editais, fetch historical
  // contract activity (all sectors) for this city from pncp_supplier_contracts.
  const hasZeroEditais = total === 0;
  const contractsFallback = hasZeroEditais
    ? await fetchContratosCidadeStats(city.slug)
    : null;
  const contractsContext = buildContractsContext(contractsFallback);

  const liveTopOrgaos = stats?.orgaos_frequentes?.map((o) => o.name);
  const faqs = generateCidadeFAQsWithFallback(
    city.name,
    city.uf,
    stats?.total_editais,
    stats?.avg_value,
    contractsContext,
    liveTopOrgaos,
  );

  const nearbyCities = getCitiesByUf(city.uf).filter((c) => c.slug !== city.slug);

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <SchemaMarkup
        pageType="cidade"
        title={`Licitações em ${city.name}/${city.uf} — ${monthYear}`}
        description={`${total} licitações públicas em ${city.name} (${ufName}) — dados consolidados de PNCP, PCP e ComprasGov.`}
        url={url}
        sectorName={`Licitações em ${city.name}`}
        uf={city.uf}
        cidade={city.name}
        totalEditais={total}
        avgValue={stats?.avg_value}
        breadcrumbs={schemaBreadcrumbs}
        faqs={faqs}
        dataPoints={[
          { name: 'Total de Editais', value: total },
          { name: 'Valor Médio', value: stats?.avg_value ?? 0 },
          { name: 'Órgãos Compradores Ativos', value: stats?.orgaos_frequentes.length ?? 0 },
        ]}
      />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
            <BreadcrumbNav items={breadcrumbs} className="mb-6" suppressSchema />

            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              Licitações em {city.name}/{city.uf} — {monthYear}
            </h1>

            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              {hasData
                ? `${total} editais publicados em ${city.name} nos últimos 10 dias.`
                : `Acompanhe em tempo real as licitações públicas de ${city.name} (${ufName}).`}
              {stats && stats.avg_value > 0
                ? ` Valor médio estimado: ${formatBRL(stats.avg_value)}.`
                : ''}
            </p>

            {stats && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <p className="inline-flex items-center gap-2 text-sm text-ink-secondary bg-surface-2 px-3 py-1 rounded-full">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  Dados atualizados em {new Date(stats.last_updated).toLocaleDateString('pt-BR')}
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* Stats grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-10">
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Editais Abertos</p>
              <p className="text-2xl font-bold text-ink">{total}</p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Valor Médio</p>
              <p className="text-2xl font-bold text-ink">{formatBRL(stats?.avg_value ?? 0)}</p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">UF</p>
              <p className="text-2xl font-bold text-ink">{city.uf}</p>
            </div>
          </div>

          {/* Top buying orgs */}
          {stats && stats.orgaos_frequentes.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Órgãos que mais publicam licitações em {city.name}
              </h2>
              <div className="space-y-3">
                {stats.orgaos_frequentes.map((org) => (
                  <div
                    key={org.name}
                    className="flex items-center justify-between p-4 rounded-lg border border-[var(--border)] hover:bg-surface-1 transition-colors"
                  >
                    <span className="text-ink font-medium line-clamp-1">{org.name}</span>
                    <span className="text-sm text-ink-secondary shrink-0 ml-3">
                      {org.count} {org.count === 1 ? 'edital' : 'editais'}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Inline CTA */}
          <BlogCTA
            variant="inline"
            setor="Licitações públicas"
            uf={ufName}
            count={total}
            slug={`cidade-${city.slug}`}
          />

          {/* Editorial block */}
          <section className="mb-10 mt-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Panorama das licitações em {city.name}
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>
                {city.name} é um dos municípios de {ufName} com presença ativa em licitações públicas.
                Todo edital publicado por prefeitura, secretarias e autarquias locais é registrado no
                Portal Nacional de Contratações Públicas (PNCP), garantindo transparência e acesso
                democrático às oportunidades B2G.
              </p>
              <p>
                Empresas de qualquer porte podem participar — MEIs, pequenas e médias empresas têm
                benefícios legais previstos pela Lei Complementar 123/2006, incluindo cota reservada
                de até 25% em itens de compra específicos. A Lei 14.133/2021 ainda reforça preferências
                para fornecedores locais em contratações municipais, o que torna {city.name} um mercado
                estratégico para fornecedores sediados em {ufName}.
              </p>
              <p>
                No SmartLic você filtra editais em tempo real por setor, valor, modalidade e prazo de
                abertura. A plataforma usa inteligência artificial (GPT-4.1-nano) para classificar a
                relevância setorial e calcula um score de viabilidade de 4 fatores — modalidade, prazo,
                valor e geografia — ajudando a priorizar apenas as oportunidades onde sua empresa tem
                chances reais de ganhar.
              </p>
              {!hasData && !contractsFallback && (
                <p className="text-ink-muted italic">
                  No momento não identificamos editais ativos para {city.name} nos últimos 10 dias.
                  Esse número oscila diariamente — cadastre-se para receber alertas automáticos.
                </p>
              )}
            </div>
          </section>

          {/* Zero-editais fallback: historical contract activity (all sectors) */}
          {hasZeroEditais && contractsFallback && contractsFallback.total_contracts > 0 && (
            <HistoricalContractsFallback
              scope="cidade"
              cityName={city.name}
              data={contractsFallback}
              ctaSlug={`cidade-${city.slug}`}
            />
          )}

          {/* Explore by sector in city */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Explore por setor em {city.name}
            </h2>
            <div className="flex flex-wrap gap-2">
              {SECTORS.map((sector) => (
                <Link
                  key={sector.slug}
                  href={`/blog/licitacoes/cidade/${city.slug}/${sector.slug}`}
                  className="inline-flex items-center px-3 py-1.5 rounded-full border border-[var(--border)] text-sm text-ink-secondary hover:bg-surface-1 hover:text-ink transition-colors"
                >
                  {sector.name} em {city.name}
                </Link>
              ))}
            </div>
          </section>

          {/* Nearby cities in same UF */}
          {nearbyCities.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Outras cidades em {ufName}
              </h2>
              <div className="flex flex-wrap gap-2">
                {nearbyCities.map((c) => (
                  <Link
                    key={c.slug}
                    href={`/blog/licitacoes/cidade/${c.slug}`}
                    className="inline-flex items-center px-3 py-1.5 rounded-full border border-[var(--border)] text-sm text-ink-secondary hover:bg-surface-1 hover:text-ink transition-colors"
                  >
                    {c.name}
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* FAQ */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">Perguntas frequentes</h2>
            <div className="space-y-4">
              {faqs.map((faq, i) => (
                <details key={i} className="group border border-[var(--border)] rounded-lg">
                  <summary className="flex items-center justify-between p-4 cursor-pointer font-medium text-ink hover:bg-surface-1 rounded-lg transition-colors">
                    {faq.question}
                    <span className="text-ink-secondary group-open:rotate-180 transition-transform">
                      &#x25BE;
                    </span>
                  </summary>
                  <p className="px-4 pb-4 text-ink-secondary leading-relaxed">{faq.answer}</p>
                </details>
              ))}
            </div>
          </section>

          {/* Final CTA */}
          <BlogCTA
            variant="final"
            setor="Licitações públicas"
            uf={ufName}
            count={total}
            slug={`cidade-${city.slug}`}
          />
        </div>
      </main>

      <Footer />
    </div>
  );
}
