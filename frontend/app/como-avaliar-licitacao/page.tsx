import { Metadata } from 'next';
import ContentPageLayout from '../components/ContentPageLayout';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Como Avaliar se uma Licitação Vale a Pena',
  description:
    'Conheça os 5 critérios que empresas B2G usam para decidir se vale investir tempo e recursos em uma licitação pública. Guia prático com exemplo real.',
  alternates: {
    canonical: 'https://smartlic.tech/como-avaliar-licitacao',
  },
  openGraph: {
    title: 'Como Avaliar se uma Licitação Vale a Pena',
    description: 'Conheça os 5 critérios que empresas B2G usam para decidir se vale investir tempo e recursos em uma licitação pública.',
    url: 'https://smartlic.tech/como-avaliar-licitacao',
    type: 'article',
    images: [{ url: '/api/og?title=Como+Avaliar+se+uma+Licita%C3%A7%C3%A3o+Vale+a+Pena', width: 1200, height: 630, alt: 'Como Avaliar se uma Licitação Vale a Pena' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Como Avaliar se uma Licitação Vale a Pena',
    description: 'Conheça os 5 critérios que empresas B2G usam para decidir se vale investir tempo e recursos em uma licitação pública.',
    images: ['/api/og?title=Como+Avaliar+se+uma+Licita%C3%A7%C3%A3o+Vale+a+Pena'],
  },
};

const articleSchema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: 'Como avaliar se uma licitação vale a pena?',
  description:
    'Critérios práticos para avaliar se uma licitação pública justifica o investimento de tempo e recursos da sua empresa.',
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
    '@id': 'https://smartlic.tech/como-avaliar-licitacao',
  },
};

const howToSchema = {
  '@context': 'https://schema.org',
  '@type': 'HowTo',
  name: 'Como avaliar se uma licitação vale a pena',
  description: 'Guia prático com 5 critérios para decidir se vale investir em uma licitação pública.',
  step: [
    { '@type': 'HowToStep', position: 1, name: 'Verificar compatibilidade setorial', text: 'Confirme se o objeto da licitação está diretamente relacionado ao seu CNAE principal e se você tem atestados compatíveis.' },
    { '@type': 'HowToStep', position: 2, name: 'Avaliar faixa de valor', text: 'Foque em editais entre 50% e 300% do seu contrato médio para equilibrar risco e eficiência.' },
    { '@type': 'HowToStep', position: 3, name: 'Verificar prazo para preparação', text: 'Confirme se há tempo para análise do edital, obtenção de certidões, elaboração da proposta e revisão interna.' },
    { '@type': 'HowToStep', position: 4, name: 'Analisar viabilidade geográfica', text: 'Calcule o custo logístico real e verifique se consome mais de 15% da margem esperada.' },
    { '@type': 'HowToStep', position: 5, name: 'Avaliar modalidade e competição', text: 'Identifique a modalidade e critério de julgamento para estimar o nível de competição.' },
  ],
};

