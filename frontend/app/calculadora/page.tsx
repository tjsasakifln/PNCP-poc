import { Metadata } from 'next';
import CalculadoraClient from './CalculadoraClient';
import ContentPageLayout from '../components/ContentPageLayout';
import { LeadCapture } from '@/components/LeadCapture';
import { CopyEmbedButton } from './CopyEmbedButton';
import { SECTORS } from '@/lib/sectors';
import { UF_NAMES, getUfPrep } from '@/lib/programmatic';

// STORY-432 AC5: OG meta tags dinâmicas baseadas em params de URL (setor, uf)
export async function generateMetadata({
  searchParams,
}: {
  searchParams: Promise<{ setor?: string; uf?: string }>;
}): Promise<Metadata> {
  const params = await searchParams;
  const setorSlug = params?.setor;
  const ufCode = params?.uf?.toUpperCase();

  const sector = setorSlug ? SECTORS.find((s) => s.slug === setorSlug) : undefined;
  const ufName = ufCode ? (UF_NAMES[ufCode] ?? ufCode) : undefined;

  const title =
    sector && ufName
      ? `Calculadora B2G: ${sector.name} ${getUfPrep(ufCode)} ${ufName} — SmartLic`
      : sector
        ? `Calculadora B2G: ${sector.name} — SmartLic`
        : 'Calculadora de Oportunidades B2G — Quanto você está perdendo em licitações?';

  const description =
    sector && ufName
      ? `Descubra quantas licitações de ${sector.name} ${getUfPrep(ufCode)} ${ufName} sua equipe está perdendo. Dados reais do PNCP por estado.`
      : sector
        ? `Descubra quantas licitações de ${sector.name} sua equipe está perdendo. Dados reais do PNCP por setor.`
        : 'Descubra quantas licitações do seu setor sua equipe está perdendo por falta de automação. Dados reais do PNCP, por setor e UF.';

  const ogTitle =
    sector && ufName
      ? `Calculadora B2G: ${sector.name} ${getUfPrep(ufCode)} ${ufName} — Quanto você está perdendo?`
      : 'Calculadora de Oportunidades B2G — Quanto você está perdendo?';

  const canonicalUrl = 'https://smartlic.tech/calculadora';

  return {
    title,
    description,
    alternates: {
      canonical: canonicalUrl,
    },
    openGraph: {
      title: ogTitle,
      description,
      url: canonicalUrl,
      type: 'website',
      images: [
        {
          url: '/api/og?title=Calculadora+de+Oportunidades+B2G',
          width: 1200,
          height: 630,
          alt: 'Calculadora de Oportunidades B2G',
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: ogTitle,
      description,
      images: ['/api/og?title=Calculadora+de+Oportunidades+B2G'],
    },
  };
}

const howToSchema = {
  '@context': 'https://schema.org',
  '@type': 'HowTo',
  name: 'Como descobrir quanto sua empresa perde em licitações não analisadas',
  description:
    'Use a calculadora gratuita do SmartLic para calcular o valor de oportunidades B2G perdidas no seu setor e UF.',
  step: [
    {
      '@type': 'HowToStep',
      position: 1,
      name: 'Selecione seu setor e UF',
      text: 'Escolha o setor de atuação da sua empresa e o estado principal de operação.',
    },
    {
      '@type': 'HowToStep',
      position: 2,
      name: 'Informe sua capacidade atual',
      text: 'Indique quantos editais sua equipe analisa por mês, sua taxa de vitória e valor médio dos contratos.',
    },
    {
      '@type': 'HowToStep',
      position: 3,
      name: 'Veja o resultado',
      text: 'Descubra o valor estimado de oportunidades que sua empresa não está analisando, com dados reais do PNCP.',
    },
  ],
};

const faqSchema = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'De onde vêm os dados da calculadora?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Os dados são extraídos diretamente do PNCP (Portal Nacional de Contratações Públicas), atualizados diariamente. Mostramos editais publicados nos últimos 30 dias.',
      },
    },
    {
      '@type': 'Question',
      name: 'A calculadora é gratuita?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Sim, a calculadora é 100% gratuita e não requer cadastro. Para analisar as oportunidades em detalhe, você pode criar uma conta trial gratuita de 14 dias.',
      },
    },
    {
      '@type': 'Question',
      name: 'Quantos setores estão disponíveis?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'O SmartLic cobre 20 setores de atuação, desde Vestuário e Uniformes até Engenharia e Obras, passando por TI, Saúde, Alimentos e Facilities.',
      },
    },
  ],
};

