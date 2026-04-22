/**
 * STORY-SEO-008: Pillar Pages — Topical Authority
 *
 * Metadata + spoke links for the 3 pillar pages under /guia/[slug]:
 *   - /guia/licitacoes   → Guia Completo de Licitações Públicas no Brasil
 *   - /guia/lei-14133    → Tudo Sobre a Lei 14.133/2021
 *   - /guia/pncp         → PNCP: Portal Nacional de Contratações Públicas
 *
 * Each pillar:
 *   • 3,000-5,000 words of original content
 *   • ≥10 internal links (spokes) to existing /blog/* posts
 *   • ≥5 outbound authority links (gov.br, planalto.gov.br, tcu.gov.br)
 *   • JSON-LD Article + BreadcrumbList + ItemList (spokes)
 */

export interface PillarSpokeLink {
  /** Spoke slug under /blog */
  slug: string;
  /** Display title in "Artigos Relacionados" section */
  title: string;
  /** 1-sentence description (~100-140 chars) */
  description: string;
}

export interface PillarAuthorityLink {
  /** Link URL — must be https and to an authoritative domain */
  url: string;
  /** Display text */
  text: string;
}

export interface PillarMeta {
  /** URL slug */
  slug: string;
  /** H1 title */
  title: string;
  /** SEO description — 150-160 chars */
  description: string;
  /** Short OG/Twitter headline */
  shortTitle: string;
  /** ISO date */
  publishDate: string;
  /** ISO date */
  lastModified: string;
  /** Estimated word count of content.tsx */
  wordCount: number;
  /** Top-of-funnel head-term keywords */
  keywords: string[];
  /** Internal spokes linked throughout (≥10) */
  spokes: PillarSpokeLink[];
  /** Outbound authoritative links (≥5) */
  authorityLinks: PillarAuthorityLink[];
  /** FAQ for FAQPage JSON-LD (5 entries) */
  faq: { question: string; answer: string }[];
}

