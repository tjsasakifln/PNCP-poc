import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import LandingNavbar from '../../../components/landing/LandingNavbar';
import Footer from '../../../components/Footer';
import SchemaMarkup from '@/components/blog/SchemaMarkup';
import BlogCTA from '@/components/blog/BlogCTA';
import RelatedPages from '@/components/blog/RelatedPages';
import {
  generateSectorParams,
  fetchPanoramaStats,
  getSectorFromSlug,
  formatBRL,
  getEditorialContent,
  generatePanoramaFAQs,
  getPanoramaEditorial,
  ALL_UFS,
  UF_NAMES,
} from '@/lib/programmatic';
import { SECTORS } from '@/lib/sectors';

/**
 * MKT-004: Panorama por Setor — 15 pillar pages.
 *
 * Route: /blog/panorama/{setor}
 * ISR 24h. Data-journalism with national aggregate data.
 * 2,500-3,000 words per page (editorial + data).
 * Schema: FAQPage + Dataset + Article + HowTo.
 */

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return generateSectorParams(); // 15 sectors
}

const year = new Date().getFullYear();

export async function generateMetadata({
  params,
}: {
  params: Promise<{ setor: string }>;
}): Promise<Metadata> {
  const { setor } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) return { title: 'Setor não encontrado' };

  const stats = await fetchPanoramaStats(setor);
  const total = stats?.total_nacional ?? 0;
  const canonicalUrl = `https://smartlic.tech/blog/panorama/${setor}`;

  return {
    title: `Panorama de Licitações de ${sector.name} no Brasil — ${year}`,
    description: `${total > 0 ? `${total} editais` : 'Editais'} de ${sector.name} publicados nos últimos 90 dias. Dados nacionais ao vivo: sazonalidade, ranking por UF, modalidades e tendência YoY.`,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: `Panorama de Licitações de ${sector.name} — ${year} | SmartLic`,
      description: `Dados exclusivos: ${total > 0 ? total : ''} editais, sazonalidade, top UFs e crescimento YoY para ${sector.name}.`,
      url: canonicalUrl,
      type: 'article',
      locale: 'pt_BR',
      siteName: 'SmartLic',
    },
    twitter: {
      card: 'summary_large_image',
      title: `Panorama de Licitações de ${sector.name} — ${year} | SmartLic`,
      description: `Dados nacionais de licitações de ${sector.name}: volume, sazonalidade e tendências.`,
    },
  };
}

/** Phase 1 sectors × UFs that have /blog/licitacoes/ pages */
const LICITACOES_SECTORS = ['informatica', 'saude', 'engenharia', 'facilities', 'software'];
const LICITACOES_UFS = ['SP', 'RJ', 'MG', 'PR', 'RS'];

function getUfPageHref(sectorSlug: string, sectorId: string, uf: string): string {
  if (LICITACOES_SECTORS.includes(sectorId) && LICITACOES_UFS.includes(uf)) {
    return `/blog/licitacoes/${sectorSlug}/${uf.toLowerCase()}`;
  }
  return `/blog/programmatic/${sectorSlug}/${uf.toLowerCase()}`;
}

