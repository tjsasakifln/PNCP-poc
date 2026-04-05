import { Metadata } from 'next';
import ContentPageLayout from '../components/ContentPageLayout';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Como Filtrar Editais de Licitação e Focar no que Importa',
  description:
    'Entenda por que a busca manual de editais não funciona e como um filtro por perfil transforma 1.500 publicações diárias em 12 oportunidades relevantes.',
  alternates: {
    canonical: 'https://smartlic.tech/como-filtrar-editais',
  },
  openGraph: {
    title: 'Como Filtrar Editais de Licitação e Focar no que Importa',
    description: 'Entenda por que a busca manual de editais não funciona e como um filtro por perfil transforma 1.500 publicações diárias em 12 oportunidades relevantes.',
    url: 'https://smartlic.tech/como-filtrar-editais',
    type: 'article',
    images: [{ url: '/api/og?title=Como+Filtrar+Editais+de+Licita%C3%A7%C3%A3o', width: 1200, height: 630, alt: 'Como Filtrar Editais de Licitação' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Como Filtrar Editais de Licitação e Focar no que Importa',
    description: 'Entenda por que a busca manual de editais não funciona e como um filtro por perfil transforma 1.500 publicações diárias em 12 oportunidades relevantes.',
    images: ['/api/og?title=Como+Filtrar+Editais+de+Licita%C3%A7%C3%A3o'],
  },
};

const articleSchema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: 'Como filtrar editais de licitação e focar no que importa',
  description:
    'Por que a busca manual de editais não funciona e como um filtro inteligente transforma milhares de publicações em oportunidades relevantes para o seu setor.',
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
    '@id': 'https://smartlic.tech/como-filtrar-editais',
  },
};

const howToSchema = {
  '@context': 'https://schema.org',
  '@type': 'HowTo',
  name: 'Como filtrar editais de licitação e focar no que importa',
  description: 'Transforme milhares de publicações diárias em oportunidades relevantes com filtro inteligente por perfil.',
  step: [
    { '@type': 'HowToStep', position: 1, name: 'Definir perfil da empresa', text: 'Configure setor, CNAE, faixa de valor e estados de atuação como critérios base.' },
    { '@type': 'HowToStep', position: 2, name: 'Aplicar filtro setorial por palavras-chave', text: 'Use palavras-chave do seu segmento para eliminar editais irrelevantes automaticamente.' },
    { '@type': 'HowToStep', position: 3, name: 'Filtrar por faixa de valor', text: 'Defina valor mínimo e máximo compatíveis com seu porte e capacidade.' },
    { '@type': 'HowToStep', position: 4, name: 'Segmentar por geografia', text: 'Selecione os estados onde sua empresa tem viabilidade logística.' },
    { '@type': 'HowToStep', position: 5, name: 'Revisar resultados filtrados', text: 'Analise apenas os editais que passaram por todos os filtros, focando energia nos mais viáveis.' },
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
    href: '/como-priorizar-oportunidades',
    title: 'Como priorizar oportunidades',
  },
];

