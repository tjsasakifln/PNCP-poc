import { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import {
  SECTORS,
  getSectorBySlug,
  getAllSectorSlugs,
  getRelatedSectors,
  fetchSectorStats,
  formatBRL,
  SectorStats,
} from "@/lib/sectors";
import { getSectorFaqs } from "@/data/sector-faqs";

/**
 * STORY-324 AC5: SSG with ISR 6h for sector landing pages.
 */
export const revalidate = 21600; // 6h ISR

export function generateStaticParams() {
  return getAllSectorSlugs().map((setor) => ({ setor }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ setor: string }>;
}): Promise<Metadata> {
  const { setor } = await params;
  const sector = getSectorBySlug(setor);
  if (!sector) return { title: "Setor não encontrado" };

  const stats = await fetchSectorStats(setor);
  const totalOpen = stats?.total_open ?? 0;
  const topUfs = stats?.top_ufs?.slice(0, 3).map((u) => u.name).join(", ") || "todo o Brasil";
  const canonicalUrl = `https://smartlic.tech/licitacoes/${setor}`;

  // AC9: Meta tags
  return {
    title: `Licitações de ${sector.name} — ${totalOpen > 0 ? `${totalOpen} Oportunidades Abertas` : "Oportunidades Abertas"}`,
    description: `Encontre ${totalOpen > 0 ? totalOpen : ""} licitações abertas de ${sector.name} em ${topUfs}. Analise com IA e score de viabilidade. 14 dias grátis.`,
    alternates: {
      canonical: canonicalUrl,
    },
    // AC11: Open Graph
    openGraph: {
      title: `Licitações de ${sector.name} — Oportunidades Abertas | SmartLic`,
      description: `Encontre licitações abertas de ${sector.name}. Analise a viabilidade com IA. 14 dias grátis.`,
      url: canonicalUrl,
      type: "website",
      locale: "pt_BR",
      siteName: "SmartLic",
      images: [
        {
          url: `/api/og?title=${encodeURIComponent(`Licitações de ${sector.name}`)}&category=${encodeURIComponent(sector.name)}`,
          width: 1200,
          height: 630,
          alt: `Licitações de ${sector.name} | SmartLic`,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: `Licitações de ${sector.name} | SmartLic`,
      description: `Encontre licitações abertas de ${sector.name}. Analise a viabilidade com IA.`,
    },
  };
}

export default async function SectorPage({
  params,
}: {
  params: Promise<{ setor: string }>;
}) {
  const { setor } = await params;
  const sector = getSectorBySlug(setor);
  if (!sector) notFound();

  const stats = await fetchSectorStats(setor);
  const faqs = getSectorFaqs(sector.id);
  const relatedSectors = getRelatedSectors(setor);

  return (
    <main className="min-h-screen bg-white dark:bg-gray-950">
      {/* AC6: Hero */}
      <section className="bg-gradient-to-br from-brand-blue to-blue-700 text-white py-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-3xl md:text-5xl font-bold mb-4">
            Licitações de {sector.name}
            {stats && stats.total_open > 0 && (
              <span className="block text-2xl md:text-3xl font-normal text-blue-200 mt-2">
                {stats.total_open} oportunidades abertas
              </span>
            )}
          </h1>
          <p className="text-lg text-blue-100 max-w-2xl mx-auto">
            {sector.description}. Encontre e analise oportunidades com inteligência artificial.
          </p>
        </div>
      </section>

      {/* AC6: Stats Cards */}
      {stats && stats.total_open > 0 && (
        <section className="max-w-5xl mx-auto -mt-8 px-4 relative z-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatsCard label="Abertas" value={String(stats.total_open)} />
            <StatsCard label="Valor Total" value={formatBRL(stats.total_value)} />
            <StatsCard label="Valor Médio" value={formatBRL(stats.avg_value)} />
            <StatsCard
              label="Top UFs"
              value={stats.top_ufs.slice(0, 3).map((u) => u.name).join(", ") || "—"}
            />
          </div>
        </section>
      )}

      {/* AC6: Sample Table */}
      {stats && stats.sample_items.length > 0 && (
        <section className="max-w-5xl mx-auto py-12 px-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Exemplos de licitações abertas
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 uppercase bg-gray-50 dark:bg-gray-800 dark:text-gray-400">
                <tr>
                  <th className="px-4 py-3">Objeto</th>
                  <th className="px-4 py-3">Órgão</th>
                  <th className="px-4 py-3">Valor Est.</th>
                  <th className="px-4 py-3">UF</th>
                  <th className="px-4 py-3">Data</th>
                </tr>
              </thead>
              <tbody>
                {stats.sample_items.map((item, i) => (
                  <tr
                    key={i}
                    className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                  >
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white max-w-xs truncate">
                      {item.titulo}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 max-w-[200px] truncate">
                      {item.orgao}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {item.valor ? formatBRL(item.valor) : "N/I"}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {item.uf}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 whitespace-nowrap">
                      {item.data}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* AC6: CTA */}
      <section className="bg-brand-blue/5 dark:bg-brand-blue/10 py-12 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
            Veja todas as {stats?.total_open || ""} oportunidades de {sector.name}
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Análise de viabilidade com IA, filtros por região e valor, alertas por email.
          </p>
          <Link
            href="/signup"
            className="inline-block px-8 py-3 bg-brand-blue text-white font-semibold
                       rounded-lg hover:bg-blue-700 transition-colors text-lg"
          >
            14 dias grátis — Comece agora
          </Link>
        </div>
      </section>

      {/* AC6: Como Funciona */}
      <section className="max-w-5xl mx-auto py-16 px-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-8 text-center">
          Como funciona
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <HowItWorksStep
            step={1}
            title="Busque"
            description="O SmartLic busca licitações em PNCP, PCP e ComprasGov simultaneamente, cobrindo todas as fontes oficiais."
          />
          <HowItWorksStep
            step={2}
            title="Filtre"
            description="IA classifica cada licitação por relevância ao seu setor, eliminando falsos positivos automaticamente."
          />
          <HowItWorksStep
            step={3}
            title="Analise"
            description="Score de viabilidade considera modalidade, prazo, valor e região para priorizar as melhores oportunidades."
          />
        </div>
      </section>

      {/* AC6/AC17: FAQ */}
      {faqs.length > 0 && (
        <section className="bg-gray-50 dark:bg-gray-900 py-16 px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-8 text-center">
              Perguntas frequentes sobre licitações de {sector.name}
            </h2>
            <div className="space-y-6">
              {faqs.map((faq, i) => (
                <details
                  key={i}
                  className="group bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <summary className="flex items-center justify-between p-5 cursor-pointer font-medium text-gray-900 dark:text-white">
                    {faq.question}
                    <span className="ml-2 text-gray-400 group-open:rotate-180 transition-transform">
                      ▼
                    </span>
                  </summary>
                  <div className="px-5 pb-5 text-gray-600 dark:text-gray-400 leading-relaxed">
                    {faq.answer}
                  </div>
                </details>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* AC16: Related Sectors */}
      <section className="max-w-5xl mx-auto py-12 px-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
          Setores relacionados
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {relatedSectors.map((rs) => (
            <Link
              key={rs.slug}
              href={`/licitacoes/${rs.slug}`}
              className="p-4 rounded-lg border border-gray-200 dark:border-gray-700
                         hover:border-brand-blue hover:shadow transition-all
                         bg-white dark:bg-gray-900"
            >
              <h3 className="font-medium text-sm text-gray-900 dark:text-white">
                {rs.name}
              </h3>
            </Link>
          ))}
        </div>
      </section>

      {/* Footer: All sectors */}
      <section className="border-t border-gray-200 dark:border-gray-800 py-8 px-4">
        <div className="max-w-5xl mx-auto">
          <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-4">
            Todos os setores
          </h3>
          <div className="flex flex-wrap gap-2">
            {SECTORS.map((s) => (
              <Link
                key={s.slug}
                href={`/licitacoes/${s.slug}`}
                className={`text-sm px-3 py-1 rounded-full border transition-colors
                  ${s.slug === setor
                    ? "bg-brand-blue text-white border-brand-blue"
                    : "text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-brand-blue hover:text-brand-blue"
                  }`}
              >
                {s.name}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* AC10: JSON-LD Schema markup */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(buildJsonLd(sector, stats)),
        }}
      />

      {/* FAQ JSON-LD for rich snippets */}
      {faqs.length > 0 && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "FAQPage",
              mainEntity: faqs.map((faq) => ({
                "@type": "Question",
                name: faq.question,
                acceptedAnswer: {
                  "@type": "Answer",
                  text: faq.answer,
                },
              })),
            }),
          }}
        />
      )}
    </main>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatsCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-md p-5 text-center border border-gray-100 dark:border-gray-800">
      <p className="text-2xl font-bold text-brand-blue">{value}</p>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{label}</p>
    </div>
  );
}

function HowItWorksStep({
  step,
  title,
  description,
}: {
  step: number;
  title: string;
  description: string;
}) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-brand-blue/10 text-brand-blue flex items-center justify-center text-xl font-bold">
        {step}
      </div>
      <h3 className="font-semibold text-gray-900 dark:text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// JSON-LD builder (AC10)
// ---------------------------------------------------------------------------

function buildJsonLd(
  sector: { name: string; slug: string; description: string },
  stats: SectorStats | null,
) {
  const jsonLd: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: `Licitações de ${sector.name}`,
    description: `Encontre licitações abertas de ${sector.name}. ${sector.description}`,
    url: `https://smartlic.tech/licitacoes/${sector.slug}`,
    publisher: {
      "@type": "Organization",
      name: "SmartLic",
      url: "https://smartlic.tech",
    },
  };

  // AC10: ItemList for sample_items
  if (stats && stats.sample_items.length > 0) {
    jsonLd.mainEntity = {
      "@type": "ItemList",
      numberOfItems: stats.total_open,
      itemListElement: stats.sample_items.map((item, i) => ({
        "@type": "ListItem",
        position: i + 1,
        name: item.titulo,
        description: `${item.orgao} — ${item.uf}`,
      })),
    };
  }

  return jsonLd;
}
