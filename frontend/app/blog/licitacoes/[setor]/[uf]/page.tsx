import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import SchemaMarkup from '@/components/blog/SchemaMarkup';
import BlogCTA from '@/components/blog/BlogCTA';
import RelatedPages from '@/components/blog/RelatedPages';
import {
  generateLicitacoesParams,
  fetchSectorUfBlogStats,
  getSectorFromSlug,
  formatBRL,
  generateLicitacoesFAQs,
  getRegionalEditorial,
  ALL_UFS,
  UF_NAMES,
} from '@/lib/programmatic';
import { getCitiesByUf } from '@/lib/cities';
import { getFreshnessLabel } from '@/lib/seo';

/**
 * MKT-003 AC1: Sector × UF programmatic page.
 *
 * Route: /blog/licitacoes/{setor}/{uf}
 * ISR 24h. Phase 1: 5 sectors × 5 UFs = 25 pages.
 */

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return generateLicitacoesParams();
}

function getMonthYear(): string {
  const now = new Date();
  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ];
  return `${months[now.getMonth()]} ${now.getFullYear()}`;
}

function getTrendIndicator(trend: { period: string; count: number }[]): {
  text: string;
  direction: 'up' | 'down' | 'stable';
  pct: number;
} {
  if (!trend || trend.length < 2) return { text: 'Estável', direction: 'stable', pct: 0 };
  const latest = trend[trend.length - 1].count;
  const previous = trend[trend.length - 2].count;
  if (previous === 0) return { text: 'Novo', direction: 'up', pct: 0 };
  const pct = Math.round(((latest - previous) / previous) * 100);
  if (pct > 5) return { text: `+${pct}%`, direction: 'up', pct };
  if (pct < -5) return { text: `${pct}%`, direction: 'down', pct };
  return { text: 'Estável', direction: 'stable', pct: 0 };
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ setor: string; uf: string }>;
}): Promise<Metadata> {
  const { setor, uf } = await params;
  const ufUpper = uf.toUpperCase();
  const sector = getSectorFromSlug(setor);
  if (!sector || !ALL_UFS.includes(ufUpper)) return { title: 'Página não encontrada' };

  const stats = await fetchSectorUfBlogStats(setor, ufUpper);
  const total = stats?.total_editais ?? 0;
  const ufName = UF_NAMES[ufUpper] || ufUpper;
  const year = new Date().getFullYear();
  const canonicalUrl = `https://smartlic.tech/blog/licitacoes/${setor}/${uf}`;

  return {
    title: `Licitações de ${sector.name} em ${ufName} — Editais Abertos ${year} | SmartLic`,
    description: `Encontre ${total > 0 ? total : ''} licitações de ${sector.name.toLowerCase()} em ${ufName}. Dados ao vivo de PNCP, PCP e ComprasGov. Filtre por valor, modalidade e prazo. Teste grátis.`,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: `Licitações de ${sector.name} em ${ufName} — Editais Abertos ${year} | SmartLic`,
      description: `${total > 0 ? `${total} editais` : 'Editais'} de ${sector.name.toLowerCase()} em ${ufName}. Dados ao vivo consolidados de 3 fontes oficiais.`,
      url: canonicalUrl,
      type: 'article',
      locale: 'pt_BR',
    },
    twitter: {
      card: 'summary_large_image',
      title: `Licitações de ${sector.name} em ${ufName} | SmartLic`,
    },
  };
}

