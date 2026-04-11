/**
 * STORY-435 AC1: Índice Municipal hub — /indice-municipal
 *
 * Hub com ranking dos municípios por transparência em compras públicas.
 * Schema.org: Dataset.
 */

import { Metadata } from 'next';
import Link from 'next/link';
import IndiceClient from './IndiceClient';

export const metadata: Metadata = {
  title: 'Índice de Transparência Municipal em Compras Públicas | SmartLic',
  description:
    'Ranking dos municípios brasileiros por transparência em compras públicas. Score calculado a partir de dados reais do PNCP: volume, eficiência, diversidade e consistência.',
  alternates: { canonical: 'https://smartlic.tech/indice-municipal' },
  openGraph: {
    title: 'Índice SmartLic — Transparência Municipal em Compras Públicas',
    description:
      'Ranking dos municípios brasileiros por transparência em compras públicas. Score calculado a partir de dados reais do PNCP: volume, eficiência, diversidade e consistência.',
    url: 'https://smartlic.tech/indice-municipal',
    type: 'website',
    locale: 'pt_BR',
  },
  robots: { index: true },
};

const datasetSchema = {
  '@context': 'https://schema.org',
  '@type': 'Dataset',
  name: 'Índice SmartLic de Transparência Municipal em Compras Públicas',
  description:
    'Ranking trimestral dos municípios brasileiros por transparência em compras públicas, calculado a partir de dados do PNCP processados por IA.',
  url: 'https://smartlic.tech/indice-municipal',
  license: 'https://creativecommons.org/licenses/by/4.0/',
  creator: {
    '@type': 'Organization',
    name: 'SmartLic — CONFENGE Avaliações e Inteligência Artificial LTDA',
    url: 'https://smartlic.tech',
  },
  temporalCoverage: '2026/..',
  spatialCoverage: 'Brasil',
  keywords: 'transparência municipal, compras públicas, licitações, PNCP, prefeituras, Brasil',
  inLanguage: 'pt-BR',
};

const DIMENSOES = [
  {
    nome: 'Transparência Digital',
    desc: 'Uso de pregão eletrônico',
    badge: 'bg-blue-100 text-blue-800',
  },
  {
    nome: 'Eficiência Temporal',
    desc: 'Tempo publicação → abertura',
    badge: 'bg-green-100 text-green-800',
  },
  {
    nome: 'Diversidade de Mercado',
    desc: 'Fornecedores únicos atraídos',
    badge: 'bg-purple-100 text-purple-800',
  },
  {
    nome: 'Volume de Publicação',
    desc: 'Total de editais publicados',
    badge: 'bg-orange-100 text-orange-800',
  },
  {
    nome: 'Consistência',
    desc: 'Publicações regulares por mês',
    badge: 'bg-gray-100 text-gray-800',
  },
];

export default function IndiceMunicipalPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetSchema) }}
      />

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Índice de Transparência Municipal em Compras Públicas
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl">
            Ranking trimestral dos municípios brasileiros por transparência em compras públicas.
            Score calculado a partir de dados do PNCP: volume de publicações, eficiência temporal,
            diversidade de mercado, uso do pregão eletrônico e consistência.
          </p>
          <p className="text-sm text-gray-500 mt-3">
            Exemplo:{' '}
            <Link
              href="/indice-municipal/sao-paulo-sp?periodo=2026-Q1"
              className="text-blue-600 hover:underline"
            >
              São Paulo (SP) — 2026-Q1
            </Link>
          </p>
        </div>

        {/* Metodologia */}
        <section className="mb-10 p-6 bg-gray-50 rounded-xl border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">
            Metodologia — 5 dimensões (20 pts cada)
          </h2>
          <div className="flex flex-wrap gap-2">
            {DIMENSOES.map((dim) => (
              <span
                key={dim.nome}
                className={`inline-flex flex-col items-start px-3 py-2 rounded-lg text-xs font-medium ${dim.badge}`}
                title={dim.desc}
              >
                <span className="font-semibold">{dim.nome}</span>
                <span className="font-normal opacity-80">{dim.desc}</span>
              </span>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Score total: soma das 5 dimensões (máximo 100 pontos). Mínimo 10 editais no período.
            Licença{' '}
            <a
              href="https://creativecommons.org/licenses/by/4.0/"
              className="underline"
              target="_blank"
              rel="noopener"
            >
              CC BY 4.0
            </a>
            {' '}— cite: SmartLic Índice Municipal (smartlic.tech/indice-municipal).
          </p>
        </section>

        {/* Ranking interativo */}
        <IndiceClient />

        {/* CTA */}
        <div className="mt-12 p-6 bg-blue-50 rounded-xl border border-blue-100 text-center">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">
            Acompanhe licitações em tempo real
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Receba alertas de novos editais, analise oportunidades e exporte relatórios com IA.
          </p>
          <Link
            href="/buscar"
            className="inline-block bg-blue-600 text-white text-sm font-medium px-5 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Acompanhe licitações em tempo real →
          </Link>
        </div>
      </main>
    </>
  );
}
