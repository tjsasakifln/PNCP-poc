import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import SchemaMarkup from '@/components/blog/SchemaMarkup';
import BlogCTA from '@/components/blog/BlogCTA';
import RelatedPages from '@/components/blog/RelatedPages';
import {
  generateSectorParams,
  getSectorFromSlug,
  fetchContratosSetorStats,
  generateContratosSetorFAQs,
  getContratosEditorialContent,
  ALL_UFS,
  UF_NAMES,
} from '@/lib/programmatic';
import { buildCanonical } from '@/lib/seo';

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return generateSectorParams();
}

function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(value);
}

type Props = { params: Promise<{ setor: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { setor } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) return { title: 'Setor nao encontrado' };

  const stats = await fetchContratosSetorStats(setor);
  const total = stats?.total_contracts ?? 0;
  const year = new Date().getFullYear();
  const canonicalUrl = buildCanonical(`/blog/contratos/${setor}`);

  return {
    title: `Contratos Publicos de ${sector.name}: Panorama Nacional ${year}`,
    description: `${total > 0 ? total.toLocaleString('pt-BR') : 'Centenas de'} contratos publicos de ${sector.name} analisados. Principais orgaos compradores, fornecedores, valores e tendencias. Dados PNCP ${year}.`,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: `Contratos Publicos de ${sector.name} ${year} | SmartLic`,
      description: `Panorama nacional de contratos de ${sector.name}. Dados ao vivo do PNCP.`,
      url: canonicalUrl,
      type: 'article',
      locale: 'pt_BR',
    },
    twitter: {
      card: 'summary_large_image',
      title: `Contratos Publicos de ${sector.name} ${year}`,
      description: `${total > 0 ? total : 'Centenas de'} contratos analisados.`,
    },
  };
}