export default async function PanoramaSectorPage({
  params,
}: {
  params: Promise<{ setor: string }>;
}) {
  const { setor } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) notFound();

  const stats = await fetchPanoramaStats(setor);
  const editorial = getEditorialContent(sector.id);
  const panoramaEditorial = getPanoramaEditorial(sector.id, sector.name);
  const faqs = generatePanoramaFAQs(
    sector.name,
    stats?.total_nacional,
    stats?.crescimento_estimado_pct,
    stats?.top_ufs?.[0]?.name ? UF_NAMES[stats.top_ufs[0].name] || stats.top_ufs[0].name : undefined,
    stats?.avg_value,
  );
  const slug = `panorama/${setor}`;
  const url = `https://smartlic.tech/blog/${slug}`;

  // Calculate totals for percentage display
  const totalUfCount = stats?.top_ufs?.reduce((s, u) => s + u.count, 0) ?? 0;
  const totalModCount = stats?.top_modalidades?.reduce((s, m) => s + m.count, 0) ?? 0;

  // Related panoramas (3 sectors)
  const relatedSectors = SECTORS.filter((s) => s.id !== sector.id).slice(0, 3);

  const breadcrumbs = [
    { name: 'SmartLic', url: 'https://smartlic.tech' },
    { name: 'Blog', url: 'https://smartlic.tech/blog' },
    { name: 'Panorama', url: 'https://smartlic.tech/blog/panorama' },
    { name: sector.name, url },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <SchemaMarkup
        pageType="panorama"
        title={`Panorama de Licitações de ${sector.name} no Brasil — ${year}`}
        description={`${stats?.total_nacional ?? 0} licitações de ${sector.name} publicadas no Brasil`}
        url={url}
        sectorName={sector.name}
        totalEditais={stats?.total_nacional}
        breadcrumbs={breadcrumbs}
        faqs={faqs}
        dataPoints={[
          { name: 'Total Nacional (90 dias)', value: stats?.total_nacional ?? 0 },
          { name: 'Valor Total Estimado', value: stats?.total_value ?? 0 },
          { name: 'Valor Médio', value: stats?.avg_value ?? 0 },
          { name: 'Crescimento YoY', value: `${stats?.crescimento_estimado_pct ?? 0}%` },
        ]}
      />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
            <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6">
              <Link href="/blog" className="hover:text-brand-blue">Blog</Link>
              <span>/</span>
              <span className="text-ink">Panorama</span>
              <span>/</span>
              <span className="text-ink">{sector.name}</span>
            </nav>

            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4 font-serif"
            >
              Panorama de Licitações de {sector.name} no Brasil — {year}
            </h1>

            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              {stats?.total_nacional
                ? `${stats.total_nacional} editais publicados nos últimos 90 dias, com valor total estimado de ${formatBRL(stats.total_value)}.`
                : `Dados nacionais consolidados de licitações de ${sector.name} no Brasil.`}
              {' '}Dados exclusivos do PNCP, Portal de Compras Públicas e ComprasGov.
            </p>

            {stats && (
              <p className="mt-3 inline-flex items-center gap-2 text-sm text-ink-secondary bg-surface-2 px-3 py-1 rounded-full">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                Atualizado em {new Date(stats.last_updated).toLocaleDateString('pt-BR')}
              </p>
            )}
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* AC2: Stats Grid — total, valor, média, crescimento */}
          {stats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
              <StatCard label="Editais (90 dias)" value={stats.total_nacional.toLocaleString('pt-BR')} />
              <StatCard label="Valor Total" value={formatBRL(stats.total_value)} />
              <StatCard label="Valor Médio" value={formatBRL(stats.avg_value)} />
              <StatCard
                label="Tendência YoY"
                value={`${stats.crescimento_estimado_pct > 0 ? '+' : ''}${stats.crescimento_estimado_pct}%`}
                highlight={stats.crescimento_estimado_pct > 0 ? 'up' : stats.crescimento_estimado_pct < 0 ? 'down' : undefined}
              />
            </div>
          )}

          {/* AC2: Top 5 UFs por volume */}
          {stats && stats.top_ufs.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Top {Math.min(5, stats.top_ufs.length)} UFs por volume de licitações
              </h2>
              <div className="space-y-3">
                {stats.top_ufs.slice(0, 5).map((uf, i) => {
                  const pct = totalUfCount > 0 ? Math.round((uf.count / totalUfCount) * 100) : 0;
                  const ufName = UF_NAMES[uf.name] || uf.name;
                  return (
                    <div key={uf.name} className="flex items-center gap-3">
                      <span className="text-sm font-medium text-brand-blue w-6 text-right">{i + 1}.</span>
                      <Link
                        href={getUfPageHref(setor, sector.id, uf.name)}
                        className="text-sm text-ink hover:text-brand-blue w-44 shrink-0 truncate"
                      >
                        {ufName} ({uf.name})
                      </Link>
                      <div className="flex-1 bg-surface-2 rounded-full h-3 overflow-hidden">
                        {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: percentage width computed from uf.count/totalUfCount at runtime */}
                        <div
                          className="bg-brand-blue h-full rounded-full transition-all"
                          style={{ width: `${Math.max(pct, 2)}%` }}
                        />
                      </div>
                      <span className="text-sm text-ink w-16 text-right">{uf.count}</span>
                      <span className="text-sm text-ink-secondary w-12 text-right">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* AC2: Modalidades — distribuição % */}
          {stats && stats.top_modalidades.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Distribuição por modalidade
              </h2>
              <div className="space-y-3">
                {stats.top_modalidades.map((mod) => {
                  const pct = totalModCount > 0 ? Math.round((mod.count / totalModCount) * 100) : 0;
                  return (
                    <div key={mod.name} className="flex items-center gap-3">
                      <span className="text-sm text-ink-secondary w-48 shrink-0 truncate">{mod.name}</span>
                      <div className="flex-1 bg-surface-2 rounded-full h-3 overflow-hidden">
                        {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: percentage width computed from mod.count/totalModCount at runtime */}
                        <div
                          className="bg-brand-blue h-full rounded-full transition-all"
                          style={{ width: `${Math.max(pct, 2)}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-ink w-12 text-right">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* AC2: Sazonalidade — 12-month chart */}
          {stats && stats.sazonalidade.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Sazonalidade — volume mensal estimado
              </h2>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
                {stats.sazonalidade.map((month) => {
                  const maxCount = Math.max(...stats.sazonalidade.map((m) => m.count));
                  const heightPct = maxCount > 0 ? Math.round((month.count / maxCount) * 100) : 0;
                  return (
                    <div key={month.period} className="text-center">
                      <div className="h-24 flex items-end justify-center mb-2">
                        {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: bar height computed from month.count/maxCount at runtime */}
                        <div
                          className="w-8 bg-brand-blue/80 rounded-t"
                          style={{ height: `${Math.max(heightPct, 5)}%` }}
                        />
                      </div>
                      <p className="text-xs text-ink-secondary">{month.period}</p>
                      <p className="text-sm font-medium text-ink">{month.count}</p>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* AC2: Faixa de valores */}
          {stats && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Faixa de valores
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg border border-[var(--border)] text-center">
                  <p className="text-sm text-ink-secondary mb-1">Valor Total</p>
                  <p className="text-xl font-bold text-ink">{formatBRL(stats.total_value)}</p>
                </div>
                <div className="p-4 rounded-lg border border-[var(--border)] text-center">
                  <p className="text-sm text-ink-secondary mb-1">Valor Médio</p>
                  <p className="text-xl font-bold text-ink">{formatBRL(stats.avg_value)}</p>
                </div>
                <div className="p-4 rounded-lg border border-[var(--border)] text-center">
                  <p className="text-sm text-ink-secondary mb-1">Editais no período</p>
                  <p className="text-xl font-bold text-ink">{stats.total_nacional.toLocaleString('pt-BR')}</p>
                </div>
              </div>
            </section>
          )}

          {/* Inline CTA */}
          <BlogCTA
            variant="inline"
            setor={sector.name}
            count={stats?.total_nacional}
            slug={slug}
          />

          {/* AC3: Editorial — Contexto do setor */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              {sector.name} no mercado de compras públicas
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>{editorial}</p>
            </div>
          </section>

          {/* AC3: Editorial — Contexto ampliado */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Panorama nacional de {sector.name} em licitações
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>{panoramaEditorial.contexto}</p>
            </div>
          </section>

          {/* AC3: Dicas para competir */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Dicas para competir em licitações de {sector.name}
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>{panoramaEditorial.dicas}</p>
            </div>
          </section>

          {/* AC3: Perfil do comprador */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Perfil do comprador governamental de {sector.name}
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>{panoramaEditorial.perfilComprador}</p>
            </div>
          </section>

          {/* AC3: Casos de uso */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Como empresas de {sector.name} usam dados de licitação
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>{panoramaEditorial.casosDeUso}</p>
            </div>
          </section>

          {/* AC3: Tendências 2026 */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              O que observar em {year} — tendências para {sector.name}
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>{panoramaEditorial.tendencias2026}</p>
            </div>
          </section>

          {/* AC4: FAQ Section (7 questions) */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Perguntas frequentes sobre licitações de {sector.name}
            </h2>
            <div className="space-y-4">
              {faqs.map((faq, i) => (
                <details
                  key={i}
                  className="group border border-[var(--border)] rounded-lg"
                >
                  <summary className="flex items-center justify-between p-4 cursor-pointer font-medium text-ink hover:bg-surface-1 rounded-lg transition-colors">
                    {faq.question}
                    <span className="text-ink-secondary group-open:rotate-180 transition-transform">
                      &#x25BE;
                    </span>
                  </summary>
                  <p className="px-4 pb-4 text-ink-secondary leading-relaxed">
                    {faq.answer}
                  </p>
                </details>
              ))}
            </div>
          </section>

          {/* AC5: All 27 UF links — internal linking grid */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Licitações de {sector.name} por estado
            </h2>
            <p className="text-sm text-ink-secondary mb-4">
              Confira dados detalhados por UF — cada página mostra editais ativos, valor médio e oportunidades reais.
            </p>
            <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-7 gap-2">
              {ALL_UFS.map((uf) => (
                <Link
                  key={uf}
                  href={getUfPageHref(setor, sector.id, uf)}
                  className="flex items-center justify-center p-2 rounded-lg border border-[var(--border)] hover:border-brand-blue/30 hover:bg-surface-1 transition-colors text-sm font-medium text-ink"
                >
                  {uf}
                </Link>
              ))}
            </div>
          </section>

          {/* AC5: Related panoramas */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Panoramas de setores relacionados
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {relatedSectors.map((s) => (
                <Link
                  key={s.id}
                  href={`/blog/panorama/${s.slug}`}
                  className="p-4 rounded-lg border border-[var(--border)] hover:border-brand-blue/30 hover:bg-surface-1 transition-colors"
                >
                  <p className="font-medium text-ink mb-1">{s.name}</p>
                  <p className="text-sm text-ink-secondary">{s.description}</p>
                </Link>
              ))}
            </div>
          </section>

          {/* Final CTA */}
          <BlogCTA
            variant="final"
            setor={sector.name}
            count={stats?.total_nacional}
            slug={slug}
          />

          {/* AC5: Related Pages — editorial + other links */}
          <RelatedPages
            sectorId={sector.id}
            currentType="panorama"
          />
        </div>
      </main>

      <Footer />
    </div>
  );
}

function StatCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: 'up' | 'down';
}) {
  return (
    <div className="p-4 rounded-lg border border-[var(--border)] text-center">
      <p className="text-sm text-ink-secondary mb-1">{label}</p>
      <p className={`text-lg font-semibold ${
        highlight === 'up' ? 'text-green-600' :
        highlight === 'down' ? 'text-red-600' :
        'text-ink'
      }`}>
        {highlight === 'up' && '↑ '}
        {highlight === 'down' && '↓ '}
        {value}
      </p>
    </div>
  );
}