const RELATED_PAGES = [
  {
    href: '/como-evitar-prejuizo-licitacao',
    title: 'Como evitar prejuízo em licitações',
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

export default function ComoAvaliarLicitacao() {
  return (
    <ContentPageLayout
      breadcrumbLabel="Como avaliar uma licitação"
      breadcrumbItems={[
        { label: 'Início', href: '/' },
        { label: 'Guias', href: '/features' },
        { label: 'Como avaliar uma licitação' },
      ]}
      relatedPages={RELATED_PAGES}
    >
      {/* Breadcrumb JSON-LD emitted by BreadcrumbNav inside ContentPageLayout */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }}
      />

      <h1>Como avaliar se uma licitação vale a pena?</h1>

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Quem trabalha com licitações conhece bem a situação: a equipe passa
        duas semanas montando proposta, reúne certidões, mobiliza técnicos,
        revisa documentação — e no final descobre que o edital nunca fez
        sentido para a empresa. O custo não é só financeiro. É o desgaste da
        equipe e a oportunidade que ficou para trás enquanto vocês estavam
        ocupados com o edital errado.
      </p>

      <p>
        A diferença entre empresas que crescem de forma consistente no mercado
        público e as que vivem de resultados esporádicos costuma estar em algo
        simples: <strong>avaliar antes de participar</strong>. Parece óbvio,
        mas na prática a pressão por volume empurra muita gente a pular essa
        etapa.
      </p>

      <p>
        Existem cinco critérios que funcionam para qualquer setor e qualquer
        porte de empresa. Não é teoria — é o que separa uma decisão informada
        de um chute.
      </p>

      <h2>Compatibilidade setorial</h2>

      <p>
        Primeiro e mais direto: o edital é do seu segmento? Parece básico, mas
        é o filtro que mais gente ignora. A lógica de &quot;quanto mais
        licitação eu participar, mais chance tenho&quot; não se sustenta quando
        você olha os números. Editais fora do seu setor principal exigem
        adaptações técnicas, equipes que você não tem e referências que não
        pode comprovar.
      </p>

      <p>
        Na prática, verifique se o objeto da licitação está diretamente
        relacionado ao seu CNAE principal e se você tem atestados de capacidade
        técnica compatíveis. Se for preciso subcontratar mais de 30% do
        escopo, é um sinal claro de que não é para você.
      </p>

      <h2>Faixa de valor</h2>

      <p>
        Toda empresa tem uma faixa de valor em que opera bem. Uma empresa
        habituada a contratos de R$ 200 mil que tenta um edital de R$ 5
        milhões enfrenta problemas de garantia, capital de giro e capacidade
        de execução que podem inviabilizar o contrato mesmo se vencer.
      </p>

      <p>
        O contrário também vale: licitações com valor muito baixo raramente
        justificam o esforço. O trabalho para montar documentação de um pregão
        de R$ 15 mil é praticamente o mesmo de um de R$ 500 mil.
      </p>

      <p>
        Uma referência útil: foque em editais entre 50% e 300% do seu contrato
        médio. Fora dessa faixa, o risco sobe e a eficiência cai.
      </p>

      <h2>Prazo para preparação</h2>

      <p>
        Um edital com prazo de 5 dias úteis pede uma análise completamente
        diferente de um com 30 dias. O prazo determina se há tempo para
        analisar o edital e seus anexos, solicitar esclarecimentos, obter
        certidões atualizadas, elaborar a proposta técnica e comercial, e
        revisar tudo internamente.
      </p>

      <p>
        Se o prazo restante não permite cumprir todas essas etapas com
        qualidade, o risco de proposta incompleta ou com erros é alto.{' '}
        <Link href="/como-evitar-prejuizo-licitacao">
          Propostas apressadas estão entre as principais causas de prejuízo em
          licitações
        </Link>.
      </p>

      <h2>Viabilidade geográfica</h2>

      <p>
        Onde fica o órgão contratante importa mais do que parece. Uma empresa
        de São Paulo que vence licitação para fornecimento contínuo no Amazonas
        vai gastar com logística, deslocamento de equipe e tempo de resposta
        valores que corroem a margem silenciosamente.
      </p>

      <p>
        A conta é simples: calcule o custo logístico real — frete,
        deslocamento, hospedagem — e inclua na análise de margem. Se esse
        custo consome mais de 15% da margem esperada, a viabilidade fica
        comprometida.
      </p>

      <h2>Modalidade e competição</h2>

      <p>
        A modalidade define as regras do jogo. Um pregão eletrônico com
        critério de menor preço tende a uma disputa acirrada por centavos. Já
        uma concorrência com técnica e preço valoriza diferenciais
        qualitativos. E um diálogo competitivo permite propor soluções que os
        concorrentes nem consideraram.
      </p>

      <p>
        Identifique a modalidade e o critério de julgamento antes de investir
        qualquer esforço. Se é pregão por menor preço no seu setor mais
        competitivo, a margem será apertada. Se inclui avaliação técnica, suas
        certificações e experiência viram vantagem concreta.{' '}
        <Link href="/como-priorizar-oportunidades">
          Veja como usar esses critérios para priorizar oportunidades
        </Link>.
      </p>

      {/* Practical Example */}
      <div className="not-prose my-8 sm:my-10 border-l-4 border-brand-blue bg-surface-1 rounded-r-xl p-4 sm:p-6 lg:p-8">
        <h3 className="font-bold text-ink text-base sm:text-lg mb-3 sm:mb-4">
          Na prática: análise de um pregão real
        </h3>
        <p className="text-sm sm:text-base text-ink-secondary mb-3 sm:mb-4 leading-relaxed">
          Pregão Eletrônico para aquisição de equipamentos de informática para
          hospital universitário em Minas Gerais. Valor estimado: R$ 1,2
          milhão. Prazo: 18 dias. Para uma empresa de TI sediada em Belo
          Horizonte:
        </p>
        <ul className="space-y-2 text-sm sm:text-base text-ink-secondary">
          <li className="flex items-start gap-2">
            <span className="text-success font-bold mt-0.5 shrink-0">&#10003;</span>
            <span><strong className="text-ink">Setor:</strong> Alta — equipamentos de informática é o core business</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-success font-bold mt-0.5 shrink-0">&#10003;</span>
            <span><strong className="text-ink">Valor:</strong> Adequado — dentro do histórico (R$ 500k a R$ 2M)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-success font-bold mt-0.5 shrink-0">&#10003;</span>
            <span><strong className="text-ink">Prazo:</strong> Suficiente — 18 dias permitem preparação completa</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-success font-bold mt-0.5 shrink-0">&#10003;</span>
            <span><strong className="text-ink">Geografia:</strong> Viável — mesma UF, custo logístico mínimo</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-success font-bold mt-0.5 shrink-0">&#10003;</span>
            <span><strong className="text-ink">Modalidade:</strong> Pregão eletrônico (menor preço) — competição previsível</span>
          </li>
        </ul>
        <p className="text-sm sm:text-base text-ink mt-3 sm:mt-4 font-medium">
          5 de 5 critérios positivos — essa licitação merece dedicação total.
          Compare com uma licitação de obras civis de R$ 8 milhões no Acre
          para a mesma empresa: nenhum critério seria atendido.
        </p>
      </div>

      <h2>O custo de avaliar manualmente</h2>

      <p>
        Aplicar esses cinco critérios a um edital leva de 30 a 60 minutos.
        Multiplicando por milhares de licitações publicadas diariamente nos
        portais PNCP, ComprasGov e Portal de Compras Públicas, fica claro
        que a triagem manual não escala para quem quer cobrir o território
        nacional.
      </p>

      <p>
        É exatamente esse o problema que ferramentas de inteligência em
        licitações resolvem: automatizar a triagem inicial para que sua equipe
        foque apenas nos editais que realmente justificam investimento.{' '}
        <Link href="/como-filtrar-editais">
          Entenda como funciona a filtragem inteligente de editais
        </Link>.
      </p>

      {/* CTA Section */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Descubra quais licitações valem a pena para o seu setor
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic aplica esses 5 critérios automaticamente a cada edital,
          usando IA e dados de 3 fontes oficiais.
        </p>
        <Link
          href="/signup?source=content-avaliar"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
        >
          Comece Grátis
        </Link>
      </div>
    </ContentPageLayout>
  );
}
