import { Metadata } from 'next';
import ContentPageLayout from '../components/ContentPageLayout';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Como Evitar Prejuízo em Licitações Públicas',
  description:
    'As 5 causas mais comuns de perda financeira em licitações e como identificar cada uma antes de investir na proposta. Exemplos reais do mercado B2G.',
  alternates: {
    canonical: 'https://smartlic.tech/como-evitar-prejuizo-licitacao',
  },
};

const articleSchema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: 'Como evitar prejuízo em licitações públicas',
  description:
    'As 5 causas mais comuns de perda financeira em licitações públicas e como identificar cada uma antes de investir na proposta.',
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
    '@id': 'https://smartlic.tech/como-evitar-prejuizo-licitacao',
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
      name: 'Como evitar prejuízo em licitações',
      item: 'https://smartlic.tech/como-evitar-prejuizo-licitacao',
    },
  ],
};

const RELATED_PAGES = [
  {
    href: '/como-avaliar-licitacao',
    title: 'Como avaliar se uma licitação vale a pena',
  },
  {
    href: '/como-filtrar-editais',
    title: 'Como filtrar editais de licitação',
  },
  {
    href: '/como-priorizar-oportunidades',
    title: 'Como priorizar oportunidades',
  },
];

export default function ComoEvitarPrejuizo() {
  return (
    <ContentPageLayout
      breadcrumbLabel="Como evitar prejuízo em licitações"
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

      <h1>Como evitar prejuízo em licitações públicas</h1>

      <p className="text-xl leading-relaxed text-ink">
        Participar da licitação errada custa mais do que não participar. Quem
        já viveu isso sabe: semanas de trabalho, honorários de advogado, custos
        com certidões e horas da equipe técnica — tudo investido em um edital
        que nunca deveria ter saído da triagem inicial.
      </p>

      <p>
        O mercado de licitações públicas no Brasil movimenta centenas de
        bilhões por ano. Com esse volume, a tentação de participar de tudo é
        grande. Mas volume sem critério não gera resultado — gera prejuízo.
      </p>

      <h2>Participar sem avaliar viabilidade</h2>

      <p>
        A causa mais frequente de prejuízo é também a mais evitável. Acontece
        assim: a equipe vê o objeto do edital, identifica que &quot;parece ser
        da área&quot; e já começa a montar a proposta. Sem verificar valor,
        região, prazos ou requisitos técnicos.
      </p>

      {/* Example Box */}
      <div className="not-prose my-8 border-l-4 border-warning bg-surface-1 rounded-r-xl p-6">
        <p className="text-ink-secondary leading-relaxed">
          <strong className="text-ink">Caso real:</strong> Uma empresa de
          facilities de médio porte investiu R$ 35 mil — entre documentação,
          certidões e horas da equipe — para participar de um pregão de
          manutenção predial avaliado em R$ 12 milhões. O edital exigia
          atestados de capacidade para no mínimo 50% do valor. A empresa
          nunca havia executado contrato acima de R$ 2 milhões.
          Desclassificada na habilitação.
        </p>
      </div>

      <p>
        A solução é simples:{' '}
        <Link href="/como-avaliar-licitacao">
          aplicar critérios objetivos de avaliação
        </Link>{' '}
        antes de investir um real. Se o edital não passa nos critérios básicos,
        não merece o esforço da equipe.
      </p>

      <h2>Subestimar custos de preparação</h2>

      <p>
        Montar uma proposta de licitação não é gratuito. Dependendo da
        modalidade e complexidade, os custos incluem:
      </p>

      <ul>
        <li>Certidões e documentos atualizados — R$ 500 a R$ 2.000</li>
        <li>Horas da equipe técnica para elaboração — 20 a 80 horas</li>
        <li>Consultoria jurídica — R$ 2.000 a R$ 10.000</li>
        <li>Garantia de proposta, quando exigida — 1% a 5% do valor</li>
        <li>Viagens para visita técnica obrigatória</li>
      </ul>

      {/* Example Box */}
      <div className="not-prose my-8 border-l-4 border-warning bg-surface-1 rounded-r-xl p-6">
        <p className="text-ink-secondary leading-relaxed">
          <strong className="text-ink">Caso real:</strong> Uma empresa de
          software gastou R$ 18 mil preparando proposta técnica detalhada para
          uma concorrência de informatização hospitalar. Perdeu por 0,3 pontos
          na avaliação técnica. O investimento não recuperável representou
          quase 40% do lucro do trimestre anterior.
        </p>
      </div>

      <p>
        Antes de decidir participar, faça uma estimativa realista do custo
        total de preparação e compare com a margem esperada em caso de
        vitória. Se o custo de preparação supera 5% da margem líquida
        estimada, reavalie.
      </p>

      <h2>Ignorar requisitos técnicos incompatíveis</h2>

      <p>
        Editais frequentemente incluem requisitos específicos que eliminam
        participantes na habilitação: certificações obrigatórias, atestados com
        metragens ou volumes mínimos, equipe técnica com formação específica.
        Tudo isso precisa ser verificado antes de investir na proposta — não
        depois.
      </p>

      {/* Example Box */}
      <div className="not-prose my-8 border-l-4 border-warning bg-surface-1 rounded-r-xl p-6">
        <p className="text-ink-secondary leading-relaxed">
          <strong className="text-ink">Caso real:</strong> Uma construtora de
          pequeno porte participou de licitação para reforma de escola. O
          edital exigia engenheiro civil com certificação em acessibilidade
          (ABNT NBR 9050) no quadro permanente. A empresa tinha o profissional
          como consultor externo, não como funcionário. Inabilitada após todo
          o investimento de preparação.
        </p>
      </div>

      <p>
        A regra é direta: leia o edital completo — especialmente os anexos de
        habilitação técnica — antes de começar qualquer preparação. Se algum
        requisito não pode ser cumprido no prazo disponível, desista cedo. O
        custo de desistir é zero. O custo de ser inabilitado não é.
      </p>

      <h2>Competir fora da faixa de valor ideal</h2>

      <p>
        Cada empresa tem uma faixa de valor onde opera com eficiência e margem
        saudável. Ir muito acima expõe a riscos de execução — capital de giro
        insuficiente, equipe subdimensionada, garantias que não consegue
        apresentar. Ir muito abaixo consome recursos que poderiam estar em
        oportunidades mais rentáveis.
      </p>

      <p>
        Defina objetivamente a faixa onde sua empresa compete melhor,
        considerando o histórico de contratos executados com sucesso.{' '}
        <Link href="/como-priorizar-oportunidades">
          Saiba como priorizar oportunidades dentro da sua faixa ideal
        </Link>.
      </p>

      <h2>Não considerar logística e região</h2>

      <p>
        Uma licitação atraente no papel pode se transformar em pesadelo na
        execução. Fornecimento contínuo para órgãos em regiões remotas,
        manutenção com SLA de 4 horas em cidades a 800 km da base,
        deslocamento de equipe técnica para estados sem filial — tudo isso
        corrói a margem de forma silenciosa.
      </p>

      {/* Example Box */}
      <div className="not-prose my-8 border-l-4 border-warning bg-surface-1 rounded-r-xl p-6">
        <p className="text-ink-secondary leading-relaxed">
          <strong className="text-ink">Caso real:</strong> Uma empresa de
          vigilância de Curitiba venceu licitação para segurança patrimonial
          em três unidades no Mato Grosso. O custo de implantação —
          recrutamento local, treinamento, deslocamento de supervisores —
          ultrapassou em 60% o previsto. O contrato operou no prejuízo durante
          14 meses até a rescisão.
        </p>
      </div>

      <p>
        Inclua o custo logístico real na análise de viabilidade. Se o edital
        exige presença física, calcule o impacto no custo total antes de
        decidir participar.
      </p>

      <h2>Como um filtro estratégico reduz o risco</h2>

      <p>
        As cinco causas acima têm algo em comum: todas podem ser identificadas
        <strong> antes</strong> de iniciar a preparação da proposta. O
        problema é que, com centenas de editais publicados diariamente, fazer
        essa análise manualmente para cada um é humanamente impossível.
      </p>

      <p>
        Um filtro estratégico automatizado resolve isso ao aplicar critérios
        objetivos — setor, valor, região, prazo, modalidade — antes que o
        edital chegue à sua mesa. Em vez de analisar 200 editais por semana e
        participar de 20 sem critério, você analisa 15 pré-qualificados e
        participa de 5 com alta probabilidade de sucesso.
      </p>

      <p>
        <Link href="/como-filtrar-editais">
          Entenda como funciona a filtragem inteligente de editais
        </Link>{' '}
        e por que ela é diferente de uma busca por palavras-chave.
      </p>

      {/* CTA Section */}
      <div className="not-prose mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-8 text-center border border-brand-blue/20">
        <p className="text-xl font-bold text-ink mb-2">
          Pare de investir em licitações erradas
        </p>
        <p className="text-ink-secondary mb-6 max-w-lg mx-auto">
          O SmartLic filtra, classifica e avalia a viabilidade de cada edital
          automaticamente — antes que você gaste um centavo.
        </p>
        <Link
          href="/signup?source=content-prejuizo"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-6 py-3 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
        >
          Comece Grátis
        </Link>
      </div>
    </ContentPageLayout>
  );
}
