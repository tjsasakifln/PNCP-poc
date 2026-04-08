import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import SchemaMarkup from '@/components/blog/SchemaMarkup';
import BlogCTA from '@/components/blog/BlogCTA';
import BreadcrumbNav from '@/components/seo/BreadcrumbNav';
import {
  CITIES,
  getCityBySlug,
  getCitiesByUf,
  fetchCidadeSectorStats,
} from '@/lib/cities';
import {
  UF_NAMES,
  formatBRL,
  getCidadeSectorEditorial,
  generateCidadeSectorFAQs,
} from '@/lib/programmatic';
import { SECTORS, getSectorBySlug } from '@/lib/sectors';
import { getFreshnessLabel } from '@/lib/seo';

/**
 * Onda 3: City x Sector programmatic SEO pages.
 *
 * Route: /blog/licitacoes/cidade/{cidade}/{setor}
 * ISR 24h. 81 cities x 15 sectors = 1,215 pages.
 *
 * Captures high-intent searches like "licitacao tecnologia curitiba"
 * or "editais engenharia salvador".
 */

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  const params: { cidade: string; setor: string }[] = [];
  for (const city of CITIES) {
    for (const sector of SECTORS) {
      params.push({ cidade: city.slug, setor: sector.slug });
    }
  }
  return params;
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
  params: Promise<{ cidade: string; setor: string }>;
}): Promise<Metadata> {
  const { cidade, setor } = await params;
  const city = getCityBySlug(cidade);
  const sector = getSectorBySlug(setor);
  if (!city || !sector) return { title: 'Página não encontrada | SmartLic' };

  const stats = await fetchCidadeSectorStats(city.slug, sector.id);
  const total = stats?.total_editais ?? 0;
  const ufName = UF_NAMES[city.uf] || city.uf;
  const canonicalUrl = `https://smartlic.tech/blog/licitacoes/cidade/${city.slug}/${sector.slug}`;

  const title = `Licitações de ${sector.name} em ${city.name}/${city.uf}${
    total > 0 ? ` — ${total} editais` : ''
  } | SmartLic`;
  const description =
    `Encontre licitações de ${sector.name.toLowerCase()} em ${city.name} (${ufName}). ` +
    `${total > 0 ? `${total} editais ativos nos últimos 10 dias. ` : ''}` +
    `Dados consolidados de PNCP, PCP e ComprasGov. Filtre por valor, modalidade e prazo. Teste grátis.`;

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
      title: `Licitações de ${sector.name} em ${city.name}/${city.uf} | SmartLic`,
      description,
    },
  };
}

