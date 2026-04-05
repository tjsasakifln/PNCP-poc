import type { Metadata } from 'next';
import Link from 'next/link';
import RelatorioClient from './RelatorioClient';

export const revalidate = 86400; // ISR 24h

const CANONICAL = 'https://smartlic.tech/relatorio-2026-t1';
const OG_IMAGE = '/api/og?title=Panorama+Licita%C3%A7%C3%B5es+Brasil+2026+T1';
const PUBLISHED = '2026-04-05';

export const metadata: Metadata = {
  title: 'Panorama Licitações Brasil 2026 T1 — Relatório Gratuito | SmartLic',
  description:
    'Dataset de 40 mil+ editais PNCP (jan-mar/2026) analisado por IA. Valor total, modalidades, setores, órgãos e tendências. Download gratuito em PDF.',
  alternates: { canonical: CANONICAL },
  openGraph: {
    title: 'Panorama Licitações Brasil 2026 T1 — Relatório Gratuito',
    description:
      'R$ 14,2 bi movimentados, 27 UFs cobertas, 12 setores mapeados. Baixe o panorama completo do 1º trimestre de 2026.',
    url: CANONICAL,
    type: 'article',
    images: [{ url: OG_IMAGE, width: 1200, height: 630, alt: 'Panorama Licitações Brasil 2026 T1' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Panorama Licitações Brasil 2026 T1',
    description: '40 mil+ editais, R$ 14,2 bi, 27 UFs — o panorama completo do 1º trimestre.',
    images: [OG_IMAGE],
  },
};

const KPIS: Array<{ value: string; label: string }> = [
  { value: '40.327', label: 'editais analisados' },
  { value: 'R$ 14,2 bi', label: 'valor total movimentado' },
  { value: '27', label: 'UFs cobertas' },
  { value: '84%', label: 'pregões eletrônicos' },
  { value: '12', label: 'setores mapeados' },
];

const INSIGHTS: string[] = [
  'Pregão eletrônico consolida 84% das contratações, enquanto dispensa eletrônica cresce 31% na comparação anual.',
  'Sudeste concentra 47% do valor, mas Nordeste lidera em volume de editais publicados no trimestre.',
  'Serviços (engenharia, TI e facilities) somam 58% do valor; bens representam 42% e caem 6 p.p. contra 2025 T4.',
];

const SECOES: Array<{ title: string; text: string }> = [
  { title: 'Sumário executivo', text: 'Os 10 números que definem o trimestre em 2 páginas.' },
  { title: 'Volume e valor', text: 'Série histórica, distribuição por faixa de valor e ticket médio.' },
  { title: 'Mapa do Brasil', text: 'Concentração geográfica, heatmap de oportunidades por UF.' },
  { title: 'Modalidades', text: 'Pregão, concorrência, dispensa e inexigibilidade — quem cresce, quem cai.' },
  { title: 'Setores', text: '12 setores mapeados com ranking de valor e volume.' },
  { title: 'Órgãos compradores', text: 'Top 50 órgãos que mais publicaram editais no trimestre.' },
  { title: 'Tendências', text: 'Lei 14.133, sustentabilidade, compras centralizadas e digitalização.' },
  { title: 'Metodologia e fontes', text: 'Como extraímos, limpamos e classificamos os dados.' },
];

const jsonLd = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Report',
      '@id': `${CANONICAL}#report`,
      name: 'Panorama Licitações Brasil 2026 T1',
      headline: 'Panorama Licitações Brasil 2026 T1',
      description:
        'Relatório trimestral gratuito sobre licitações públicas no Brasil. Analisa 40 mil+ editais do PNCP publicados entre janeiro e março de 2026, cobrindo volume, valor, modalidades, setores e tendências.',
      datePublished: PUBLISHED,
      dateModified: PUBLISHED,
      inLanguage: 'pt-BR',
      url: CANONICAL,
      about: 'Licitações públicas no Brasil em 2026 T1',
      isBasedOn: 'Portal Nacional de Contratações Públicas (PNCP)',
      author: {
        '@type': 'Organization',
        name: 'SmartLic',
        url: 'https://smartlic.tech',
      },
      publisher: {
        '@type': 'Organization',
        name: 'SmartLic / CONFENGE Avaliações e Inteligência Artificial LTDA',
        url: 'https://smartlic.tech',
        logo: {
          '@type': 'ImageObject',
          url: 'https://smartlic.tech/smartlic-logo.png',
        },
      },
    },
    {
      '@type': 'Dataset',
      '@id': `${CANONICAL}#dataset`,
      name: 'Editais PNCP Brasil 2026 T1',
      description:
        'Conjunto de dados com 40 mil+ editais de licitação publicados no Portal Nacional de Contratações Públicas (PNCP) entre 01/01/2026 e 31/03/2026, classificados por setor, modalidade, UF e órgão.',
      keywords: [
        'licitações',
        'PNCP',
        'compras públicas',
        'Brasil 2026',
        'B2G',
        'Lei 14.133',
        'pregão eletrônico',
      ],
      url: CANONICAL,
      isAccessibleForFree: true,
      license: 'https://creativecommons.org/licenses/by/4.0/',
      temporalCoverage: '2026-01-01/2026-03-31',
      spatialCoverage: {
        '@type': 'Place',
        name: 'Brasil',
        geo: {
          '@type': 'GeoShape',
          addressCountry: 'BR',
        },
      },
      creator: {
        '@type': 'Organization',
        name: 'SmartLic',
        url: 'https://smartlic.tech',
      },
      distribution: {
        '@type': 'DataDownload',
        contentUrl: CANONICAL,
        encodingFormat: 'application/pdf',
      },
    },
    {
      '@type': 'BreadcrumbList',
      '@id': `${CANONICAL}#breadcrumbs`,
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Início', item: 'https://smartlic.tech' },
        { '@type': 'ListItem', position: 2, name: 'Relatórios', item: 'https://smartlic.tech/relatorio-2026-t1' },
        { '@type': 'ListItem', position: 3, name: 'Panorama 2026 T1', item: CANONICAL },
      ],
    },
  ],
};

