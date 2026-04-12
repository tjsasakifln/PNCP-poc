/**
 * STORY-431 AC1: Observatory hub — /observatorio
 *
 * Hub com lista de relatórios publicados. Link no rodapé e nav.
 * Schema.org: Dataset collection.
 */

import { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Observatório de Licitações',
  description:
    'Análise mensal do mercado de compras públicas do Brasil. Dados reais do PNCP processados por IA: total de editais, setores em alta, valores e distribuição por modalidade.',
  alternates: { canonical: 'https://smartlic.tech/observatorio' },
  openGraph: {
    title: 'Observatório SmartLic — Raio-X das Licitações Públicas do Brasil',
    description:
      'Relatórios mensais com dados reais do PNCP: volume de editais, setores em alta, valores médios e tendências por UF e modalidade.',
    url: 'https://smartlic.tech/observatorio',
    type: 'website',
    locale: 'pt_BR',
  },
  robots: { index: true },
};

const datasetSchema = {
  '@context': 'https://schema.org',
  '@type': 'Dataset',
  name: 'Observatório SmartLic — Licitações Públicas do Brasil',
  description:
    'Série histórica de relatórios mensais sobre o mercado de compras públicas brasileiras, compilados a partir dos dados do PNCP (Portal Nacional de Contratações Públicas).',
  url: 'https://smartlic.tech/observatorio',
  license: 'https://creativecommons.org/licenses/by/4.0/',
  creator: {
    '@type': 'Organization',
    name: 'SmartLic — CONFENGE Avaliações e Inteligência Artificial LTDA',
    url: 'https://smartlic.tech',
  },
  temporalCoverage: '2024/..',
  spatialCoverage: 'Brasil',
  keywords: 'licitações públicas, compras governamentais, PNCP, Brasil, pregão eletrônico',
  inLanguage: 'pt-BR',
};

// Relatórios publicados — atualizar a cada novo mês
const RELATORIOS_PUBLICADOS = [
  {
    slug: 'raio-x-marco-2026',
    titulo: 'Raio-X das Licitações — Março 2026',
    mes: 3,
    ano: 2026,
    descricao: 'Volume, valores e tendências das licitações públicas brasileiras em março de 2026.',
    publicado_em: '2026-04-11',
  },
];

export default function ObservatorioPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetSchema) }}
      />

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Observatório de Licitações Públicas
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl">
            Relatórios mensais com dados reais do PNCP: volume de editais, setores em alta,
            valores médios e distribuição por modalidade em todo o Brasil.
            Licença Creative Commons BY 4.0 — livre para citar e republicar com atribuição.
          </p>
        </div>

        <section>
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Relatórios publicados</h2>

          {RELATORIOS_PUBLICADOS.length === 0 ? (
            <p className="text-gray-500">Primeiro relatório em breve.</p>
          ) : (
            <div className="space-y-4">
              {RELATORIOS_PUBLICADOS.map((rel) => (
                <Link
                  key={rel.slug}
                  href={`/observatorio/${rel.slug}`}
                  className="block p-5 bg-white border border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-sm transition-all"
                >
                  <h3 className="text-lg font-semibold text-blue-700 mb-1">{rel.titulo}</h3>
                  <p className="text-gray-600 text-sm mb-2">{rel.descricao}</p>
                  <span className="text-xs text-gray-400">
                    Publicado em {new Date(rel.publicado_em).toLocaleDateString('pt-BR')}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </section>

        <section className="mt-12 p-6 bg-blue-50 rounded-xl border border-blue-100">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Sobre os dados</h2>
          <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
            <li>Fonte: PNCP (Portal Nacional de Contratações Públicas)</li>
            <li>Processamento: SmartLic — classificação por IA e agregação</li>
            <li>Atualização: relatório publicado até o dia 11 do mês seguinte</li>
            <li>Licença: Creative Commons BY 4.0 — cite como "SmartLic Observatório (smartlic.tech/observatorio)"</li>
            <li>Disponível via API: <code className="text-xs bg-white px-1 rounded">GET /v1/observatorio/relatorio/{'{mes}'}/{'{ano}'}</code></li>
          </ul>
        </section>
      </main>
    </>
  );
}
