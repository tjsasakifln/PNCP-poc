import { Metadata } from 'next';
import { buildCanonical, SITE_URL, getFreshnessLabel } from '@/lib/seo';
import ContentPageLayout from '../components/ContentPageLayout';
import EstatisticasClient from './EstatisticasClient';

export const revalidate = 21600; // 6h ISR

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export const metadata: Metadata = {
  title: 'Estatísticas de Licitações Públicas no Brasil',
  description:
    'Dados atualizados de licitações públicas no Brasil: total de editais, valores médios por setor e UF, tendências. Fonte: PNCP. Cite livremente.',
  alternates: {
    canonical: buildCanonical('/estatisticas'),
  },
  openGraph: {
    title: 'Estatísticas de Licitações Públicas no Brasil | SmartLic',
    description:
      'Dados do PNCP atualizados a cada 6 horas: total de editais, valores médios, top setores e UFs.',
    url: buildCanonical('/estatisticas'),
    type: 'website',
    images: [
      {
        url: '/api/og?title=Estatísticas+de+Licitações+Públicas',
        width: 1200,
        height: 630,
        alt: 'Estatísticas de Licitações Públicas no Brasil — SmartLic',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Estatísticas de Licitações Públicas no Brasil | SmartLic',
    description:
      'Dados do PNCP atualizados a cada 6 horas: total de editais, valores médios, top setores e UFs.',
    images: ['/api/og?title=Estatísticas+de+Licitações+Públicas'],
  },
};

// ---------------------------------------------------------------------------
// JSON-LD schemas
// ---------------------------------------------------------------------------

function buildDatasetSchema(updatedAt: string) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: 'Estatísticas de Licitações Públicas no Brasil',
    description:
      'Agregações de contratações públicas publicadas no PNCP — total de editais, valores estimados, distribuição por UF, setor e modalidade.',
    url: buildCanonical('/estatisticas'),
    creator: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: SITE_URL,
    },
    publisher: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: SITE_URL,
    },
    license: 'https://creativecommons.org/licenses/by/4.0/',
    dateModified: updatedAt,
    temporalCoverage: 'Últimos 30 dias',
    spatialCoverage: {
      '@type': 'Place',
      name: 'Brasil',
    },
    isBasedOn: {
      '@type': 'DataCatalog',
      name: 'PNCP — Portal Nacional de Contratações Públicas',
      url: 'https://pncp.gov.br',
    },
  };
}

const breadcrumbSchema = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'Início',
      item: SITE_URL,
    },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Estatísticas',
      item: buildCanonical('/estatisticas'),
    },
  ],
};

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

interface PublicStat {
  id: string;
  label: string;
  value: number;
  formatted_value: string;
  unit: string;
  context: string;
  source: string;
  period: string;
  sector?: string | null;
  uf?: string | null;
}

interface StatsResponse {
  updated_at: string;
  total_stats: number;
  stats: PublicStat[];
}

async function fetchStats(): Promise<StatsResponse> {
  const baseUrl =
    process.env.BACKEND_URL ||
    (typeof window === 'undefined' ? 'http://localhost:8000' : '');

  try {
    const resp = await fetch(`${baseUrl}/v1/stats/public`, {
      next: { revalidate: 21600 },
      signal: AbortSignal.timeout(8000),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error('estatisticas: failed to fetch stats', err);
    return { updated_at: new Date().toISOString(), total_stats: 0, stats: [] };
  }
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default async function EstatisticasPage() {
  const data = await fetchStats();
  const freshnessLabel = getFreshnessLabel(data.updated_at);
  const datasetSchema = buildDatasetSchema(data.updated_at);

  return (
    <ContentPageLayout
      breadcrumbLabel="Estatísticas de Licitações"
      relatedPages={[
        { href: '/calculadora', title: 'Calculadora de Oportunidades B2G' },
        { href: '/licitacoes', title: 'Licitações por Setor' },
        { href: '/glossario', title: 'Glossário de Licitações' },
      ]}
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      {/* Header */}
      <h1>Estatísticas de Licitações Públicas no Brasil</h1>
      <p className="lead">
        Dados atualizados do PNCP · Atualizados a cada 6 horas · Cite livremente
      </p>
      <p className="text-gray-600 text-sm mb-4">
        Todas as estatísticas abaixo são calculadas a partir do banco de dados do PNCP
        (Portal Nacional de Contratações Públicas) processado pelo SmartLic.
        Clique em <strong>Citar esta estatística</strong> para obter um snippet HTML com
        blockquote e backlink, ou <strong>Copiar citação</strong> para o formato
        acadêmico ABNT.
      </p>

      {/* Client component handles copy interaction and formatting */}
      <EstatisticasClient
        stats={data.stats}
        updatedAt={data.updated_at}
        freshnessLabel={freshnessLabel}
      />

      {/* CTA */}
      <section className="mt-12 rounded-xl bg-indigo-50 border border-indigo-100 p-6 text-center">
        <h2 className="text-xl font-semibold text-indigo-900 mb-2">
          Analise editais do seu setor em tempo real
        </h2>
        <p className="text-indigo-700 text-sm mb-4">
          Filtre oportunidades por setor, UF e valor. 14 dias grátis, sem cartão de crédito.
        </p>
        <a
          href="/signup"
          className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg px-6 py-2.5 text-sm transition-colors"
        >
          Começar análise gratuita
        </a>
      </section>

      {/* Methodology */}
      <section className="mt-10">
        <h2>Metodologia</h2>
        <p>
          As estatísticas desta página são calculadas sobre os editais indexados pelo SmartLic
          a partir do PNCP (Portal Nacional de Contratações Públicas) nos últimos 30 dias
          corridos. O banco de dados é atualizado três vezes ao dia (08h, 14h e 20h BRT).
        </p>
        <p className="mt-2">
          A classificação por setor utiliza correspondência de palavras-chave no objeto da
          contratação. Valores estimados ausentes ou zerados não são incluídos nos cálculos
          de médias e medianas. Os dados são públicos e podem ser citados com atribuição ao
          SmartLic e ao PNCP.
        </p>
        <h3>Fonte primária</h3>
        <p>
          <a
            href="https://pncp.gov.br"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:underline"
          >
            PNCP — Portal Nacional de Contratações Públicas
          </a>{' '}
          · API de consulta de contratações públicas brasileiras (Lei 14.133/2021).
        </p>
      </section>

      {/* Internal links */}
      <section className="mt-8">
        <h2>Explore mais dados</h2>
        <ul className="space-y-1">
          <li>
            <a href="/calculadora" className="text-indigo-600 hover:underline">
              Calculadora de Oportunidades B2G
            </a>{' '}
            — descubra o valor que sua empresa está deixando na mesa
          </li>
          <li>
            <a href="/licitacoes" className="text-indigo-600 hover:underline">
              Licitações por Setor
            </a>{' '}
            — editais organizados por área de atuação
          </li>
          <li>
            <a href="/glossario" className="text-indigo-600 hover:underline">
              Glossário de Licitações
            </a>{' '}
            — terminologia das contratações públicas
          </li>
        </ul>
      </section>
    </ContentPageLayout>
  );
}
