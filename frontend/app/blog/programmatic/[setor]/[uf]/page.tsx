import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import LandingNavbar from '../../../../components/landing/LandingNavbar';
import Footer from '../../../../components/Footer';
import SchemaMarkup from '@/components/blog/SchemaMarkup';
import BlogCTA from '@/components/blog/BlogCTA';
import RelatedPages from '@/components/blog/RelatedPages';
import {
  generateSectorUfParams,
  fetchSectorUfBlogStats,
  getSectorFromSlug,
  formatBRL,
  generateSectorFAQs,
  getUfPrep,
  ALL_UFS,
  UF_NAMES,
} from '@/lib/programmatic';

/**
 * MKT-002 AC2: Sector × UF programmatic page template.
 *
 * ISR 24h. Generates 15 sectors × 27 UFs = 405 pages.
 */

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return generateSectorUfParams();
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
  const canonicalUrl = `https://smartlic.tech/blog/programmatic/${setor}/${uf}`;

  // STORY-430 AC2: noindex quando abaixo do limiar de conteúdo ativo
  const minBids = parseInt(process.env.MIN_ACTIVE_BIDS_FOR_INDEX ?? '5', 10);
  if (total < minBids) {
    return {
      title: `Licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} | SmartLic`,
      description: `Licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}. Dados do PNCP atualizados diariamente.`,
      robots: { index: false, follow: false },
    };
  }

  return {
    title: `Licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} — ${total} Editais`,
    description: `${total} licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} (${ufUpper}). Top oportunidades da semana, valor médio e análise de viabilidade com IA.`,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: `Licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} | SmartLic`,
      description: `${total} editais de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}. Dados ao vivo do PNCP.`,
      url: canonicalUrl,
      type: 'article',
      locale: 'pt_BR',
    },
    twitter: {
      card: 'summary_large_image',
      title: `Licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} | SmartLic`,
    },
  };
}

export default async function SectorUfProgrammaticPage({
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
  const faqs = generateSectorFAQs(sector.name, stats?.total_editais, ufName);
  const slug = `programmatic/${setor}/${uf}`;
  const url = `https://smartlic.tech/blog/${slug}`;

  const breadcrumbs = [
    { name: 'SmartLic', url: 'https://smartlic.tech' },
    { name: 'Blog', url: 'https://smartlic.tech/blog' },
    { name: sector.name, url: `https://smartlic.tech/blog/programmatic/${setor}` },
    { name: ufName, url },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <SchemaMarkup
        pageType="sector-uf"
        title={`Licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`}
        description={`${stats?.total_editais ?? 0} licitações de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`}
        url={url}
        sectorName={sector.name}
        uf={ufUpper}
        totalEditais={stats?.total_editais}
        breadcrumbs={breadcrumbs}
        faqs={faqs}
        dataPoints={[
          { name: 'Total de Editais', value: stats?.total_editais ?? 0 },
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
              <Link href={`/blog/programmatic/${setor}`} className="hover:text-brand-blue">
                {sector.name}
              </Link>
              <span>/</span>
              <span className="text-ink">{ufName}</span>
            </nav>
            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              Licitações de {sector.name} {getUfPrep(ufUpper)} {ufName}
            </h1>
            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              {stats?.total_editais ?? 0} editais publicados nos últimos 10 dias.
              {stats?.avg_value ? ` Valor médio: ${formatBRL(stats.avg_value)}.` : ''}
            </p>
            {stats && (
              <p className="mt-3 text-sm text-ink-secondary">
                Dados atualizados em {new Date(stats.last_updated).toLocaleDateString('pt-BR')}
              </p>
            )}
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* Stats Summary */}
          {stats && (
            <div className="grid grid-cols-2 gap-4 mb-10">
              <div className="p-4 rounded-lg border border-[var(--border)] text-center">
                <p className="text-sm text-ink-secondary mb-1">Editais em {ufUpper}</p>
                <p className="text-2xl font-bold text-ink">{stats.total_editais}</p>
              </div>
              <div className="p-4 rounded-lg border border-[var(--border)] text-center">
                <p className="text-sm text-ink-secondary mb-1">Valor Médio</p>
                <p className="text-2xl font-bold text-ink">{formatBRL(stats.avg_value)}</p>
              </div>
            </div>
          )}

          {/* Top 5 Opportunities */}
          {stats && stats.top_oportunidades.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Top oportunidades da semana
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
                      {item.valor && <span>{formatBRL(item.valor)}</span>}
                      {item.data && <span>{item.data}</span>}
                    </div>
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
            ufCode={ufUpper}
            count={stats?.total_editais}
            slug={slug}
          />

          {/* Context paragraph (300+ words about sector in this UF) */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              {sector.name} {getUfPrep(ufUpper)} {ufName}: panorama de licitações
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              <p>
                O estado de {ufName} ({ufUpper}) é um dos mercados mais relevantes para licitações
                de {sector.name} no Brasil. A concentração de órgãos públicos federais, estaduais
                e municipais gera um fluxo constante de oportunidades para empresas do setor.
                A análise dos editais publicados nos últimos 10 dias no PNCP revela
                {stats?.total_editais ? ` ${stats.total_editais} processos licitatórios` : ' diversas oportunidades'} relevantes
                para {sector.name.toLowerCase()}.
              </p>
              <p>
                Para empresas que buscam expandir ou consolidar sua presença {getUfPrep(ufUpper)} {ufName}, a chave
                está na análise de viabilidade prévia. Dos editais publicados, nem todos são
                oportunidades reais — fatores como modalidade de contratação, prazo de entrega,
                valor estimado e distância geográfica determinam se vale a pena investir tempo
                e recursos na elaboração de uma proposta. O SmartLic automatiza essa triagem
                usando 4 fatores de viabilidade, economizando horas de análise manual.
              </p>
              <p>
                As modalidades mais comuns para {sector.name.toLowerCase()} {getUfPrep(ufUpper)} {ufName} incluem
                o pregão eletrônico (para compras de menor complexidade técnica) e a concorrência
                (para contratos de maior vulto). A Lei 14.133/2021 consolidou o pregão eletrônico
                como modalidade preferencial para aquisições de bens e serviços comuns, o que
                beneficia empresas com experiência em plataformas de compras eletrônicas como
                ComprasNet e Bolsa Eletrônica.
              </p>
              <p>
                O histórico de preços praticados {getUfPrep(ufUpper)} {ufName} serve como referência para a
                formulação de propostas competitivas. Empresas que monitoram sistematicamente
                os valores de adjudicação em editais similares conseguem precificar com mais
                precisão, equilibrando competitividade com margem de lucro sustentável.
              </p>
            </div>
          </section>

          {/* FAQ */}
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
            uf={ufName}
            ufCode={ufUpper}
            count={stats?.total_editais}
            slug={slug}
          />

          {/* Related Pages */}
          <RelatedPages
            sectorId={sector.id}
            currentUf={ufUpper}
            currentType="sector-uf"
          />
        </div>
      </main>

      <Footer />
    </div>
  );
}
