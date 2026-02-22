import { Metadata } from 'next';
import ContentPageLayout from '../components/ContentPageLayout';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Como Identificar Licitações com Maior Chance de Vitória',
  description:
    'Framework prático para priorizar licitações: critérios de aderência, viabilidade e competição. Inclui exemplo com 3 editais reais e decisão fundamentada.',
  alternates: {
    canonical: 'https://smartlic.tech/como-priorizar-oportunidades',
  },
};

const articleSchema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: 'Como identificar licitações com maior chance de vitória',
  description:
    'Framework prático para priorizar oportunidades de licitação usando critérios de aderência, viabilidade operacional e competição estimada.',
  author: {
    '@type': 'Organization',
    name: 'SmartLic',
    url: 'https://smartlic.tech',
  },
  publisher: {
    '@type': 'Organization',
    name: 'SmartLic',
    logo: {
      '@type': 'ImageObject',
      url: 'https://smartlic.tech/logo.png',
    },
  },
  datePublished: '2026-02-22',
  dateModified: '2026-02-22',
  mainEntityOfPage: {
    '@type': 'WebPage',
    '@id': 'https://smartlic.tech/como-priorizar-oportunidades',
  },
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
      name: 'Como priorizar oportunidades',
      item: 'https://smartlic.tech/como-priorizar-oportunidades',
    },
  ],
};

const RELATED_PAGES = [
  {
    href: '/como-avaliar-licitacao',
    title: 'Como avaliar se uma licitação vale a pena',
  },
  {
    href: '/como-evitar-prejuizo-licitacao',
    title: 'Como evitar prejuízo em licitações',
  },
  {
    href: '/como-filtrar-editais',
    title: 'Como filtrar editais de licitação',
  },
];