const breadcrumbSchema = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'Início',
      item: 'https://smartlic.tech',
    },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Calculadora B2G',
      item: 'https://smartlic.tech/calculadora',
    },
  ],
};

// STORY-432 AC7: Schema.org SoftwareApplication para descobribilidade e rich snippets
const softwareAppSchema = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Calculadora de Oportunidades B2G',
  url: 'https://smartlic.tech/calculadora',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'BRL',
  },
  description: 'Calcule quantas licitações públicas seu setor publica por mês e descubra o valor de oportunidades não analisadas. Dados reais do PNCP.',
  provider: {
    '@type': 'Organization',
    name: 'SmartLic',
    url: 'https://smartlic.tech',
  },
  featureList: [
    'Dados reais do PNCP por setor e UF',
    'Cálculo de cobertura atual vs total disponível',
    'Estimativa de receita perdida',
    'Código de incorporação gratuito para terceiros',
  ],
};

export default function CalculadoraPage({}: {
  searchParams?: Promise<{ setor?: string; uf?: string }>;
}) {
  return (
    <ContentPageLayout
      breadcrumbLabel="Calculadora de Oportunidades B2G"
      relatedPages={[
        { href: '/licitacoes', title: 'Licitações por Setor' },
        { href: '/como-avaliar-licitacao', title: 'Como Avaliar uma Licitação' },
        { href: '/glossario', title: 'Glossário de Licitações' },
      ]}
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareAppSchema) }}
      />

      <h1>Calculadora de Oportunidades B2G</h1>
      <p className="lead">
        Descubra quanto sua empresa está deixando de faturar em licitações.
        Dados reais do PNCP, calculados para o seu setor e estado.
      </p>

      <CalculadoraClient />

      <div className="mt-10">
        <LeadCapture
          source="calculadora"
          heading="Receba oportunidades do seu setor toda semana"
          description="Análise automática de editais novos, filtrada pelo seu perfil. Direto no email."
        />
      </div>

      {/* STORY-432 AC3: Embed code generator */}
      <section className="mt-12 p-6 bg-gray-50 rounded-xl border border-gray-200">
        <h2 className="text-xl font-bold text-gray-900 mb-2">Incorpore esta calculadora no seu site</h2>
        <p className="text-gray-600 text-sm mb-4">
          Ofereça gratuitamente aos seus leitores a calculadora de oportunidades em licitações.
          Dados reais do PNCP, sem nenhum custo.
        </p>
        <div className="bg-white rounded-lg border border-gray-300 p-4 mb-3">
          <code className="text-xs text-gray-700 break-all block font-mono leading-relaxed select-all" id="embed-code">
            {`<iframe src="https://smartlic.tech/calculadora/embed" width="100%" height="620" frameborder="0" title="Calculadora de Oportunidades em Licitações Públicas" loading="lazy"></iframe>`}
          </code>
        </div>
        <CopyEmbedButton code={`<iframe src="https://smartlic.tech/calculadora/embed" width="100%" height="620" frameborder="0" title="Calculadora de Oportunidades em Licitações Públicas" loading="lazy"></iframe>`} />
      </section>

      <section className="mt-12">
        <h2>Perguntas Frequentes</h2>

        <h3>De onde vêm os dados da calculadora?</h3>
        <p>
          Os dados são extraídos diretamente do PNCP (Portal Nacional de Contratações Públicas),
          atualizados diariamente. Mostramos editais publicados nos últimos 30 dias.
        </p>

        <h3>A calculadora é gratuita?</h3>
        <p>
          Sim, a calculadora é 100% gratuita e não requer cadastro. Para analisar as oportunidades
          em detalhe, você pode criar uma conta trial gratuita de 14 dias.
        </p>

        <h3>Quantos setores estão disponíveis?</h3>
        <p>
          O SmartLic cobre 20 setores de atuação, desde Vestuário e Uniformes até Engenharia e
          Obras, passando por TI, Saúde, Alimentos e Facilities.
        </p>
      </section>
    </ContentPageLayout>
  );
}
