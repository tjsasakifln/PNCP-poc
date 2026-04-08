import { Metadata } from 'next';
import ContentPageLayout from '../components/ContentPageLayout';
import OrgaoSearchForm from './OrgaoSearchForm';
import { LeadCapture } from '@/components/LeadCapture';

export const metadata: Metadata = {
  title: 'Órgãos Compradores — Licitações por Órgão Público | SmartLic',
  description:
    'Consulte o perfil de qualquer órgão comprador público. Total de licitações, valores, modalidades e editais recentes. Dados do PNCP atualizados diariamente.',
  alternates: {
    canonical: 'https://smartlic.tech/orgaos',
  },
  openGraph: {
    title: 'Órgãos Compradores — Licitações por Órgão Público',
    description:
      'Consulte o perfil de qualquer órgão comprador público. Total de licitações, valores e editais recentes do PNCP.',
    url: 'https://smartlic.tech/orgaos',
    type: 'website',
    images: [
      {
        url: '/api/og?title=%C3%93rg%C3%A3os+Compradores',
        width: 1200,
        height: 630,
        alt: 'Órgãos Compradores — SmartLic',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Órgãos Compradores — Licitações por Órgão Público',
    description: 'Consulte gratuitamente o perfil de compras de qualquer órgão público.',
    images: ['/api/og?title=%C3%93rg%C3%A3os+Compradores'],
  },
};

const breadcrumbSchema = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    { '@type': 'ListItem', position: 1, name: 'Início', item: 'https://smartlic.tech' },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Órgãos Compradores',
      item: 'https://smartlic.tech/orgaos',
    },
  ],
};

const faqSchema = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'O que são órgãos compradores?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Órgãos compradores são entidades públicas — prefeituras, autarquias, secretarias, universidades federais, hospitais públicos e outros entes da administração — que publicam licitações para contratar produtos e serviços. Toda compra acima de determinado valor deve ser realizada por meio de processo licitatório aberto e transparente.',
      },
    },
    {
      '@type': 'Question',
      name: 'Como consultar licitações de um órgão?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Informe o CNPJ do órgão comprador no campo acima e clique em "Consultar Órgão". Você verá o perfil completo de compras: total de licitações publicadas, valores contratados, modalidades utilizadas e os editais mais recentes disponíveis no PNCP.',
      },
    },
    {
      '@type': 'Question',
      name: 'De onde vêm os dados?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Os dados vêm do PNCP — Portal Nacional de Contratações Públicas, a base oficial do Governo Federal que centraliza todas as contratações públicas do país. As informações são atualizadas diariamente e refletem o estado mais recente dos processos licitatórios.',
      },
    },
    {
      '@type': 'Question',
      name: 'Preciso me cadastrar?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Não. A consulta de órgãos compradores é 100% gratuita e não exige cadastro. Para acessar análise detalhada de editais, monitoramento automático e alertas, você pode criar um trial gratuito de 14 dias no SmartLic.',
      },
    },
    {
      '@type': 'Question',
      name: 'Quais informações estão disponíveis?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Para cada órgão comprador você encontrará: total de licitações publicadas no período, valor total estimado contratado, modalidades de contratação mais utilizadas (Pregão Eletrônico, Concorrência, Dispensa etc.), setores e segmentos com maior volume de compras e os editais abertos mais recentes com prazos e valores.',
      },
    },
  ],
};

const softwareApplicationSchema = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'SmartLic — Perfil de Órgãos Compradores',
  url: 'https://smartlic.tech/orgaos',
  applicationCategory: 'BusinessApplication',
  applicationSubCategory: 'GovTech',
  operatingSystem: 'Web',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'BRL',
  },
  featureList: [
    'Consulta de perfil de órgãos públicos por CNPJ',
    'Total de licitações publicadas por órgão',
    'Valores contratados e estimados',
    'Modalidades de contratação mais utilizadas',
    'Editais abertos e recentes do PNCP',
    'Setores e segmentos com maior volume de compras',
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

export default function OrgaosLandingPage() {
  return (
    <ContentPageLayout
      breadcrumbLabel="Órgãos Compradores"
      relatedPages={[
        { href: '/calculadora', title: 'Calculadora de Oportunidades B2G' },
        { href: '/licitacoes', title: 'Licitações por Setor' },
        { href: '/cnpj', title: 'Consulta CNPJ B2G' },
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

      <h1>Órgãos Compradores — Licitações por Órgão Público</h1>
      <p className="lead">
        Descubra o perfil de compras de qualquer órgão público. Veja total de licitações,
        valores contratados, modalidades utilizadas e editais recentes — tudo a partir do CNPJ
        do órgão. Dados oficiais do PNCP, atualizados diariamente.
      </p>

      <OrgaoSearchForm />

      <div className="mt-10">
        <LeadCapture
          source="orgaos"
          heading="Monitore órgãos compradores automaticamente"
          description="Receba alertas quando um órgão público do seu interesse publicar novos editais no seu setor."
        />
      </div>

      <section className="mt-12">
        <h2>O que você verá</h2>
        <ul>
          <li><strong>Perfil do órgão</strong> — Razão social, esfera, UF e CNPJ</li>
          <li><strong>Total de licitações</strong> — Quantidade de processos publicados no período</li>
          <li><strong>Valores contratados</strong> — Soma dos valores estimados e homologados</li>
          <li><strong>Modalidades utilizadas</strong> — Pregão Eletrônico, Concorrência, Dispensa e outras</li>
          <li><strong>Editais recentes</strong> — Últimos processos publicados com prazo e objeto</li>
          <li><strong>Setores de compra</strong> — Segmentos com maior volume de contratações</li>
        </ul>

        <h2>Perguntas Frequentes</h2>

        <h3>O que são órgãos compradores?</h3>
        <p>
          Órgãos compradores são entidades públicas — prefeituras, autarquias, secretarias,
          universidades federais, hospitais públicos e outros entes da administração — que
          publicam licitações para contratar produtos e serviços. Toda compra acima de
          determinado valor deve ser realizada por meio de processo licitatório aberto e
          transparente.
        </p>

        <h3>Como consultar licitações de um órgão?</h3>
        <p>
          Informe o CNPJ do órgão comprador no campo acima e clique em{' '}
          <strong>"Consultar Órgão"</strong>. Você verá o perfil completo de compras: total
          de licitações publicadas, valores contratados, modalidades utilizadas e os editais
          mais recentes disponíveis no PNCP.
        </p>

        <h3>De onde vêm os dados?</h3>
        <p>
          Os dados vêm do <strong>PNCP</strong> — Portal Nacional de Contratações Públicas,
          a base oficial do Governo Federal que centraliza todas as contratações públicas do
          país. As informações são atualizadas diariamente e refletem o estado mais recente
          dos processos licitatórios.
        </p>

        <h3>Preciso me cadastrar?</h3>
        <p>
          Não. A consulta de órgãos compradores é 100% gratuita e não exige cadastro.
          Para acessar análise detalhada de editais, monitoramento automático e alertas,
          você pode criar um trial gratuito de 14 dias no SmartLic.
        </p>

        <h3>Quais informações estão disponíveis?</h3>
        <p>
          Para cada órgão comprador você encontrará: total de licitações publicadas no
          período, valor total estimado contratado, modalidades de contratação mais utilizadas
          (Pregão Eletrônico, Concorrência, Dispensa etc.), setores e segmentos com maior
          volume de compras e os editais abertos mais recentes com prazos e valores.
        </p>
      </section>
    </ContentPageLayout>
  );
}
