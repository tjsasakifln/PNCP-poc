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
  fetchSectorBlogStats,
  getSectorFromSlug,
  formatBRL,
  getEditorialContent,
  generateSectorFAQs,
  UF_NAMES,
} from '@/lib/programmatic';

/**
 * MKT-002 AC2: Sector programmatic page template.
 *
 * ISR with 24h revalidation. Each sector gets a unique page with:
 * - Dynamic stats from backend API
 * - 300+ word editorial content block
 * - Auto-generated FAQ
 * - Schema markup (Article + FAQPage + Dataset + HowTo)
 * - Internal linking via RelatedPages
 * - Contextual CTA
 */

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return generateSectorParams();
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ setor: string }>;
}): Promise<Metadata> {
  const { setor } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) return { title: 'Setor não encontrado' };

  const stats = await fetchSectorBlogStats(setor);
  const total = stats?.total_editais ?? 0;
  const canonicalUrl = `https://smartlic.tech/blog/programmatic/${setor}`;

  return {
    title: `Licitações de ${sector.name} — ${total > 0 ? `${total} Editais Publicados` : 'Oportunidades Abertas'}`,
    description: `Dados atualizados de licitações de ${sector.name}: ${total} editais publicados, modalidades predominantes, UFs mais ativas e tendência de 90 dias. Analise com IA.`,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: `Licitações de ${sector.name} | SmartLic`,
      description: `${total} editais de ${sector.name} publicados. Dados ao vivo do PNCP.`,
      url: canonicalUrl,
      type: 'article',
      locale: 'pt_BR',
      siteName: 'SmartLic',
    },
    twitter: {
      card: 'summary_large_image',
      title: `Licitações de ${sector.name} | SmartLic`,
      description: `${total} editais de ${sector.name} publicados.`,
    },
  };
}

export default async function SectorProgrammaticPage({
  params,
}: {
  params: Promise<{ setor: string }>;
}) {
  const { setor } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) notFound();

  const stats = await fetchSectorBlogStats(setor);
  const editorial = getEditorialContent(sector.id);
  const faqs = generateSectorFAQs(
    sector.name,
    stats?.total_editais,
    stats?.top_ufs?.[0]?.name,
  );
  const slug = `programmatic/${setor}`;
  const url = `https://smartlic.tech/blog/${slug}`;

  const breadcrumbs = [
    { name: 'SmartLic', url: 'https://smartlic.tech' },
    { name: 'Blog', url: 'https://smartlic.tech/blog' },
    { name: sector.name, url },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <SchemaMarkup
        pageType="sector"
        title={`Licitações de ${sector.name}`}
        description={`Dados atualizados de licitações de ${sector.name} no Brasil`}
        url={url}
        sectorName={sector.name}
        totalEditais={stats?.total_editais}
        breadcrumbs={breadcrumbs}
        faqs={faqs}
        dataPoints={[
          { name: 'Total de Editais', value: stats?.total_editais ?? 0 },
          { name: 'Valor Médio', value: stats?.avg_value ?? 0 },
          { name: 'Faixa Mínima', value: stats?.value_range_min ?? 0 },
          { name: 'Faixa Máxima', value: stats?.value_range_max ?? 0 },
        ]}
      />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
            <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6">
              <Link href="/blog" className="hover:text-brand-blue">Blog</Link>
              <span>/</span>
              <span className="text-ink">{sector.name}</span>
            </nav>
            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4 font-serif"
            >
              Licitações de {sector.name}
            </h1>
            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              {sector.description}. Dados atualizados do PNCP e portais estaduais.
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
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
              <StatCard
                label="Editais Publicados"
                value={stats.total_editais.toString()}
              />
              <StatCard
                label="Valor Médio"
                value={formatBRL(stats.avg_value)}
              />
              <StatCard
                label="Faixa Mínima"
                value={formatBRL(stats.value_range_min)}
              />
              <StatCard
                label="Faixa Máxima"
                value={formatBRL(stats.value_range_max)}
              />
            </div>
          )}

          {/* Top UFs */}
          {stats && stats.top_ufs.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                UFs com mais licitações de {sector.name}
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {stats.top_ufs.map((uf) => (
                  <Link
                    key={uf.name}
                    href={`/blog/programmatic/${setor}/${uf.name.toLowerCase()}`}
                    className="flex items-center justify-between p-3 rounded-lg border border-[var(--border)] hover:border-brand-blue/30 hover:bg-surface-1 transition-colors"
                  >
                    <span className="font-medium text-ink">{uf.name}</span>
                    <span className="text-sm text-ink-secondary">{uf.count}</span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Top Modalities */}
          {stats && stats.top_modalidades.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Modalidades predominantes
              </h2>
              <div className="space-y-2">
                {stats.top_modalidades.map((mod) => (
                  <div key={mod.name} className="flex items-center gap-3">
                    <div className="flex-1 bg-surface-1 rounded-full h-3 overflow-hidden">
                      {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: percentage width computed from mod.count relative to top modalidade count at runtime */}
                      <div
                        className="h-full bg-brand-blue rounded-full"
                        style={{
                          width: `${Math.min(100, (mod.count / (stats.top_modalidades[0]?.count || 1)) * 100)}%`,
                        }}
                      />
                    </div>
                    <span className="text-sm text-ink min-w-[180px]">{mod.name}</span>
                    <span className="text-sm text-ink-secondary">{mod.count}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Inline CTA */}
          <BlogCTA
            variant="inline"
            setor={sector.name}
            count={stats?.total_editais}
            slug={slug}
          />

          {/* Editorial Content (300+ words) */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Mercado de {sector.name} em licitações públicas
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>{editorial}</p>
            </div>
          </section>

          {/* 90-day Trend */}
          {stats && stats.trend_90d.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Tendência de 90 dias
              </h2>
              <div className="grid grid-cols-3 gap-4">
                {stats.trend_90d.map((point) => (
                  <div
                    key={point.period}
                    className="p-4 rounded-lg border border-[var(--border)] text-center"
                  >
                    <p className="text-sm text-ink-secondary">{point.period}</p>
                    <p className="text-lg font-semibold text-ink">{point.count} editais</p>
                    <p className="text-sm text-ink-secondary">
                      média {formatBRL(point.avg_value)}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* FAQ Section */}
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

          {/* Final CTA */}
          <BlogCTA
            variant="final"
            setor={sector.name}
            count={stats?.total_editais}
            slug={slug}
          />

          {/* Related Pages */}
          <RelatedPages
            sectorId={sector.id}
            currentType="sector"
          />
        </div>
      </main>

      <Footer />
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-4 rounded-lg border border-[var(--border)] text-center">
      <p className="text-sm text-ink-secondary mb-1">{label}</p>
      <p className="text-lg font-semibold text-ink">{value}</p>
    </div>
  );
}
