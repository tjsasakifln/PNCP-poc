import { Metadata } from "next";
import Link from "next/link";
import { SECTORS, fetchSectorStats, formatBRL } from "@/lib/sectors";

/**
 * STORY-324 AC14: Sector index page — grid of 15 sectors with stats.
 */

export const metadata: Metadata = {
  title: "Licitações por Setor — Oportunidades Abertas",
  description:
    "Encontre licitações abertas em 15 setores: TI, Saúde, Engenharia, Alimentos e mais. Dados reais do PNCP atualizados diariamente.",
  alternates: {
    canonical: "https://smartlic.tech/licitacoes",
  },
  openGraph: {
    title: "Licitações por Setor — Oportunidades Abertas | SmartLic",
    description:
      "Encontre licitações abertas em 15 setores. Dados reais do PNCP atualizados diariamente. 14 dias grátis.",
    url: "https://smartlic.tech/licitacoes",
    type: "website",
    locale: "pt_BR",
  },
};

// Sector icon mapping (emoji for simplicity — no external deps)
const SECTOR_ICONS: Record<string, string> = {
  vestuario: "👔",
  alimentos: "🍎",
  informatica: "💻",
  mobiliario: "🪑",
  papelaria: "📄",
  engenharia: "🏗️",
  software: "🖥️",
  facilities: "🧹",
  saude: "🏥",
  vigilancia: "🔒",
  transporte: "🚛",
  manutencao_predial: "🔧",
  engenharia_rodoviaria: "🛣️",
  materiais_eletricos: "⚡",
  materiais_hidraulicos: "🚰",
};

export default async function LicitacoesIndexPage() {
  // Fetch stats for all sectors in parallel (server-side, ISR 6h)
  const statsPromises = SECTORS.map((s) => fetchSectorStats(s.slug));
  const statsResults = await Promise.all(statsPromises);

  return (
    <main className="min-h-screen bg-white dark:bg-gray-950">
      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-blue to-blue-700 text-white py-16 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Licitações Abertas por Setor
          </h1>
          <p className="text-lg md:text-xl text-blue-100 max-w-3xl mx-auto">
            Encontre oportunidades de licitação em 15 setores da economia.
            Dados reais do PNCP atualizados diariamente.
          </p>
        </div>
      </section>

      {/* Sector Grid */}
      <section className="max-w-6xl mx-auto py-12 px-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {SECTORS.map((sector, i) => {
            const stats = statsResults[i];
            const icon = SECTOR_ICONS[sector.id] || "📋";

            return (
              <Link
                key={sector.slug}
                href={`/licitacoes/${sector.slug}`}
                className="group block p-6 rounded-xl border border-gray-200 dark:border-gray-800
                           hover:border-brand-blue hover:shadow-lg transition-all duration-200
                           bg-white dark:bg-gray-900"
              >
                <div className="flex items-start gap-3 mb-3">
                  <span className="text-2xl" role="img" aria-hidden="true">
                    {icon}
                  </span>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-brand-blue transition-colors">
                    {sector.name}
                  </h2>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {sector.description}
                </p>
                {stats && stats.total_open > 0 ? (
                  <div className="flex items-center gap-4 text-sm">
                    <span className="font-medium text-brand-blue">
                      {stats.total_open} abertas
                    </span>
                    {stats.avg_value > 0 && (
                      <span className="text-gray-500 dark:text-gray-400">
                        Média: {formatBRL(stats.avg_value)}
                      </span>
                    )}
                  </div>
                ) : (
                  <span className="text-sm text-gray-400">
                    Veja oportunidades atualizadas →
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gray-50 dark:bg-gray-900 py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Monitore licitações do seu setor automaticamente
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            O SmartLic busca, filtra e classifica licitações por relevância com IA.
            Economize horas de busca manual.
          </p>
          <Link
            href="/signup"
            className="inline-block px-8 py-3 bg-brand-blue text-white font-semibold
                       rounded-lg hover:bg-blue-700 transition-colors"
          >
            Teste grátis por 14 dias
          </Link>
        </div>
      </section>

      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            name: "Licitações Abertas por Setor",
            description:
              "Encontre oportunidades de licitação pública em 15 setores da economia brasileira.",
            url: "https://smartlic.tech/licitacoes",
            publisher: {
              "@type": "Organization",
              name: "SmartLic",
              url: "https://smartlic.tech",
            },
            numberOfItems: SECTORS.length,
            itemListElement: SECTORS.map((s, i) => ({
              "@type": "ListItem",
              position: i + 1,
              url: `https://smartlic.tech/licitacoes/${s.slug}`,
              name: `Licitações de ${s.name}`,
            })),
          }),
        }}
      />
    </main>
  );
}