export default function ComoFiltrarEditais() {
  return (
    <ContentPageLayout
      breadcrumbLabel="Como filtrar editais"
      breadcrumbItems={[
        { label: 'Início', href: '/' },
        { label: 'Guias', href: '/features' },
        { label: 'Como filtrar editais' },
      ]}
      relatedPages={RELATED_PAGES}
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
      {/* breadcrumbSchema emitted by BreadcrumbNav in ContentPageLayout */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }}
      />

      <h1>Como filtrar editais de licitação e focar no que importa</h1>

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O problema não é falta de licitações. É excesso de irrelevância. Todos
        os dias, milhares de editais são publicados nos portais PNCP,
        ComprasGov e Portal de Compras Públicas. Para uma empresa de
        engenharia, por exemplo, menos de 1% dessas publicações são realmente
        relevantes. O desafio não é encontrar licitações — é separar as que
        importam das que só consomem tempo.
      </p>

      <h2>Por que a busca manual não funciona</h2>

      <p>
        A maioria das empresas ainda monitora licitações da forma tradicional:
        acessa os portais oficiais, digita palavras-chave e navega páginas de
        resultados. Esse processo tem três problemas estruturais que nenhum
        esforço individual resolve.
      </p>

      <h3>Volume impossível de processar</h3>
      <p>
        O PNCP sozinho publica milhares de contratações por dia, cobrindo 27
        UFs. Para monitorar tudo com profundidade, seria necessário analisar
        centenas de resultados diariamente. Nenhuma equipe de licitações
        consegue fazer isso com consistência — e quando tenta, a qualidade
        da análise cai.
      </p>

      <h3>Fontes dispersas</h3>
      <p>
        Não existe um portal único que consolide todas as licitações do Brasil.
        O PNCP cobre a maioria, mas o Portal de Compras Públicas e o ComprasGov
        publicam editais que não aparecem lá — e vice-versa. Monitorar uma
        fonte já é difícil. Monitorar três, com formatos diferentes e
        atualizações em horários diferentes, é impraticável no dia a dia.
      </p>

      <h3>Palavras-chave são ambíguas</h3>
      <p>
        Buscar por &quot;manutenção&quot; retorna manutenção predial,
        manutenção de veículos, manutenção de equipamentos médicos, manutenção
        de software e dezenas de outros objetos completamente diferentes entre
        si. A mesma palavra que traz editais relevantes traz uma avalanche de
        ruído.
      </p>

      <h2>O que um bom filtro precisa considerar</h2>

      <p>
        Um filtro eficaz vai além de palavras-chave. Ele cruza múltiplas
        dimensões para determinar se um edital é relevante para uma empresa
        específica:
      </p>

      <ul>
        <li>
          <strong>Setor de atuação</strong> — não apenas o objeto, mas o
          contexto completo. Uma licitação de &quot;serviços de limpeza&quot;
          pode ser facilities ou pode ser descontaminação industrial. Setores
          completamente diferentes.
        </li>
        <li>
          <strong>Faixa de valor</strong> — editais dentro da capacidade
          financeira e operacional da empresa.
        </li>
        <li>
          <strong>Região</strong> — UFs onde a empresa tem presença ou
          capacidade logística real.
        </li>
        <li>
          <strong>Prazo</strong> — tempo suficiente para preparar uma proposta
          de qualidade.
        </li>
        <li>
          <strong>Modalidade</strong> — compatível com o perfil competitivo da
          empresa.
        </li>
      </ul>

      <h2>Filtro por palavra-chave vs. filtro por perfil</h2>

      <p>
        Aqui está a diferença fundamental entre a busca tradicional e um filtro
        inteligente.
      </p>

      <p>
        <strong>Filtro por palavra-chave</strong> pergunta: &quot;esse edital
        contém a palavra X?&quot;. É rápido, mas impreciso. A palavra
        &quot;informática&quot; aparece tanto em editais de compra de
        computadores quanto em cursos de capacitação em informática básica.
        Muito ruído, pouca relevância.
      </p>

      <p>
        <strong>Filtro por perfil</strong> pergunta: &quot;esse edital é
        compatível com o que essa empresa faz, na faixa de valor que ela
        opera, nas regiões onde ela atua?&quot;. Menos editais, mais
        relevância.{' '}
        <Link href="/como-avaliar-licitacao">
          Veja os critérios usados para avaliar essa compatibilidade
        </Link>.
      </p>

      {/* Practical Example */}
      <div className="not-prose my-8 sm:my-10 border-l-4 border-brand-blue bg-surface-1 rounded-r-xl p-4 sm:p-6 lg:p-8">
        <h3 className="font-bold text-ink text-base sm:text-lg mb-3 sm:mb-4">
          Na prática: de 1.500 para 12
        </h3>
        <p className="text-sm sm:text-base text-ink-secondary mb-3 sm:mb-4 leading-relaxed">
          Cenário real de uma empresa de mobiliário corporativo em uma semana
          típica:
        </p>
        <ul className="space-y-2.5 sm:space-y-3 text-sm sm:text-base text-ink-secondary">
          <li className="flex items-start gap-2.5 sm:gap-3">
            <span className="text-ink-muted font-mono text-xs sm:text-sm mt-0.5 shrink-0 tabular-nums w-10 text-right">1.500</span>
            <span>editais publicados nas 3 fontes oficiais para 27 UFs</span>
          </li>
          <li className="flex items-start gap-2.5 sm:gap-3">
            <span className="text-ink-muted font-mono text-xs sm:text-sm mt-0.5 shrink-0 tabular-nums w-10 text-right">180</span>
            <span>após filtro por setor — 12% relacionados a mobiliário</span>
          </li>
          <li className="flex items-start gap-2.5 sm:gap-3">
            <span className="text-ink-muted font-mono text-xs sm:text-sm mt-0.5 shrink-0 tabular-nums w-10 text-right">45</span>
            <span>após filtro por faixa de valor (R$ 100k a R$ 2M)</span>
          </li>
          <li className="flex items-start gap-2.5 sm:gap-3">
            <span className="text-ink-muted font-mono text-xs sm:text-sm mt-0.5 shrink-0 tabular-nums w-10 text-right">22</span>
            <span>após filtro por UFs de atuação (SP, RJ, MG, PR)</span>
          </li>
          <li className="flex items-start gap-2.5 sm:gap-3">
            <span className="text-brand-blue font-mono text-xs sm:text-sm mt-0.5 font-bold shrink-0 tabular-nums w-10 text-right">12</span>
            <span><strong className="text-ink">após classificação IA de relevância</strong> — 0,8% do total</span>
          </li>
        </ul>
        <p className="text-sm sm:text-base text-ink mt-3 sm:mt-4 font-medium">
          Esses 12 editais são os que realmente merecem atenção. Os outros
          1.488 seriam tempo perdido.{' '}
          <Link href="/como-evitar-prejuizo-licitacao" className="text-brand-blue hover:underline">
            E tempo perdido em licitações se traduz diretamente em prejuízo
          </Link>.
        </p>
      </div>

      <h2>Como o SmartLic aborda esse problema</h2>

      <p>
        O SmartLic agrega dados de três fontes oficiais — PNCP, Portal de
        Compras Públicas e ComprasGov — e aplica um pipeline de filtragem em
        múltiplas etapas:
      </p>

      <ol>
        <li>
          <strong>Consolidação</strong> — busca simultânea nas 3 fontes com
          deduplicação automática, já que o mesmo edital pode aparecer em mais
          de um portal.
        </li>
        <li>
          <strong>Filtro por UF e valor</strong> — eliminação rápida de editais
          fora do escopo geográfico e financeiro da empresa.
        </li>
        <li>
          <strong>Classificação setorial</strong> — análise por keywords com
          pontuação de densidade, complementada por classificação com IA para
          editais ambíguos.
        </li>
        <li>
          <strong>Avaliação de viabilidade</strong> — scoring de 4 fatores
          (modalidade, prazo, valor, geografia) para cada edital aprovado.
        </li>
      </ol>

      <p>
        O resultado é um conjunto reduzido de editais classificados por
        relevância e viabilidade — prontos para análise humana qualificada.
        Sem ruído, sem repetição, sem perda de tempo.
      </p>

      {/* CTA Section */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Pare de perder tempo com editais irrelevantes
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic filtra milhares de licitações e entrega apenas as que
          importam para o seu setor, região e faixa de valor.
        </p>
        <Link
          href="/signup?source=content-filtrar"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
        >
          Comece Grátis
        </Link>
      </div>
    </ContentPageLayout>
  );
}