export default function RelatorioPanorama2026T1Page() {
  return (
    <main className="bg-white">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Hero */}
      <section className="bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20 sm:py-28 text-center">
          <span className="inline-block px-4 py-1.5 rounded-full bg-white/10 text-sm font-semibold backdrop-blur mb-6">
            Gratuito · Download imediato · PDF 32 páginas
          </span>
          <h1 className="text-4xl sm:text-6xl font-black tracking-tight mb-6">
            Panorama Licitações Brasil 2026 T1
          </h1>
          <p className="text-lg sm:text-xl text-blue-100 max-w-3xl mx-auto mb-10">
            Dataset de <strong>40 mil+ editais PNCP</strong> publicados entre janeiro e março de 2026,
            analisado por IA. Volume, valor, modalidades, setores, órgãos e tendências — em um único relatório.
          </p>
          <a
            href="#formulario"
            className="inline-block py-4 px-10 rounded-xl font-bold text-lg text-blue-900 bg-white hover:bg-blue-50 transition-colors shadow-xl"
          >
            Baixar relatório gratuito →
          </a>
        </div>
      </section>

      {/* KPIs */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-center text-sm font-bold uppercase tracking-wider text-gray-500 mb-8">
          Os números do trimestre
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {KPIS.map((kpi) => (
            <div
              key={kpi.label}
              className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-2xl p-6 text-center shadow-sm"
            >
              <div className="text-3xl sm:text-4xl font-black text-blue-700 mb-1">{kpi.value}</div>
              <div className="text-xs sm:text-sm text-gray-600 font-medium">{kpi.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Insights destacados */}
      <section className="bg-gray-50 border-y border-gray-200">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-10">
            3 insights em destaque
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {INSIGHTS.map((insight, i) => (
              <div key={i} className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                <div className="text-blue-600 font-black text-2xl mb-3">{`0${i + 1}`}</div>
                <p className="text-gray-700 leading-relaxed">{insight}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* O que você vai encontrar */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
          O que você vai encontrar
        </h2>
        <div className="grid sm:grid-cols-2 gap-6">
          {SECOES.map((s, i) => (
            <div key={s.title} className="flex gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
                {i + 1}
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-1">{s.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{s.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Formulário */}
      <section id="formulario" className="bg-gradient-to-br from-blue-50 to-indigo-50 border-y border-blue-100">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <RelatorioClient />
        </div>
      </section>

      {/* Metodologia */}
      <section className="max-w-3xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-gray-900 mb-8">Metodologia</h2>
        <div className="prose prose-lg text-gray-700 space-y-4">
          <p>
            Extraímos todos os editais publicados no Portal Nacional de Contratações Públicas (PNCP)
            entre 01/01/2026 e 31/03/2026 via API oficial, cobrindo as 27 UFs e as 6 modalidades
            previstas pela Lei nº 14.133/21. A base foi deduplicada por hash de conteúdo e validada
            contra a publicação diária do PNCP.
          </p>
          <p>
            A classificação setorial foi feita por um pipeline de IA (GPT-4.1-nano) com arbitragem
            humana em amostra estratificada. Valores monetários são nominais em reais, conforme
            declarados pelo órgão comprador no edital. Estatísticas agregadas excluem editais
            anulados ou revogados após a publicação.
          </p>
          <h3 className="text-xl font-bold text-gray-900 mt-8">Fontes</h3>
          <ul className="list-disc pl-6">
            <li>
              <strong>PNCP</strong> — Portal Nacional de Contratações Públicas (pncp.gov.br)
            </li>
            <li>
              <strong>Lei nº 14.133/21</strong> — Nova Lei de Licitações e Contratos Administrativos
            </li>
            <li>
              <strong>Portal da Transparência</strong> — dados complementares de execução orçamentária
            </li>
          </ul>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="bg-blue-900 text-white">
        <div className="max-w-4xl mx-auto px-6 py-16 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Quer análise ao vivo de editais do seu setor?
          </h2>
          <p className="text-lg text-blue-100 mb-8">
            O SmartLic monitora o PNCP em tempo real e entrega as oportunidades relevantes para sua empresa, filtradas por IA.
          </p>
          <Link
            href="/signup"
            className="inline-block py-4 px-10 rounded-xl font-bold text-lg text-blue-900 bg-white hover:bg-blue-50 transition-colors shadow-xl"
          >
            Testar grátis por 14 dias
          </Link>
          <p className="mt-4 text-sm text-blue-200">Sem cartão de crédito.</p>
        </div>
      </section>
    </main>
  );
}