export default async function ContratosSetorPillarPage({ params }: Props) {
  const { setor } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) notFound();

  const stats = await fetchContratosSetorStats(setor);
  const editorial = getContratosEditorialContent(sector.id);
  const faqs = generateContratosSetorFAQs(
    sector.name,
    stats?.total_contracts,
    stats?.top_orgaos?.[0]?.nome,
  );
  const year = new Date().getFullYear();
  const slug = `contratos/${setor}`;
  const url = buildCanonical(`/blog/${slug}`);

  const breadcrumbs = [
    { name: 'SmartLic', url: 'https://smartlic.tech' },
    { name: 'Blog', url: 'https://smartlic.tech/blog' },
    { name: 'Contratos', url: 'https://smartlic.tech/contratos' },
    { name: sector.name, url },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <SchemaMarkup
        pageType="sector"
        title={`Contratos Publicos de ${sector.name}`}
        description={`Panorama nacional de contratos publicos de ${sector.name} ${year}`}
        url={url}
        sectorName={sector.name}
        totalEditais={stats?.total_contracts}
        breadcrumbs={breadcrumbs}
        faqs={faqs}
        dataPoints={[
          { name: 'Total de Contratos', value: stats?.total_contracts ?? 0 },
          { name: 'Valor Total', value: stats?.total_value ?? 0 },
          { name: 'Valor Medio', value: stats?.avg_value ?? 0 },
        ]}
      />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
            <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6 flex-wrap">
              <Link href="/blog" className="hover:text-brand-blue">Blog</Link>
              <span>/</span>
              <Link href="/contratos" className="hover:text-brand-blue">Contratos</Link>
              <span>/</span>
              <span className="text-ink">{sector.name}</span>
            </nav>
            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4 font-serif"
            >
              Contratos Publicos de {sector.name}
            </h1>
            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              Panorama nacional {year}: orgaos compradores, fornecedores, valores e tendencias.
              Dados atualizados do PNCP.
            </p>
            {stats && (
              <p className="mt-3 text-sm text-ink-secondary">
                Dados atualizados em {new Date(stats.last_updated).toLocaleDateString('pt-BR')}
              </p>
            )}
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* Stats Grid */}
          {stats && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
              <StatCard label="Total de Contratos" value={stats.total_contracts.toLocaleString('pt-BR')} />
              <StatCard label="Valor Total" value={formatBRL(stats.total_value)} />
              <StatCard label="Valor Medio" value={formatBRL(stats.avg_value)} />
            </div>
          )}

          {/* Top Orgaos */}
          {stats && stats.top_orgaos.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Principais Orgaos Compradores de {sector.name}
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-ink-secondary">
                      <th className="text-left py-2 pr-4 font-medium">Orgao</th>
                      <th className="text-right py-2 px-4 font-medium">Contratos</th>
                      <th className="text-right py-2 pl-4 font-medium">Valor Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.top_orgaos.map((o) => (
                      <tr key={o.cnpj} className="border-b border-[var(--border)] hover:bg-surface-1 transition-colors">
                        <td className="py-3 pr-4">
                          <Link href={`/contratos/orgao/${o.cnpj}`} className="text-brand-blue hover:underline font-medium">
                            {o.nome}
                          </Link>
                        </td>
                        <td className="py-3 px-4 text-right font-mono">{o.total_contratos}</td>
                        <td className="py-3 pl-4 text-right font-mono">{formatBRL(o.valor_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Top Fornecedores */}
          {stats && stats.top_fornecedores.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Principais Fornecedores de {sector.name}
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-ink-secondary">
                      <th className="text-left py-2 pr-4 font-medium">Fornecedor</th>
                      <th className="text-right py-2 px-4 font-medium">Contratos</th>
                      <th className="text-right py-2 pl-4 font-medium">Valor Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.top_fornecedores.map((f) => (
                      <tr key={f.cnpj} className="border-b border-[var(--border)] hover:bg-surface-1 transition-colors">
                        <td className="py-3 pr-4">
                          <Link href={`/cnpj/${f.cnpj}`} className="text-brand-blue hover:underline font-medium">
                            {f.nome}
                          </Link>
                        </td>
                        <td className="py-3 px-4 text-right font-mono">{f.total_contratos}</td>
                        <td className="py-3 pl-4 text-right font-mono">{formatBRL(f.valor_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Inline CTA */}
          <BlogCTA variant="inline" setor={sector.name} count={stats?.total_contracts} slug={slug} />

          {/* Monthly Trend */}
          {stats && stats.monthly_trend.some(t => t.count > 0) && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">Tendencia Mensal (12 meses)</h2>
              <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3">
                {stats.monthly_trend.filter(t => t.count > 0).map((t) => (
                  <div key={t.month} className="p-3 rounded-lg border border-[var(--border)] text-center">
                    <p className="text-xs text-ink-secondary">{t.month}</p>
                    <p className="text-lg font-semibold text-ink">{t.count}</p>
                    <p className="text-xs text-ink-secondary">{formatBRL(t.value)}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Distribution by UF */}
          {stats && stats.by_uf.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Contratos de {sector.name} por Estado
              </h2>
              <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-2">
                {ALL_UFS.map((uf) => {
                  const ufData = stats.by_uf.find(u => u.uf === uf);
                  return (
                    <Link
                      key={uf}
                      href={`/contratos/${setor}/${uf.toLowerCase()}`}
                      className="flex flex-col items-center p-2 rounded-lg border border-[var(--border)] hover:border-brand-blue/30 hover:bg-surface-1 transition-colors"
                    >
                      <span className="font-medium text-ink text-sm">{uf}</span>
                      <span className="text-xs text-ink-secondary">
                        {ufData ? ufData.total_contratos : 0}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </section>
          )}

          {/* Editorial Content */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Mercado de contratos publicos de {sector.name}
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>{editorial}</p>
            </div>
          </section>

          {/* FAQ Section */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">Perguntas frequentes</h2>
            <div className="space-y-4">
              {faqs.map((faq, i) => (
                <details key={i} className="group border border-[var(--border)] rounded-lg">
                  <summary className="flex items-center justify-between p-4 cursor-pointer font-medium text-ink hover:bg-surface-1 rounded-lg transition-colors">
                    {faq.question}
                    <span className="text-ink-secondary group-open:rotate-180 transition-transform">&#x25BE;</span>
                  </summary>
                  <p className="px-4 pb-4 text-ink-secondary leading-relaxed">{faq.answer}</p>
                </details>
              ))}
            </div>
          </section>

          {/* Final CTA */}
          <BlogCTA variant="final" setor={sector.name} count={stats?.total_contracts} slug={slug} />

          {/* Related Pages */}
          <RelatedPages sectorId={sector.id} currentType="sector" />
        </div>
      </main>

      <Footer />
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-1 border border-[var(--border)] rounded-xl p-5 text-center">
      <p className="text-xs text-ink-secondary uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-bold text-ink">{value}</p>
    </div>
  );
}