export default async function LicitacoesCidadeSetorPage({
  params,
}: {
  params: Promise<{ cidade: string; setor: string }>;
}) {
  const { cidade, setor } = await params;
  const city = getCityBySlug(cidade);
  const sector = getSectorBySlug(setor);
  if (!city || !sector) notFound();

  const stats = await fetchCidadeSectorStats(city.slug, sector.id);
  const ufName = UF_NAMES[city.uf] || city.uf;
  const monthYear = getMonthYear();
  const url = `https://smartlic.tech/blog/licitacoes/cidade/${city.slug}/${sector.slug}`;
  const total = stats?.total_editais ?? 0;
  const hasData = !!stats && total > 0;
  const hasSufficientData = stats?.has_sufficient_data ?? false;

  const breadcrumbs = [
    { label: 'Início', href: '/' },
    { label: 'Licitações', href: '/licitacoes' },
    { label: city.name, href: `/blog/licitacoes/cidade/${city.slug}` },
    { label: sector.name },
  ];

  const schemaBreadcrumbs = [
    { name: 'SmartLic', url: 'https://smartlic.tech' },
    { name: 'Licitações', url: 'https://smartlic.tech/licitacoes' },
    { name: city.name, url: `https://smartlic.tech/blog/licitacoes/cidade/${city.slug}` },
    { name: sector.name, url },
  ];

  const editorial = getCidadeSectorEditorial(city.name, city.uf, ufName, sector.name);
  const faqs = generateCidadeSectorFAQs(
    city.name,
    city.uf,
    sector.name,
    stats?.total_editais,
    stats?.avg_value,
  );

  const nearbyCities = getCitiesByUf(city.uf).filter((c) => c.slug !== city.slug);
  const otherSectors = SECTORS.filter((s) => s.slug !== sector.slug);

  const topModalidade = stats?.top_modalidades?.[0]?.name ?? 'Pregão Eletrônico';

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <SchemaMarkup
        pageType="cidade-setor"
        title={`Licitações de ${sector.name} em ${city.name}/${city.uf} — ${monthYear}`}
        description={`${total} licitações de ${sector.name.toLowerCase()} em ${city.name} (${ufName}) — dados consolidados de PNCP, PCP e ComprasGov.`}
        url={url}
        sectorName={sector.name}
        uf={city.uf}
        cidade={city.name}
        totalEditais={total}
        avgValue={stats?.avg_value}
        breadcrumbs={schemaBreadcrumbs}
        faqs={faqs}
        dataPoints={[
          { name: 'Total de Editais', value: total },
          { name: 'Valor Médio', value: stats?.avg_value ?? 0 },
          { name: 'Órgãos Compradores Ativos', value: stats?.orgaos_frequentes?.length ?? 0 },
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
              Licitações de {sector.name} em {city.name}/{city.uf}
            </h1>

            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              {hasData
                ? `${total} editais de ${sector.name.toLowerCase()} publicados em ${city.name} nos últimos 10 dias.`
                : `Acompanhe em tempo real as licitações de ${sector.name.toLowerCase()} em ${city.name} (${ufName}).`}
              {stats && stats.avg_value > 0
                ? ` Valor médio estimado: ${formatBRL(stats.avg_value)}.`
                : ''}
            </p>

            {stats && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <p className="inline-flex items-center gap-2 text-sm text-ink-secondary bg-surface-2 px-3 py-1 rounded-full">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  Dados atualizados {getFreshnessLabel(stats.last_updated)}
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* Stats grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Editais Abertos</p>
              <p className="text-2xl font-bold text-ink">{total}</p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Valor Médio</p>
              <p className="text-2xl font-bold text-ink">{formatBRL(stats?.avg_value ?? 0)}</p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Top Modalidade</p>
              <p className="text-lg font-bold text-ink leading-tight">{topModalidade}</p>
            </div>
            {stats && stats.value_range_max > 0 && (
              <div className="p-4 rounded-lg border border-[var(--border)] text-center">
                <p className="text-sm text-ink-secondary mb-1">Faixa de Valores</p>
                <p className="text-lg font-bold text-ink leading-tight">
                  {formatBRL(stats.value_range_min)} — {formatBRL(stats.value_range_max)}
                </p>
              </div>
            )}
          </div>

          {/* Modality distribution */}
          {stats && stats.top_modalidades.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Modalidades de contratação em {city.name}
              </h2>
              <div className="space-y-3">
                {stats.top_modalidades.map((mod) => {
                  const pct = total > 0 ? Math.round((mod.count / total) * 100) : 0;
                  return (
                    <div key={mod.name} className="flex items-center gap-3">
                      <span className="text-sm text-ink-secondary w-48 shrink-0 truncate">
                        {mod.name}
                      </span>
                      <div className="flex-1 h-3 bg-surface-2 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[var(--accent)] rounded-full transition-all"
                          style={{ width: `${Math.max(pct, 2)}%` }}
                        />
                      </div>
                      <span className="text-sm text-ink-secondary w-16 text-right shrink-0">
                        {mod.count} ({pct}%)
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* Top 5 opportunities */}
          {hasSufficientData && stats && stats.top_oportunidades.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Oportunidades recentes de {sector.name} em {city.name}
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)]">
                      <th className="text-left py-3 px-2 text-ink-secondary font-medium">Objeto</th>
                      <th className="text-left py-3 px-2 text-ink-secondary font-medium">Órgão</th>
                      <th className="text-right py-3 px-2 text-ink-secondary font-medium">Valor Est.</th>
                      <th className="text-right py-3 px-2 text-ink-secondary font-medium">Data</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.top_oportunidades.map((item, i) => (
                      <tr key={i} className="border-b border-[var(--border)] hover:bg-surface-1 transition-colors">
                        <td className="py-3 px-2 text-ink max-w-xs truncate">{item.titulo}</td>
                        <td className="py-3 px-2 text-ink-secondary max-w-[200px] truncate">{item.orgao}</td>
                        <td className="py-3 px-2 text-ink text-right whitespace-nowrap">
                          {item.valor ? formatBRL(item.valor) : 'Não informado'}
                        </td>
                        <td className="py-3 px-2 text-ink-secondary text-right whitespace-nowrap">
                          {item.data ? new Date(item.data).toLocaleDateString('pt-BR') : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Top buying orgs */}
          {stats && stats.orgaos_frequentes.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Órgãos que mais compram {sector.name.toLowerCase()} em {city.name}
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
            setor={sector.name}
            uf={ufName}
            count={total}
            slug={`cidade-${city.slug}-${sector.slug}`}
          />

          {/* Editorial block */}
          <section className="mb-10 mt-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              {sector.name} em {city.name}: panorama de licitações
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              {editorial.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          </section>

          {/* Thin content fallback */}
          {!hasSufficientData && (
            <div className="mb-10 p-5 rounded-lg border-l-4 border-amber-400 bg-amber-50 dark:bg-amber-950/20">
              <p className="text-sm text-amber-800 dark:text-amber-200 font-medium mb-2">
                Volume reduzido de editais nesta combinação
              </p>
              <p className="text-sm text-amber-700 dark:text-amber-300 leading-relaxed">
                No momento, o volume de editais de {sector.name.toLowerCase()} especificamente em{' '}
                {city.name} é reduzido. Isso é comum em períodos de transição orçamentária ou para
                combinações cidade/setor mais específicas. Recomendamos acompanhar também:
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Link
                  href={`/blog/licitacoes/cidade/${city.slug}`}
                  className="inline-flex items-center px-3 py-1.5 rounded-full bg-white dark:bg-surface-1 border border-amber-300 text-sm text-amber-800 dark:text-amber-200 hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
                >
                  Todos os setores em {city.name}
                </Link>
                <Link
                  href={`/blog/licitacoes/${sector.slug}/${city.uf.toLowerCase()}`}
                  className="inline-flex items-center px-3 py-1.5 rounded-full bg-white dark:bg-surface-1 border border-amber-300 text-sm text-amber-800 dark:text-amber-200 hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
                >
                  {sector.name} em todo {ufName}
                </Link>
              </div>
            </div>
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

          {/* Internal links: Other sectors in same city */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Outros setores em {city.name}
            </h2>
            <div className="flex flex-wrap gap-2">
              {otherSectors.slice(0, 10).map((s) => (
                <Link
                  key={s.slug}
                  href={`/blog/licitacoes/cidade/${city.slug}/${s.slug}`}
                  className="inline-flex items-center px-3 py-1.5 rounded-full border border-[var(--border)] text-sm text-ink-secondary hover:bg-surface-1 hover:text-ink transition-colors"
                >
                  {s.name}
                </Link>
              ))}
            </div>
          </section>

          {/* Internal links: Same sector in nearby cities */}
          {nearbyCities.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                {sector.name} em outras cidades de {ufName}
              </h2>
              <div className="flex flex-wrap gap-2">
                {nearbyCities.map((c) => (
                  <Link
                    key={c.slug}
                    href={`/blog/licitacoes/cidade/${c.slug}/${sector.slug}`}
                    className="inline-flex items-center px-3 py-1.5 rounded-full border border-[var(--border)] text-sm text-ink-secondary hover:bg-surface-1 hover:text-ink transition-colors"
                  >
                    {c.name}
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Parent page links */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">Veja também</h2>
            <div className="flex flex-wrap gap-3">
              <Link
                href={`/blog/licitacoes/cidade/${city.slug}`}
                className="inline-flex items-center px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-ink hover:bg-surface-1 transition-colors"
              >
                Todas as licitações em {city.name}
              </Link>
              <Link
                href={`/blog/licitacoes/${sector.slug}/${city.uf.toLowerCase()}`}
                className="inline-flex items-center px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-ink hover:bg-surface-1 transition-colors"
              >
                {sector.name} em {ufName}
              </Link>
              <Link
                href={`/licitacoes/${sector.slug}`}
                className="inline-flex items-center px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-ink hover:bg-surface-1 transition-colors"
              >
                {sector.name} no Brasil
              </Link>
            </div>
          </section>

          {/* Final CTA */}
          <BlogCTA
            variant="final"
            setor={sector.name}
            uf={ufName}
            count={total}
            slug={`cidade-${city.slug}-${sector.slug}`}
          />
        </div>
      </main>

      <Footer />
    </div>
  );
}
