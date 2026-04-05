import { Metadata } from 'next';
import ContentPageLayout from '../components/ContentPageLayout';
import CnpjSearchForm from './CnpjSearchForm';

export const metadata: Metadata = {
  title: 'Consulta CNPJ B2G — Histórico de Contratos Públicos | SmartLic',
  description:
    'Consulte o histórico de contratos públicos de qualquer empresa por CNPJ. Score B2G, setor detectado e oportunidades abertas. Dados do PNCP e Portal da Transparência.',
  alternates: {
    canonical: 'https://smartlic.tech/cnpj',
  },
  openGraph: {
    title: 'Consulta CNPJ B2G — Histórico de Contratos Públicos',
    description:
      'Consulte o histórico de contratos públicos de qualquer empresa por CNPJ. Dados reais do Portal da Transparência.',
    url: 'https://smartlic.tech/cnpj',
    type: 'website',
    images: [
      {
        url: '/api/og?title=Consulta+CNPJ+B2G',
        width: 1200,
        height: 630,
        alt: 'Consulta CNPJ B2G — SmartLic',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Consulta CNPJ B2G — Histórico de Contratos Públicos',
    description: 'Consulte gratuitamente o histórico B2G de qualquer empresa.',
    images: ['/api/og?title=Consulta+CNPJ+B2G'],
  },
};

const breadcrumbSchema = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    { '@type': 'ListItem', position: 1, name: 'Início', item: 'https://smartlic.tech' },
    { '@type': 'ListItem', position: 2, name: 'Consulta CNPJ B2G', item: 'https://smartlic.tech/cnpj' },
  ],
};

const faqSchema = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'De onde vêm os dados?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Os dados de contratos vêm do Portal da Transparência do Governo Federal. Os dados cadastrais vêm de fontes públicas (CNPJ aberto). Os editais abertos vêm do PNCP.',
      },
    },
    {
      '@type': 'Question',
      name: 'Preciso me cadastrar?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Não. A consulta por CNPJ é 100% gratuita e não requer cadastro. Para acessar análise detalhada de editais, você pode criar um trial gratuito de 14 dias.',
      },
    },
    {
      '@type': 'Question',
      name: 'Como é calculado o Score B2G?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'O Score B2G classifica empresas em três níveis: Ativo (5+ contratos públicos nos últimos 24 meses), Iniciante (1-4 contratos no período) e Sem Histórico (nenhum contrato público rastreado). O cálculo considera apenas dados públicos do Portal da Transparência e PNCP.',
      },
    },
    {
      '@type': 'Question',
      name: 'Os dados são em tempo real?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Os contratos do Portal da Transparência são atualizados diariamente pelo Governo Federal. Os editais abertos do PNCP são consultados ao vivo a cada requisição. A consulta reflete o estado mais recente disponível nas fontes oficiais.',
      },
    },
    {
      '@type': 'Question',
      name: 'Posso consultar qualquer CNPJ?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Sim. A ferramenta aceita qualquer CNPJ válido de empresa ativa no Brasil. Não há limite de consultas, não exige cadastro e não há custo.',
      },
    },
  ],
};

const softwareApplicationSchema = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'SmartLic — Consulta CNPJ B2G',
  url: 'https://smartlic.tech/cnpj',
  applicationCategory: 'BusinessApplication',
  applicationSubCategory: 'GovTech',
  operatingSystem: 'Web',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'BRL',
  },
  featureList: [
    'Consulta de contratos públicos por CNPJ',
    'Score B2G (Ativo, Iniciante, Sem Histórico)',
    'Histórico do Portal da Transparência e PNCP',
    'Detecção automática de setor via CNAE',
    'Oportunidades de editais abertos no setor e UF da empresa',
  ],
  provider: {
    '@type': 'Organization',
    name: 'SmartLic',
    url: 'https://smartlic.tech',
    legalName: 'CONFENGE Avaliações e Inteligência Artificial LTDA',
  },
  inLanguage: 'pt-BR',
  isAccessibleForFree: true,
};

const websiteSearchActionSchema = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  url: 'https://smartlic.tech/cnpj',
  name: 'Consulta CNPJ B2G — SmartLic',
  potentialAction: {
    '@type': 'SearchAction',
    target: {
      '@type': 'EntryPoint',
      urlTemplate: 'https://smartlic.tech/cnpj?q={search_term_string}',
    },
    'query-input': 'required name=search_term_string',
  },
};

export default function CnpjLandingPage() {
  return (
    <ContentPageLayout
      breadcrumbLabel="Consulta CNPJ B2G"
      relatedPages={[
        { href: '/calculadora', title: 'Calculadora de Oportunidades B2G' },
        { href: '/licitacoes', title: 'Licitações por Setor' },
        { href: '/como-avaliar-licitacao', title: 'Como Avaliar uma Licitação' },
      ]}
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareApplicationSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSearchActionSchema) }}
      />

      <h1>Consulta CNPJ B2G — Histórico de Contratos Públicos</h1>
      <p className="lead">
        Descubra o histórico de contratos com o governo de qualquer empresa.
        Dados reais do Portal da Transparência e PNCP.
      </p>

      <CnpjSearchForm />

      <section className="mt-12">
        <h2>O que você verá</h2>
        <ul>
          <li><strong>Dados cadastrais</strong> — Razão social, CNAE, porte, UF</li>
          <li><strong>Contratos públicos</strong> — Últimos contratos com órgãos governamentais</li>
          <li><strong>Score B2G</strong> — Ativo, Iniciante ou Sem Histórico</li>
          <li><strong>Setor detectado</strong> — Baseado no CNAE principal da empresa</li>
          <li><strong>Oportunidades abertas</strong> — Editais abertos no setor e UF da empresa</li>
        </ul>

        <h2>Perguntas Frequentes</h2>

        <h3>De onde vêm os dados?</h3>
        <p>
          Os dados de contratos vêm do Portal da Transparência do Governo Federal.
          Os dados cadastrais vêm de fontes públicas (CNPJ aberto).
          Os editais abertos vêm do PNCP.
        </p>

        <h3>Preciso me cadastrar?</h3>
        <p>
          Não. A consulta por CNPJ é 100% gratuita e não requer cadastro.
          Para acessar análise detalhada de editais, você pode criar um trial gratuito de 14 dias.
        </p>

        <h3>Como é calculado o Score B2G?</h3>
        <p>
          O Score B2G classifica empresas em três níveis: <strong>Ativo</strong> (5+ contratos
          públicos nos últimos 24 meses), <strong>Iniciante</strong> (1-4 contratos no período)
          e <strong>Sem Histórico</strong> (nenhum contrato público rastreado). O cálculo
          considera apenas dados públicos do Portal da Transparência e PNCP.
        </p>

        <h3>Os dados são em tempo real?</h3>
        <p>
          Os contratos do Portal da Transparência são atualizados diariamente pelo Governo
          Federal. Os editais abertos do PNCP são consultados ao vivo a cada requisição.
          A consulta reflete o estado mais recente disponível nas fontes oficiais.
        </p>

        <h3>Posso consultar qualquer CNPJ?</h3>
        <p>
          Sim. A ferramenta aceita qualquer CNPJ válido de empresa ativa no Brasil. Não há
          limite de consultas, não exige cadastro e não há custo.
        </p>
      </section>
    </ContentPageLayout>
  );
}