export default function ComoPriorizarOportunidades() {
  return (
    <ContentPageLayout
      breadcrumbLabel="Como priorizar oportunidades"
      relatedPages={RELATED_PAGES}
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      <h1>Como identificar licitações com maior chance de vitória</h1>

      <p className="text-xl leading-relaxed text-ink">
        Encontrar licitações é fácil. Saber quais priorizar é o que gera
        resultado. Uma empresa com recursos limitados — e todas têm — precisa
        concentrar esforços nos editais onde a probabilidade de vitória e a
        margem esperada justificam o investimento. Participar de tudo não é
        estratégia. É dispersão.
      </p>

      <h2>Por que priorização importa mais que volume</h2>

      <p>
        Existe uma crença persistente no mercado B2G de que participar de mais
        licitações automaticamente aumenta as chances de vencer. A matemática
        conta outra história.
      </p>

      <p>
        Uma empresa que participa de 30 licitações por mês com preparação
        superficial tem taxa de sucesso típica de 3-5%. A mesma empresa
        participando de 8 licitações bem escolhidas, com preparação
        aprofundada, pode alcançar 25-35% de sucesso. O resultado líquido é
        melhor com menos participações — desde que sejam as corretas.
      </p>

      <p>
        Menos editais com mais dedicação significa proposta melhor, equipe
        menos sobrecarregada e{' '}
        <Link href="/como-evitar-prejuizo-licitacao">
          risco de prejuízo drasticamente menor
        </Link>.
      </p>

      <h2>Os três eixos de priorização</h2>

      <p>
        Priorizar exige um framework objetivo. Opinião e &quot;feeling&quot;
        não escalam. Os três eixos fundamentais são:
      </p>

      <h3>Aderência ao perfil</h3>
      <p>
        Quão alinhado o edital está com o que sua empresa faz de melhor? Isso
        vai além do setor — inclui tipo de serviço ou produto, porte do
        contrato e complexidade técnica. Uma aderência alta significa atestados
        sólidos, equipe qualificada e experiência comprovada. São fatores que
        pesam em qualquer avaliação, independente da modalidade.
      </p>

      <h3>Viabilidade operacional</h3>
      <p>
        Você consegue executar esse contrato com qualidade e margem saudável?
        A viabilidade considera quatro fatores:{' '}
        <Link href="/como-avaliar-licitacao">
          modalidade, prazo, valor e geografia
        </Link>. Um edital pode ser altamente aderente ao seu perfil, mas
        inviável por estar em uma região onde você não tem infraestrutura ou
        por exigir um prazo incompatível com sua capacidade atual.
      </p>

      <h3>Competição estimada</h3>
      <p>
        Quantas empresas provavelmente vão participar? Pregões eletrônicos com
        critério de menor preço em setores comoditizados atraem dezenas de
        concorrentes. Concorrências técnicas em nichos especializados podem ter
        3 a 5 participantes. A probabilidade de vitória muda drasticamente
        entre esses cenários.
      </p>

      <h2>Como avaliar a viabilidade de cada oportunidade</h2>

      <p>
        Para cada edital pré-filtrado, aplique uma avaliação estruturada com
        pontuação ponderada:
      </p>

      <ul>
        <li>
          <strong>Modalidade (peso 30%)</strong> — pregão eletrônico com menor
          preço pontua baixo para quem compete por qualidade. Concorrência com
          técnica e preço pontua alto para quem tem diferenciais técnicos.
        </li>
        <li>
          <strong>Prazo (peso 25%)</strong> — prazo apertado reduz a pontuação
          porque limita a qualidade da preparação.
        </li>
        <li>
          <strong>Faixa de valor (peso 25%)</strong> — o valor ideal é aquele
          em que a empresa opera com eficiência. Muito acima ou muito abaixo
          reduz a pontuação.
        </li>
        <li>
          <strong>Geografia (peso 20%)</strong> — regiões distantes sem
          presença local reduzem a pontuação pelo custo logístico implícito.
        </li>
      </ul>

      <p>
        A soma ponderada gera um índice de viabilidade classificado em três
        níveis: <strong>alta</strong> (acima de 70), <strong>média</strong>
        {' '}(40-70) e <strong>baixa</strong> (abaixo de 40).
      </p>

      <h2>O framework: participar, monitorar ou descartar</h2>

      <p>
        Com aderência e viabilidade avaliadas, cada oportunidade cai em uma de
        três categorias:
      </p>

      <ul>
        <li>
          <strong>Participar</strong> — aderência alta + viabilidade alta.
          Dedique recursos completos para a melhor proposta possível.
        </li>
        <li>
          <strong>Monitorar</strong> — aderência alta + viabilidade média, ou
          vice-versa. Acompanhe e reavalie se as condições mudarem
          (esclarecimentos, aditivos, prorrogação de prazo).
        </li>
        <li>
          <strong>Descartar</strong> — qualquer combinação com aderência baixa
          ou viabilidade baixa. Não invista tempo — passe para o próximo.
        </li>
      </ul>

      <p>
        Esse framework elimina decisões emocionais e substitui por critérios
        objetivos e replicáveis.
      </p>

      {/* Practical Example */}
      <div className="not-prose my-10 border-l-4 border-brand-blue bg-surface-1 rounded-r-xl p-6 lg:p-8">
        <h3 className="font-bold text-ink text-lg mb-6">
          Na prática: 3 editais, qual priorizar?
        </h3>
        <p className="text-ink-secondary mb-6 leading-relaxed">
          Uma empresa de materiais elétricos com sede em São Paulo, faixa ideal
          de R$ 200k a R$ 1,5M, encontra três editais na mesma semana:
        </p>

        {/* Edital A */}
        <div className="mb-6 bg-canvas rounded-lg p-5 border border-[var(--border)]">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-ink">Edital A — Pregão Eletrônico, R$ 450 mil</h4>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-success/10 text-success">PARTICIPAR</span>
          </div>
          <p className="text-sm text-ink-secondary mb-2">
            Material elétrico para hospital em Campinas/SP. Menor preço. Prazo: 12 dias.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-ink-secondary">
            <span>Setor: <strong className="text-success">Alta</strong></span>
            <span>Valor: <strong className="text-success">Adequado</strong></span>
            <span>Prazo: <strong className="text-success">Suficiente</strong></span>
            <span>Geografia: <strong className="text-success">Mesma UF</strong></span>
            <span>Modalidade: <strong className="text-ink-secondary">Competitiva</strong></span>
          </div>
        </div>

        {/* Edital B */}
        <div className="mb-6 bg-canvas rounded-lg p-5 border border-[var(--border)]">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-ink">Edital B — Concorrência, R$ 3,2 milhões</h4>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-error/10 text-error">DESCARTAR</span>
          </div>
          <p className="text-sm text-ink-secondary mb-2">
            Instalação elétrica completa de escola em Manaus/AM. Técnica e preço. Prazo: 25 dias.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-ink-secondary">
            <span>Setor: <strong className="text-ink-secondary">Média</strong></span>
            <span>Valor: <strong className="text-error">Acima da faixa</strong></span>
            <span>Prazo: <strong className="text-success">Confortável</strong></span>
            <span>Geografia: <strong className="text-error">Logística inviável</strong></span>
            <span>Modalidade: <strong className="text-success">Favorável</strong></span>
          </div>
        </div>

        {/* Edital C */}
        <div className="bg-canvas rounded-lg p-5 border border-[var(--border)]">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-ink">Edital C — Pregão Eletrônico, R$ 180 mil</h4>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-warning/10 text-warning">MONITORAR</span>
          </div>
          <p className="text-sm text-ink-secondary mb-2">
            Material elétrico para reforma de edifício público no Rio de Janeiro/RJ. Menor preço. Prazo: 8 dias.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-ink-secondary">
            <span>Setor: <strong className="text-success">Alta</strong></span>
            <span>Valor: <strong className="text-ink-secondary">Abaixo da faixa</strong></span>
            <span>Prazo: <strong className="text-warning">Apertado</strong></span>
            <span>Geografia: <strong className="text-success">Viável</strong></span>
            <span>Modalidade: <strong className="text-ink-secondary">Competitiva</strong></span>
          </div>
        </div>

        <p className="text-ink-secondary mt-6 leading-relaxed">
          Sem esse framework, a empresa provavelmente tentaria os três editais,
          diluindo recursos e reduzindo a qualidade de todas as propostas.
        </p>
      </div>

      <p>
        <Link href="/como-filtrar-editais">
          Veja como a filtragem inteligente automatiza a primeira etapa desse
          processo
        </Link> — entregando apenas os editais que merecem essa análise
        aprofundada.
      </p>

      {/* CTA Section */}
      <div className="not-prose mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-8 text-center border border-brand-blue/20">
        <p className="text-xl font-bold text-ink mb-2">
          Priorize com dados, não com intuição
        </p>
        <p className="text-ink-secondary mb-6 max-w-lg mx-auto">
          O SmartLic avalia a viabilidade de cada edital com 4 critérios
          ponderados e classifica automaticamente em alta, média e baixa.
        </p>
        <Link
          href="/signup?source=content-priorizar"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-6 py-3 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
        >
          Comece Grátis
        </Link>
      </div>
    </ContentPageLayout>
  );
}