export default async function LicitacoesSectorUfPage({
  params,
}: {
  params: Promise<{ setor: string; uf: string }>;
}) {
  const { setor, uf } = await params;
  const ufUpper = uf.toUpperCase();
  const sector = getSectorFromSlug(setor);
  if (!sector || !ALL_UFS.includes(ufUpper)) notFound();

  const stats = await fetchSectorUfBlogStats(setor, ufUpper);
  const ufName = UF_NAMES[ufUpper] || ufUpper;
  const monthYear = getMonthYear();
  const faqs = generateLicitacoesFAQs(sector.name, ufName, stats?.total_editais, stats?.avg_value);
  const editorial = getRegionalEditorial(sector.name, ufUpper, ufName);
  const slug = `licitacoes/${setor}/${uf}`;
  const url = `https://smartlic.tech/blog/${slug}`;
  const trend = stats?.trend_90d ? getTrendIndicator(stats.trend_90d) : null;

  // Modality percentages
  const totalModCount = stats?.top_modalidades?.reduce((s, m) => s + m.count, 0) ?? 0;

  const breadcrumbs = [
    { name: 'SmartLic', url: 'https://smartlic.tech' },
    { name: 'Blog', url: 'https://smartlic.tech/blog' },
    { name: 'Licitações', url: 'https://smartlic.tech/blog/licitacoes' },
    { name: sector.name, url: `https://smartlic.tech/blog/programmatic/${setor}` },
    { name: ufName, url },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <SchemaMarkup
        pageType="sector-uf"
        title={`Licitações de ${sector.name} em ${ufName} — ${monthYear}`}
        description={`${stats?.total_editais ?? 0} licitações de ${sector.name} em ${ufName}`}
        url={url}
        sectorName={sector.name}
        uf={ufUpper}
        totalEditais={stats?.total_editais}
        breadcrumbs={breadcrumbs}
        faqs={faqs}
        dataPoints={[
          { name: 'Total de Editais', value: stats?.total_editais ?? 0 },
          { name: 'Valor Mínimo', value: stats?.value_range_min ?? 0 },
          { name: 'Valor Máximo', value: stats?.value_range_max ?? 0 },
          { name: 'Valor Médio', value: stats?.avg_value ?? 0 },
        ]}
      />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
            <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6">
              <Link href="/blog" className="hover:text-brand-blue">Blog</Link>
              <span>/</span>
              <Link href="/blog/licitacoes" className="hover:text-brand-blue">Licitações</Link>
              <span>/</span>
              <Link href={`/blog/programmatic/${setor}`} className="hover:text-brand-blue">
                {sector.name}
              </Link>
              <span>/</span>
              <span className="text-ink">{ufName}</span>
            </nav>

            {/* AC2: H1 with month and year */}
            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              Licitações de {sector.name} em {ufName} — {monthYear}
            </h1>

            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              {stats?.total_editais ?? 0} editais publicados nos últimos 10 dias.
              {stats?.value_range_min && stats?.value_range_max
                ? ` Faixa de valores: ${formatBRL(stats.value_range_min)} a ${formatBRL(stats.value_range_max)}.`
                : ''}
            </p>

            {/* AC4: Badge "Dados atualizados em {data}" + granular freshness label */}
            {stats && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <p className="inline-flex items-center gap-2 text-sm text-ink-secondary bg-surface-2 px-3 py-1 rounded-full">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  Dados atualizados em {new Date(stats.last_updated).toLocaleDateString('pt-BR')}
                </p>
                <time
                  dateTime={new Date(stats.last_updated).toISOString()}
                  className="text-xs text-ink-muted"
                >
                  {getFreshnessLabel(stats.last_updated)}
                </time>
              </div>
            )}
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* AC2: Stats grid — count, value range, modalities, trend */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Editais Abertos</p>
              <p className="text-2xl font-bold text-ink">{stats?.total_editais ?? 0}</p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Valor Médio</p>
              <p className="text-2xl font-bold text-ink">{formatBRL(stats?.avg_value ?? 0)}</p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Faixa de Valores</p>
              <p className="text-lg font-bold text-ink">
                {stats?.value_range_min ? formatBRL(stats.value_range_min) : 'R$ 0'}
                <span className="text-ink-secondary font-normal text-sm"> a </span>
                {stats?.value_range_max ? formatBRL(stats.value_range_max) : 'R$ 0'}
              </p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Tendência 90 dias</p>
              {trend && (
                <p className={`text-2xl font-bold ${
                  trend.direction === 'up' ? 'text-green-600' :
                  trend.direction === 'down' ? 'text-red-600' :
                  'text-ink'
                }`}>
                  {trend.direction === 'up' && '↑ '}
                  {trend.direction === 'down' && '↓ '}
                  {trend.text}
                </p>
              )}
            </div>
          </div>

          {/* AC2: Modality percentages */}
          {stats && stats.top_modalidades && stats.top_modalidades.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Modalidades predominantes
              </h2>
              <div className="space-y-3">
                {stats.top_modalidades.map((mod) => {
                  const pct = totalModCount > 0 ? Math.round((mod.count / totalModCount) * 100) : 0;
                  return (
                    <div key={mod.name} className="flex items-center gap-3">
                      <span className="text-sm text-ink-secondary w-48 shrink-0 truncate">{mod.name}</span>
                      <div className="flex-1 bg-surface-2 rounded-full h-3 overflow-hidden">
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

          {/* AC2: Top 5 opportunities of the week */}
          {stats && stats.top_oportunidades.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Top 5 oportunidades da semana
              </h2>
              <div className="space-y-3">
                {stats.top_oportunidades.map((item, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-lg border border-[var(--border)] hover:bg-surface-1 transition-colors"
                  >
                    <p className="font-medium text-ink mb-1 line-clamp-2">{item.titulo}</p>
                    <div className="flex flex-wrap gap-3 text-sm text-ink-secondary">
                      <span>{item.orgao}</span>
                      {item.valor && <span className="font-medium text-ink">{formatBRL(item.valor)}</span>}
                      {item.data && <span>{item.data}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* AC4: CTA inline */}
          <BlogCTA
            variant="inline"
            setor={sector.name}
            uf={ufName}
            count={stats?.total_editais}
            slug={`${setor}-${uf}`}
          />

          {/* AC2: Regional editorial block (300+ words) */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              {sector.name} em {ufName}: panorama de licitações
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              {editorial.map((paragraph, i) => (
                <p key={i}>{paragraph}</p>
              ))}
            </div>
          </section>

          {/* Thin content mitigation: show suggestion when 0 results */}
          {(!stats || stats.total_editais === 0) && (
            <div className="mb-10 p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800 font-medium mb-2">
                Nenhuma licitação ativa neste período para {sector.name} em {ufName}.
              </p>
              <p className="text-sm text-yellow-700">
                Isso pode variar — licitações são publicadas diariamente. Confira UFs vizinhas ou
                teste o SmartLic para receber alertas automáticos quando novas oportunidades surgirem.
              </p>
            </div>
          )}

          {/* AC2: FAQ section */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Perguntas frequentes
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

          {/* AC4: Final CTA with button */}
          <BlogCTA
            variant="final"
            setor={sector.name}
            uf={ufName}
            count={stats?.total_editais}
            slug={`${setor}-${uf}`}
          />

          {/* AC7: Internal linking */}
          <RelatedPages
            sectorId={sector.id}
            currentUf={ufUpper}
            currentType="sector-uf"
          />

          {/* SEO Frente 4: Cidades relevantes em {UF} */}
          {(() => {
            const cidadesUf = getCitiesByUf(ufUpper);
            if (cidadesUf.length === 0) return null;
            return (
              <section className="mt-10">
                <h2 className="text-xl font-semibold text-ink mb-4">
                  Cidades relevantes em {ufName}
                </h2>
                <div className="flex flex-wrap gap-2">
                  {cidadesUf.map((c) => (
                    <Link
                      key={c.slug}
                      href={`/blog/licitacoes/cidade/${c.slug}`}
                      className="inline-flex items-center px-3 py-1.5 rounded-full border border-[var(--border)] text-sm text-ink-secondary hover:bg-surface-1 hover:text-ink transition-colors"
                    >
                      Licitações em {c.name}
                    </Link>
                  ))}
                </div>
              </section>
            );
          })()}
        </div>
      </main>

      <Footer />
    </div>
  );
}