export const PILLARS: PillarMeta[] = [
  {
    slug: 'licitacoes',
    title: 'Guia Completo de Licitações Públicas no Brasil',
    shortTitle: 'Guia de Licitações Públicas',
    description:
      'Entenda como funcionam as licitações públicas no Brasil em 2026: modalidades da Lei 14.133, documentos de habilitação, passo a passo para participar, erros comuns e automação com SmartLic.',
    publishDate: '2026-04-22',
    lastModified: '2026-04-22',
    wordCount: 3800,
    keywords: [
      'licitações públicas',
      'como participar de licitação',
      'guia de licitações',
      'licitações Brasil',
      'pregão eletrônico',
      'lei 14.133',
    ],
    spokes: [
      {
        slug: 'como-aumentar-taxa-vitoria-licitacoes',
        title: 'Como Aumentar sua Taxa de Vitória em Licitações',
        description:
          'Empresas B2G aumentam de 8% para 25% a taxa de adjudicação usando triagem inteligente e análise de viabilidade.',
      },
      {
        slug: 'vale-a-pena-disputar-pregao',
        title: 'Vale a Pena Disputar este Pregão?',
        description: '4 fatores de viabilidade para decidir em minutos se um edital merece proposta.',
      },
      {
        slug: 'reduzir-tempo-analisando-editais-irrelevantes',
        title: 'Como Reduzir 80% do Tempo Analisando Editais Irrelevantes',
        description: 'Automação de triagem + filtros setoriais eliminam ruído antes do analista humano entrar em cena.',
      },
      {
        slug: 'escolher-editais-maior-probabilidade-vitoria',
        title: 'Como Escolher Editais com Maior Probabilidade de Vitória',
        description: 'Framework de scoring que combina modalidade, timeline, valor e geografia para priorizar pipeline.',
      },
      {
        slug: 'erro-operacional-perder-contratos-publicos',
        title: 'O Erro Operacional que Faz Empresas Perderem Contratos',
        description: 'Falha de triagem mais comum em setores B2G — e como corrigir antes do próximo pregão.',
      },
      {
        slug: 'checklist-habilitacao-licitacao-2026',
        title: 'Checklist de Habilitação em Licitações 2026',
        description: 'Documentação completa de habilitação jurídica, fiscal, técnica e econômico-financeira.',
      },
      {
        slug: 'analise-viabilidade-editais-guia',
        title: 'Guia de Análise de Viabilidade de Editais',
        description: '4 fatores quantitativos que separam edital-oportunidade de edital-armadilha.',
      },
      {
        slug: 'como-calcular-preco-proposta-licitacao',
        title: 'Como Calcular o Preço da Proposta em Licitação',
        description: 'Metodologia de pricing B2G com margens defensáveis e BDI correto.',
      },
      {
        slug: 'mei-microempresa-vantagens-licitacoes',
        title: 'Vantagens de MEI e Microempresa em Licitações',
        description: 'Benefícios LC 123/2006: empate ficto, exclusividade até R$80k, cota de 25%.',
      },
      {
        slug: 'impugnacao-edital-quando-como-contestar',
        title: 'Impugnação de Edital: Quando e Como Contestar',
        description: 'Prazos, fundamentos e template para impugnar edital viciado.',
      },
    ],
    authorityLinks: [
      { url: 'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm', text: 'Lei 14.133/2021 (Planalto)' },
      { url: 'https://pncp.gov.br/', text: 'Portal Nacional de Contratações Públicas (PNCP)' },
      { url: 'https://portal.tcu.gov.br/', text: 'Tribunal de Contas da União (TCU)' },
      { url: 'https://www.gov.br/compras/pt-br', text: 'Compras.gov.br' },
      { url: 'https://www.gov.br/cgu/pt-br', text: 'Controladoria-Geral da União (CGU)' },
    ],
    faq: [
      {
        question: 'O que é uma licitação pública?',
        answer:
          'Licitação pública é o processo administrativo pelo qual órgãos da administração pública selecionam a proposta mais vantajosa para contratar bens, serviços ou obras, seguindo os princípios da isonomia, economicidade e legalidade estabelecidos pela Lei 14.133/2021.',
      },
      {
        question: 'Quais são as modalidades de licitação na Lei 14.133?',
        answer:
          'A Lei 14.133/2021 prevê cinco modalidades: pregão (eletrônico ou presencial, padrão para bens e serviços comuns), concorrência, diálogo competitivo, concurso e leilão. A modalidade pregão é a mais usada em 2026 devido à celeridade.',
      },
      {
        question: 'Como me cadastrar para participar de licitações federais?',
        answer:
          'É necessário cadastro no SICAF (Sistema de Cadastramento Unificado de Fornecedores) via gov.br/compras. O cadastro é gratuito e exige documentação jurídica, fiscal, técnica e econômico-financeira conforme habilitação exigida pela Lei 14.133.',
      },
      {
        question: 'MEI pode participar de licitações públicas?',
        answer:
          'Sim. MEI e microempresas têm tratamento diferenciado pela LC 123/2006: empate ficto em pregões, exclusividade em contratações até R$ 80.000 e cota reservada de 25% em licitações divisíveis.',
      },
      {
        question: 'Quanto tempo leva para ganhar a primeira licitação?',
        answer:
          'Empresas B2G levam em média 6 a 12 meses entre o primeiro cadastro e a primeira adjudicação. Esse prazo reduz significativamente com triagem automatizada de editais relevantes e análise de viabilidade antes da participação.',
      },
    ],
  },
  {
    slug: 'lei-14133',
    title: 'Tudo Sobre a Lei 14.133/2021: A Nova Lei de Licitações',
    shortTitle: 'Lei 14.133 — Guia Completo',
    description:
      'Guia completo da Lei 14.133/2021, a Nova Lei de Licitações: modalidades, critérios de julgamento, fases, habilitação, sanções e diferenças em relação à Lei 8.666/93.',
    publishDate: '2026-04-22',
    lastModified: '2026-04-22',
    wordCount: 4200,
    keywords: [
      'lei 14.133',
      'nova lei de licitações',
      'lei 14.133/2021',
      'lei de licitações e contratos',
      'lei 14.133 vs 8.666',
    ],
    spokes: [
      {
        slug: 'lei-14133-guia-fornecedores',
        title: 'Lei 14.133 — Guia Prático para Fornecedores',
        description: 'O que muda para quem vende ao governo: modalidades, critérios e novas obrigações.',
      },
      {
        slug: 'erro-operacional-perder-contratos-publicos',
        title: 'Erros Operacionais sob a Lei 14.133',
        description: 'Falhas típicas de quem migrou da 8.666 para a 14.133 sem revisar processos internos.',
      },
      {
        slug: 'checklist-habilitacao-licitacao-2026',
        title: 'Habilitação na Lei 14.133: Checklist 2026',
        description: 'Documentação atualizada conforme artigos 62-70 da Lei 14.133/2021.',
      },
      {
        slug: 'pregao-eletronico-guia-passo-a-passo',
        title: 'Pregão Eletrônico Passo a Passo',
        description: 'Modalidade-padrão sob a 14.133 para bens e serviços comuns.',
      },
      {
        slug: 'impugnacao-edital-quando-como-contestar',
        title: 'Impugnação sob a Lei 14.133',
        description: 'Prazos do art. 164 e fundamentos legais para contestar edital.',
      },
      {
        slug: 'sicaf-como-cadastrar-manter-ativo-2026',
        title: 'SICAF em 2026: Cadastro e Manutenção',
        description: 'Pré-requisito para participar de certames federais sob a 14.133.',
      },
      {
        slug: 'analise-viabilidade-editais-guia',
        title: 'Análise de Viabilidade sob a Nova Lei',
        description: 'Fatores quantitativos que mudaram com o novo regime jurídico.',
      },
      {
        slug: 'como-calcular-preco-proposta-licitacao',
        title: 'Precificação na Lei 14.133',
        description: 'Matriz de risco, reajustes e reequilíbrio segundo os arts. 124-137.',
      },
      {
        slug: 'mei-microempresa-vantagens-licitacoes',
        title: 'ME/EPP e a Lei 14.133',
        description: 'Como a LC 123/2006 dialoga com o novo regime da 14.133.',
      },
      {
        slug: 'vale-a-pena-disputar-pregao',
        title: 'Viabilidade de Pregões sob a 14.133',
        description: 'Decisão go/no-go em 4 fatores operacionais.',
      },
    ],
    authorityLinks: [
      { url: 'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm', text: 'Lei 14.133/2021 — Planalto' },
      { url: 'https://www.planalto.gov.br/ccivil_03/leis/l8666cons.htm', text: 'Lei 8.666/93 (revogada) — Planalto' },
      { url: 'https://portal.tcu.gov.br/', text: 'Tribunal de Contas da União (TCU)' },
      { url: 'https://www.gov.br/agu/pt-br', text: 'Advocacia-Geral da União (AGU)' },
      { url: 'https://enap.gov.br/', text: 'Escola Nacional de Administração Pública (Enap)' },
    ],
    faq: [
      {
        question: 'Quando a Lei 14.133/2021 entrou em vigor integralmente?',
        answer:
          'A Lei 14.133/2021 foi publicada em 01/04/2021 e passou a ser de aplicação obrigatória em 30/12/2023, após sucessivas prorrogações do período de transição. Desde então, todas as novas contratações públicas no Brasil devem seguir o novo regime jurídico, com raras exceções de contratos em curso.',
      },
      {
        question: 'A Lei 8.666/93 ainda vale em 2026?',
        answer:
          'Não para novas licitações. A Lei 8.666/93 foi integralmente revogada pela 14.133 a partir de 30/12/2023. Contratos firmados antes dessa data continuam regidos pela lei anterior, mas qualquer novo certame deve seguir a 14.133.',
      },
      {
        question: 'Quais são as principais diferenças entre a Lei 8.666 e a 14.133?',
        answer:
          'As principais mudanças são: (1) pregão torna-se modalidade-padrão para bens e serviços comuns, (2) introdução do diálogo competitivo, (3) matriz de risco obrigatória em contratos complexos, (4) agente de contratação substitui a antiga comissão, (5) critério julgamento por maior desconto e maior retorno econômico.',
      },
      {
        question: 'O que é o diálogo competitivo na Lei 14.133?',
        answer:
          'Diálogo competitivo é uma nova modalidade prevista no art. 32 da Lei 14.133, usada em contratações complexas em que a administração dialoga com licitantes previamente selecionados para desenvolver alternativas que atendam às necessidades específicas, antes da apresentação das propostas finais.',
      },
      {
        question: 'Quem fiscaliza o cumprimento da Lei 14.133?',
        answer:
          'No âmbito federal, o TCU (Tribunal de Contas da União) e a CGU (Controladoria-Geral da União) fiscalizam os certames. Nos estados e municípios, os respectivos Tribunais de Contas estaduais e municipais exercem a fiscalização, junto com Ministério Público e controle social.',
      },
    ],
  },
  {
    slug: 'pncp',
    title: 'PNCP: Portal Nacional de Contratações Públicas — Guia Completo',
    shortTitle: 'PNCP — Guia Completo',
    description:
      'Entenda o PNCP (Portal Nacional de Contratações Públicas): o que é, como consultar editais, API pública, obrigatoriedade legal e como usar a plataforma para encontrar oportunidades B2G.',
    publishDate: '2026-04-22',
    lastModified: '2026-04-22',
    wordCount: 3600,
    keywords: [
      'pncp',
      'portal nacional de contratações públicas',
      'pncp.gov.br',
      'como usar o PNCP',
      'api pncp',
      'consultar editais pncp',
    ],
    spokes: [
      {
        slug: 'pncp-guia-completo-empresas',
        title: 'PNCP para Empresas: Guia Operacional',
        description: 'Como extrair editais, montar alertas e navegar o portal oficial na prática.',
      },
      {
        slug: 'reduzir-tempo-analisando-editais-irrelevantes',
        title: 'Filtrando Editais no PNCP',
        description: 'Parâmetros de busca e automação para não perder tempo com ruído.',
      },
      {
        slug: 'como-aumentar-taxa-vitoria-licitacoes',
        title: 'Do PNCP à Vitória: Taxa de Adjudicação',
        description: 'Como transformar radar PNCP em pipeline com taxa de vitória acima da média.',
      },
      {
        slug: 'lei-14133-guia-fornecedores',
        title: 'Obrigatoriedade do PNCP na Lei 14.133',
        description: 'Art. 54 e 174 tornaram PNCP o único canal oficial de publicação de editais.',
      },
      {
        slug: 'vale-a-pena-disputar-pregao',
        title: 'Viabilidade Baseada em Dados do PNCP',
        description: 'Histórico de certames similares publicado no portal informa decisão go/no-go.',
      },
      {
        slug: 'escolher-editais-maior-probabilidade-vitoria',
        title: 'Scoring de Editais do PNCP',
        description: 'Modelagem de probabilidade a partir dos metadados expostos pela API PNCP.',
      },
      {
        slug: 'analise-viabilidade-editais-guia',
        title: 'Análise de Viabilidade com PNCP',
        description: 'Fluxo de dados PNCP → viabilidade 4 fatores → decisão.',
      },
      {
        slug: 'pregao-eletronico-guia-passo-a-passo',
        title: 'Pregões Eletrônicos via PNCP',
        description: 'O que mudou desde que o PNCP tornou-se canal único obrigatório.',
      },
      {
        slug: 'checklist-habilitacao-licitacao-2026',
        title: 'Habilitação + PNCP',
        description: 'Como o CRC e o SICAF integram-se à publicação no PNCP.',
      },
      {
        slug: 'como-calcular-preco-proposta-licitacao',
        title: 'Precificação com Dados Históricos PNCP',
        description: 'Usando 2M+ contratos no portal para benchmark de valores.',
      },
    ],
    authorityLinks: [
      { url: 'https://pncp.gov.br/', text: 'PNCP — Portal Nacional de Contratações Públicas' },
      { url: 'https://pncp.gov.br/api/consulta/', text: 'Manual da API Pública do PNCP' },
      { url: 'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art174', text: 'Art. 174 da Lei 14.133 — Obrigatoriedade PNCP' },
      { url: 'https://www.gov.br/compras/pt-br', text: 'Compras.gov.br' },
      { url: 'https://www.gov.br/governodigital/pt-br', text: 'Governo Digital' },
    ],
    faq: [
      {
        question: 'O que é o PNCP?',
        answer:
          'O PNCP (Portal Nacional de Contratações Públicas) é o portal oficial único para divulgação de editais, atas de registro de preço, contratos e demais atos de contratação pública no Brasil, instituído pela Lei 14.133/2021. Desde 30/12/2023 é obrigatório para todos os entes federativos.',
      },
      {
        question: 'Como pesquisar editais no PNCP?',
        answer:
          'Em pncp.gov.br, na aba "Consulta de Contratações", é possível filtrar por palavra-chave, UF, modalidade, valor, data de publicação e situação. Resultados podem ser exportados em CSV ou consumidos via API pública gratuita em pncp.gov.br/api/consulta/v1.',
      },
      {
        question: 'A API do PNCP é pública e gratuita?',
        answer:
          'Sim. A API de consulta do PNCP é pública, gratuita e não requer autenticação. O endpoint principal é https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao. Existem limites de paginação (máx. 50 registros/página desde fev/2026) e rate limiting.',
      },
      {
        question: 'Quais órgãos são obrigados a publicar no PNCP?',
        answer:
          'Todos os entes da administração pública direta, autárquica e fundacional da União, Estados, Distrito Federal e Municípios, bem como as empresas estatais controladas pelo Poder Público, conforme art. 174 da Lei 14.133/2021.',
      },
      {
        question: 'Como receber alertas de novos editais no PNCP?',
        answer:
          'O PNCP não oferece notificações nativas. Para receber alertas setoriais ou por palavra-chave, é necessário usar a API pública com agendamento próprio ou plataformas terceiras como o SmartLic, que monitora 24/7 o PNCP + Compras.gov.br + Portal de Compras Públicas em um único radar.',
      },
    ],
  },
];

export function getPillarBySlug(slug: string): PillarMeta | undefined {
  return PILLARS.find((p) => p.slug === slug);
}

export function getAllPillarSlugs(): string[] {
  return PILLARS.map((p) => p.slug);
}
