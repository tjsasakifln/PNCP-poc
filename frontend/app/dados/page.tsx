import { Metadata } from 'next';
import Link from 'next/link';
import { buildCanonical, SITE_URL, getFreshnessLabel } from '@/lib/seo';
import ContentPageLayout from '@/app/components/ContentPageLayout';
import DadosClient, { DadosData } from './DadosClient';

export const revalidate = 21600;

export const metadata: Metadata = {
  title: 'Dados de Licitações Públicas no Brasil — Painel Interativo',
  description:
    'Painel interativo com dados agregados de licitações públicas do PNCP: editais por setor, UF e modalidade. Atualizado a cada 6 horas. Download em CSV.',
  alternates: { canonical: buildCanonical('/dados') },
  openGraph: {
    title: 'Dados de Licitações Públicas no Brasil | SmartLic',
    description:
      'Painel interativo com dados do PNCP atualizados a cada 6h.',
    url: buildCanonical('/dados'),
    type: 'website',
    siteName: 'SmartLic',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Dados de Licitações Públicas no Brasil | SmartLic',
    description: 'Painel interativo com dados do PNCP atualizados a cada 6h.',
  },
};

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

async function fetchDados(): Promise<DadosData | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/v1/dados/agregados`, {
      next: { revalidate: 21600 },
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

const BRL = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
});

// ---------------------------------------------------------------------------
// JSON-LD structured data
// ---------------------------------------------------------------------------

function buildJsonLd(dados: DadosData | null) {
  const datasetSchema = {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: 'Dados Agregados de Licitações Públicas — PNCP',
    description:
      'Dados agregados de licitações publicadas no Portal Nacional de Contratações Públicas (PNCP), por setor, UF, modalidade e tendência temporal.',
    url: buildCanonical('/dados'),
    creator: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: SITE_URL,
    },
    license: 'https://creativecommons.org/licenses/by/4.0/',
    temporalCoverage: dados
      ? `${dados.period_start}/${dados.period_end}`
      : 'P30D',
    spatialCoverage: {
      '@type': 'Place',
      name: 'Brasil',
    },
    variableMeasured: ['Quantidade de editais', 'Valor estimado', 'Modalidade de contratação'],
    distribution: [
      {
        '@type': 'DataDownload',
        encodingFormat: 'text/csv',
        name: 'Download CSV dos dados agregados',
      },
    ],
  };

  const catalogSchema = {
    '@context': 'https://schema.org',
    '@type': 'DataCatalog',
    name: 'SmartLic — Catálogo de Dados de Licitações',
    description:
      'Dados de licitações públicas extraídos do PNCP, SIASG e outras fontes oficiais.',
    url: buildCanonical('/dados'),
    dataset: [{ '@type': 'Dataset', name: 'Licitações PNCP — Últimos 30 dias' }],
  };

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Início', item: SITE_URL },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Dados de Licitações',
        item: buildCanonical('/dados'),
      },
    ],
  };

  return { datasetSchema, catalogSchema, breadcrumbSchema };
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default async function DadosPage() {
  const dados = await fetchDados();
  const { datasetSchema, catalogSchema, breadcrumbSchema } = buildJsonLd(dados);

  const freshnessLabel = dados?.updated_at
    ? getFreshnessLabel(dados.updated_at)
    : null;

  return (
    <ContentPageLayout
      breadcrumbLabel="Dados de Licitações Públicas"
      relatedPages={[
        { href: '/calculadora', title: 'Calculadora de Oportunidades B2G' },
        { href: '/licitacoes', title: 'Licitações por Setor' },
      ]}
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(catalogSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="mb-6 flex items-center gap-2 text-sm text-gray-500">
        <Link href="/" className="hover:text-blue-600">
          Início
        </Link>
        <span>/</span>
        <span className="text-gray-900">Dados</span>
      </nav>

      {/* Header */}
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          Dados de Licitações Públicas no Brasil
        </h1>
        <p className="text-lg text-gray-600">
          Painel interativo com dados agregados do PNCP · Atualizado a cada 6 horas
        </p>
        {freshnessLabel && (
          <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700 ring-1 ring-green-200">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
            {freshnessLabel}
          </span>
        )}
      </div>

      {/* Summary cards */}
      {dados ? (
        <>
          <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-medium text-gray-500">Total de editais</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {dados.total_bids.toLocaleString('pt-BR')}
              </p>
              <p className="mt-1 text-xs text-gray-400">{dados.period}</p>
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-medium text-gray-500">Valor total estimado</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {BRL.format(dados.total_value)}
              </p>
              <p className="mt-1 text-xs text-gray-400">Soma dos valores estimados</p>
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <p className="text-sm font-medium text-gray-500">Valor médio por edital</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {BRL.format(dados.avg_value)}
              </p>
              <p className="mt-1 text-xs text-gray-400">Média dos valores estimados</p>
            </div>
          </div>

          {/* Interactive charts */}
          <div className="mb-12 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <DadosClient data={dados} />
          </div>
        </>
      ) : (
        <div className="mb-8 rounded-2xl border border-gray-200 bg-gray-50 p-12 text-center">
          <p className="text-gray-500">
            Dados temporariamente indisponíveis. Tente novamente em alguns minutos.
          </p>
        </div>
      )}

      {/* CTA */}
      <div className="mb-12 rounded-2xl bg-blue-600 px-8 py-10 text-center text-white shadow-lg">
        <h2 className="mb-2 text-2xl font-bold">
          Analise editais do seu setor com filtro inteligente
        </h2>
        <p className="mb-6 text-blue-100">
          Deixe a IA qualificar as oportunidades e entregue apenas o que importa para o seu
          negócio.
        </p>
        <Link
          href="/signup"
          className="inline-block rounded-xl bg-white px-8 py-3 text-sm font-bold text-blue-700 shadow hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-white/60"
        >
          Criar conta gratuita — 14 dias sem cartão
        </Link>
      </div>

      {/* Methodology */}
      <section className="mb-10">
        <h2 className="mb-4 text-xl font-bold text-gray-900">Metodologia e fontes</h2>
        <div className="prose prose-sm max-w-none text-gray-600">
          <p>
            Os dados exibidos neste painel são extraídos automaticamente do{' '}
            <strong>PNCP — Portal Nacional de Contratações Públicas</strong>, a base
            oficial mantida pelo Governo Federal que centraliza licitações dos três poderes e
            todos os entes federativos.
          </p>
          <ul>
            <li>
              <strong>Período:</strong> Editais publicados nos últimos 30 dias corridos.
            </li>
            <li>
              <strong>Atualização:</strong> O banco de dados local é atualizado 4×/dia (full
              diário + incrementais a cada 6 horas).
            </li>
            <li>
              <strong>Cobertura:</strong> 27 UFs × 6 modalidades (Pregão Eletrônico, Pregão
              Presencial, Concorrência, Dispensa, Credenciamento, Leilão).
            </li>
            <li>
              <strong>Classificação setorial:</strong> Realizada por correspondência de
              palavras-chave no campo objeto da licitação, com fallback para IA
              (GPT-4.1-nano).
            </li>
            <li>
              <strong>Valores:</strong> Valores estimados informados pelos órgãos no PNCP.
              Editais sem valor informado são contabilizados mas excluídos da soma de valores.
            </li>
          </ul>
        </div>
      </section>

      {/* Internal links */}
      <section className="mb-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Explore mais</h2>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/calculadora"
            className="rounded-lg border border-blue-100 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100"
          >
            Calculadora de Oportunidades B2G
          </Link>
          <Link
            href="/licitacoes"
            className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Licitações por Setor
          </Link>
        </div>
      </section>
    </ContentPageLayout>
  );
}
