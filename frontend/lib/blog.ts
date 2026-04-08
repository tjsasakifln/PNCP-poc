/**
 * STORY-261 AC6 / STORY-262 AC20: Blog article metadata index and utilities
 *
 * Central registry for all blog articles. Provides access patterns
 * used by listing page, dynamic route, RSS feed, and sitemap.
 */

export type BlogCategory = 'Empresas B2G' | 'Consultorias de Licitação' | 'Guias';

export interface BlogArticleMeta {
  slug: string;
  title: string;
  description: string;
  category: BlogCategory;
  tags: string[];
  publishDate: string;
  lastModified?: string;
  readingTime: string;
  wordCount: number;
  keywords: string[];
  relatedSlugs: string[];
  sources?: string[];
  authorSlug?: string;
}

/**
 * Calculate reading time based on word count (~200 words/minute).
 */
export function calculateReadingTime(wordCount: number): string {
  const minutes = Math.max(1, Math.ceil(wordCount / 200));
  return `${minutes} min de leitura`;
}

/**
 * Central article metadata registry.
 *
 * STORY-262: 15 B2G articles (empresas-b2g cluster)
 * STORY-263: 15 Consultorias articles (consultorias-de-licitacao cluster)
 */
export const BLOG_ARTICLES: BlogArticleMeta[] = [
  // ──────────────────────────────────────────────
  // STORY-262: Empresas B2G — 15 articles
  // ──────────────────────────────────────────────

  // B2G-01
  {
    slug: 'como-aumentar-taxa-vitoria-licitacoes',
    title: 'Como Aumentar sua Taxa de Vitória em Licitações sem Contratar mais Analistas',
    description:
      'Descubra como empresas B2G aumentam de 8% para 25% a taxa de adjudicação em pregões usando análise de viabilidade e triagem inteligente de editais.',
    category: 'Empresas B2G',
    tags: ['taxa de vitória', 'triagem inteligente', 'viabilidade', 'estratégia'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'taxa de vitória em licitações',
      'como ganhar mais licitações',
      'eficiência setor de licitação',
      'análise de viabilidade pregão',
    ],
    relatedSlugs: [
      'vale-a-pena-disputar-pregao',
      'reduzir-tempo-analisando-editais-irrelevantes',
      'escolher-editais-maior-probabilidade-vitoria',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-02
  {
    slug: 'erro-operacional-perder-contratos-publicos',
    title: 'O Erro Operacional que Faz Empresas Perderem Contratos Públicos de R$ 150 mil',
    description:
      'Empresas B2G perdem contratos de seis dígitos por falhas de triagem. Conheça o erro operacional mais comum e como corrigi-lo antes do próximo pregão.',
    category: 'Empresas B2G',
    tags: ['erros operacionais', 'contratos públicos', 'triagem', 'viabilidade'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2300),
    wordCount: 2300,
    keywords: [
      'perder licitação por erro',
      'erro em licitação pública',
      'como não perder pregão',
      'falha operacional licitação',
    ],
    relatedSlugs: [
      'custo-invisivel-disputar-pregoes-errados',
      'reduzir-tempo-analisando-editais-irrelevantes',
      'empresas-vencem-30-porcento-pregoes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-03
  {
    slug: 'vale-a-pena-disputar-pregao',
    title: 'Como Saber se Vale a Pena Disputar um Pregão antes de Investir Horas na Análise',
    description:
      'Aprenda os 4 critérios objetivos para avaliar a viabilidade de um pregão em menos de 5 minutos — antes de comprometer sua equipe com análise completa.',
    category: 'Empresas B2G',
    tags: ['viabilidade', 'avaliação de pregão', 'triagem rápida', 'critérios objetivos'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'vale a pena disputar licitação',
      'como avaliar pregão',
      'viabilidade de licitação',
      'análise rápida de edital',
    ],
    relatedSlugs: [
      'como-aumentar-taxa-vitoria-licitacoes',
      'como-calcular-preco-proposta-licitacao',
      'disputar-todas-licitacoes-matematica-real',
      'escolher-editais-maior-probabilidade-vitoria',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-04
  {
    slug: 'clausulas-escondidas-editais-licitacao',
    title: '7 Cláusulas Escondidas em Editais que Eliminam Fornecedores Experientes',
    description:
      'Conheça as 7 cláusulas escondidas em editais de licitação que mais eliminam empresas qualificadas — e como identificá-las na triagem antes de investir.',
    category: 'Empresas B2G',
    tags: ['cláusulas de edital', 'habilitação', 'Lei 14.133', 'riscos em editais'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'cláusulas edital licitação',
      'armadilhas em editais',
      'como ler edital de licitação',
      'erros comuns em licitação',
    ],
    relatedSlugs: [
      'erro-operacional-perder-contratos-publicos',
      'estruturar-setor-licitacao-5-milhoes',
      'empresas-vencem-30-porcento-pregoes',
    ],
    sources: [
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'TCU — Jurisprudência sobre habilitação em licitações',
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
    ],
  },

  // B2G-05
  {
    slug: 'reduzir-tempo-analisando-editais-irrelevantes',
    title: 'Como Reduzir em 50% o Tempo Gasto Analisando Editais Irrelevantes',
    description:
      'Empresas B2G gastam até 40 horas por mês lendo editais que serão descartados. Veja como cortar esse tempo pela metade com triagem estruturada e automação.',
    category: 'Empresas B2G',
    tags: ['produtividade', 'triagem de editais', 'eficiência operacional', 'automação'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2300),
    wordCount: 2300,
    keywords: [
      'reduzir tempo analisando editais',
      'otimizar setor de licitação',
      'eficiência em licitações',
      'triagem de editais',
    ],
    relatedSlugs: [
      'equipe-40-horas-mes-editais-descartados',
      'como-aumentar-taxa-vitoria-licitacoes',
      'licitacao-volume-ou-inteligencia',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-06
  {
    slug: 'disputar-todas-licitacoes-matematica-real',
    title: 'Vale a Pena Disputar Todas as Licitações do Seu Segmento? A Matemática Real',
    description:
      'Análise quantitativa: disputar 100% das licitações do seu setor gera prejuízo operacional. Veja os números reais e a estratégia que maximiza o retorno.',
    category: 'Empresas B2G',
    tags: ['ROI em licitações', 'matemática', 'estratégia seletiva', 'análise quantitativa'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'quantas licitações participar',
      'estratégia de licitação',
      'ROI em licitações',
      'matemática de licitação',
    ],
    relatedSlugs: [
      'licitacao-volume-ou-inteligencia',
      'vale-a-pena-disputar-pregao',
      'custo-invisivel-disputar-pregoes-errados',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-07
  {
    slug: 'estruturar-setor-licitacao-5-milhoes',
    title: 'Como Estruturar um Setor de Licitação Enxuto para Faturar R$ 5 Milhões por Ano',
    description:
      'Modelo operacional comprovado: como montar um setor de licitação enxuto com 2-3 pessoas dedicadas capaz de gerar R$ 5 milhões/ano em contratos públicos.',
    category: 'Empresas B2G',
    tags: ['setor de licitação', 'modelo operacional', 'equipe enxuta', 'faturamento'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'como montar setor de licitação',
      'estruturar equipe de licitação',
      'faturar com licitações',
      'setor de licitação empresa',
    ],
    relatedSlugs: [
      'pipeline-licitacoes-funil-comercial',
      'como-aumentar-taxa-vitoria-licitacoes',
      'empresas-vencem-30-porcento-pregoes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-08
  {
    slug: 'custo-invisivel-disputar-pregoes-errados',
    title: 'O Custo Invisível de Disputar Pregões Errados',
    description:
      'Além do tempo perdido: conheça os 6 custos invisíveis de disputar pregões sem análise prévia de viabilidade e o impacto no seu faturamento anual.',
    category: 'Empresas B2G',
    tags: ['custos ocultos', 'prejuízo em licitação', 'análise de viabilidade', 'ROI'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2300),
    wordCount: 2300,
    keywords: [
      'custo de participar de licitação',
      'prejuízo em licitação',
      'custos ocultos licitação',
      'pregão errado',
    ],
    relatedSlugs: [
      'erro-operacional-perder-contratos-publicos',
      'disputar-todas-licitacoes-matematica-real',
      'equipe-40-horas-mes-editais-descartados',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-09
  {
    slug: 'escolher-editais-maior-probabilidade-vitoria',
    title: 'Como Escolher Editais com Maior Probabilidade de Vitória',
    description:
      'Framework prático com 4 indicadores preditivos para selecionar editais onde sua empresa tem vantagem competitiva real — antes de investir na proposta.',
    category: 'Empresas B2G',
    tags: ['seleção de editais', 'indicadores preditivos', 'vantagem competitiva', 'framework'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'como escolher licitação',
      'probabilidade de ganhar licitação',
      'selecionar editais',
      'vantagem competitiva licitação',
    ],
    relatedSlugs: [
      'como-aumentar-taxa-vitoria-licitacoes',
      'vale-a-pena-disputar-pregao',
      'disputar-todas-licitacoes-matematica-real',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-10
  {
    slug: 'licitacao-volume-ou-inteligencia',
    title: 'Licitação por Volume ou por Inteligência? Qual Estratégia Dá mais Lucro',
    description:
      'Comparação objetiva entre as estratégias de volume e inteligência em licitações públicas: custos, margens, riscos, casos reais e qual dá mais lucro.',
    category: 'Empresas B2G',
    tags: ['estratégia', 'volume vs inteligência', 'margem de lucro', 'comparativo'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'estratégia de licitação',
      'volume vs qualidade licitação',
      'como lucrar com licitações',
      'inteligência em licitações',
    ],
    relatedSlugs: [
      'disputar-todas-licitacoes-matematica-real',
      'como-aumentar-taxa-vitoria-licitacoes',
      'reduzir-tempo-analisando-editais-irrelevantes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-11
  {
    slug: 'orgaos-risco-atraso-pagamento-licitacao',
    title: 'Como Identificar Órgãos com Maior Risco de Atraso no Pagamento',
    description:
      'Guia prático para verificar o histórico de pagamento de órgãos públicos antes de disputar um pregão — com fontes oficiais e indicadores de risco.',
    category: 'Empresas B2G',
    tags: ['risco de pagamento', 'órgãos públicos', 'Portal da Transparência', 'due diligence'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2300),
    wordCount: 2300,
    keywords: [
      'atraso pagamento governo',
      'órgão público paga em dia',
      'risco de pagamento licitação',
      'inadimplência governo',
    ],
    relatedSlugs: [
      'custo-invisivel-disputar-pregoes-errados',
      'escolher-editais-maior-probabilidade-vitoria',
      'clausulas-escondidas-editais-licitacao',
    ],
    sources: [
      'Portal da Transparência (portaldatransparencia.gov.br)',
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-12
  {
    slug: 'empresas-vencem-30-porcento-pregoes',
    title: 'Empresas que Vencem 30% dos Pregões Fazem Isso Diferente',
    description:
      'Análise de padrões comuns em empresas B2G com taxa de adjudicação acima de 30% em pregões eletrônicos — e as 5 práticas que as separam da média do mercado.',
    category: 'Empresas B2G',
    tags: ['benchmark', 'melhores práticas', 'taxa de adjudicação', 'top performers'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'como ganhar mais pregões',
      'empresas que vencem licitações',
      'melhores práticas licitação',
      'taxa de adjudicação',
    ],
    relatedSlugs: [
      'como-aumentar-taxa-vitoria-licitacoes',
      'estruturar-setor-licitacao-5-milhoes',
      'licitacao-volume-ou-inteligencia',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-13
  {
    slug: 'pipeline-licitacoes-funil-comercial',
    title: 'Como Organizar seu Pipeline de Licitações como um Funil Comercial',
    description:
      'Adapte o conceito de pipeline comercial B2B para licitações: as 5 etapas do funil, métricas de conversão e como garantir previsibilidade de receita.',
    category: 'Empresas B2G',
    tags: ['pipeline', 'funil comercial', 'gestão de oportunidades', 'métricas'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'pipeline de licitações',
      'funil de licitação',
      'gestão de oportunidades licitação',
      'CRM para licitação',
    ],
    relatedSlugs: [
      'estruturar-setor-licitacao-5-milhoes',
      'como-aumentar-taxa-vitoria-licitacoes',
      'empresas-vencem-30-porcento-pregoes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // B2G-14
  {
    slug: 'ata-registro-precos-como-escolher',
    title: 'Ata de Registro de Preços — Como Escolher as que Realmente Valem a Pena',
    description:
      'Nem toda Ata de Registro de Preços é vantajosa. Conheça os 6 critérios objetivos para avaliar se uma ARP vale a adesão da sua empresa — e quando recusar.',
    category: 'Empresas B2G',
    tags: ['ARP', 'ata de registro de preços', 'Lei 14.133', 'avaliação de risco'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'ata de registro de preços',
      'ARP licitação',
      'como escolher ata de registro',
      'vale a pena ata de preços',
    ],
    relatedSlugs: [
      'ata-registro-precos-estrategia-licitacao',
      'clausulas-escondidas-editais-licitacao',
      'escolher-editais-maior-probabilidade-vitoria',
      'disputar-todas-licitacoes-matematica-real',
    ],
    sources: [
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Decreto 11.462/2023 — Sistema de Registro de Preços',
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
    ],
  },

  // B2G-15
  {
    slug: 'equipe-40-horas-mes-editais-descartados',
    title: 'Por Que sua Equipe Passa 40 Horas por Mês Lendo Editais que Descarta',
    description:
      'Análise do problema operacional n.1 em setores de licitação: o custo de 40h/mês em triagem manual de editais. Diagnóstico, causas e solução estruturada.',
    category: 'Empresas B2G',
    tags: ['triagem manual', 'ineficiência operacional', 'custo de oportunidade', 'automação'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2300),
    wordCount: 2300,
    keywords: [
      'tempo perdido lendo editais',
      'ineficiência setor de licitação',
      'triagem manual de editais',
      'automatizar licitação',
    ],
    relatedSlugs: [
      'reduzir-tempo-analisando-editais-irrelevantes',
      'custo-invisivel-disputar-pregoes-errados',
      'como-aumentar-taxa-vitoria-licitacoes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // ─��────────────────────────────────────────────
  // STORY-263: Consultorias de Licitação — 15 articles
  // ──────────────────────────────────────────────

  // CONS-01
  {
    slug: 'aumentar-retencao-clientes-inteligencia-editais',
    title: 'Como Aumentar a Retenção dos seus Clientes com Inteligência em Editais',
    description:
      'Consultorias que entregam inteligência estruturada sobre editais retêm clientes por 3x mais tempo. Veja o framework que transforma análise em diferencial.',
    category: 'Consultorias de Licitação',
    tags: ['retenção de clientes', 'inteligência em editais', 'churn', 'consultoria'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'retenção de clientes consultoria licitação',
      'fidelizar clientes B2G',
      'consultoria de licitação diferencial',
      'inteligência em editais',
    ],
    relatedSlugs: [
      'entregar-mais-resultado-clientes-sem-aumentar-equipe',
      'aumentar-taxa-sucesso-clientes-20-porcento',
      'como-aumentar-taxa-vitoria-licitacoes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-02
  {
    slug: 'analise-edital-diferencial-competitivo-consultoria',
    title: 'Análise de Edital como Diferencial Competitivo para Consultorias',
    description:
      'A análise de editais pode ser commodity ou diferencial. Veja como consultorias estão reposicionando esse serviço para cobrar mais e reter melhor.',
    category: 'Consultorias de Licitação',
    tags: ['diferencial competitivo', 'análise de edital', 'precificação', 'posicionamento'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'diferencial consultoria licitação',
      'análise de edital como serviço',
      'reposicionar consultoria B2G',
      'valor agregado consultoria',
    ],
    relatedSlugs: [
      'consultorias-modernas-inteligencia-priorizar-oportunidades',
      'triagem-editais-vantagem-estrategica-clientes',
      'diagnostico-eficiencia-licitacao-servico-premium',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-03
  {
    slug: 'entregar-mais-resultado-clientes-sem-aumentar-equipe',
    title: 'Como Entregar mais Resultado aos seus Clientes sem Aumentar sua Equipe',
    description:
      'Consultorias de licitação podem dobrar a entrega de análises sem precisar contratar — usando triagem inteligente e automação de análise de viabilidade.',
    category: 'Consultorias de Licitação',
    tags: ['produtividade', 'escalar consultoria', 'automação', 'modelo operacional'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2300),
    wordCount: 2300,
    keywords: [
      'escalar consultoria licitação',
      'produtividade consultoria',
      'entregar mais sem contratar',
      'automação consultoria licitação',
    ],
    relatedSlugs: [
      'escalar-consultoria-sem-depender-horas-tecnicas',
      'aumentar-retencao-clientes-inteligencia-editais',
      'reduzir-ruido-aumentar-performance-pregoes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-04
  {
    slug: 'clientes-perdem-pregoes-boa-documentacao',
    title: 'Por que seus Clientes Perdem Pregões mesmo com Boa Documentação',
    description:
      'Documentação impecável não garante vitória em pregões eletrônicos. O problema está antes: na seleção do edital. A triagem é mais crítica que a proposta.',
    category: 'Consultorias de Licitação',
    tags: ['perda de pregão', 'documentação', 'triagem', 'viabilidade'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2300),
    wordCount: 2300,
    keywords: [
      'perder pregão com documentação certa',
      'por que perco licitação',
      'seleção de edital para pregão',
      'triagem antes da proposta',
    ],
    relatedSlugs: [
      'aumentar-retencao-clientes-inteligencia-editais',
      'erro-operacional-perder-contratos-publicos',
      'escolher-editais-maior-probabilidade-vitoria',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-05
  {
    slug: 'usar-dados-provar-eficiencia-licitacoes',
    title: 'Como Usar Dados para Provar Eficiência no Setor de Licitações',
    description:
      'Consultorias que apresentam dados objetivos de performance — taxa de vitória, economia de tempo e ROI comprovado — conquistam e retêm mais clientes B2G.',
    category: 'Consultorias de Licitação',
    tags: ['KPIs', 'dados de performance', 'ROI', 'reporting'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'KPIs consultoria licitação',
      'medir eficiência licitação',
      'ROI consultoria B2G',
      'dados de performance licitação',
    ],
    relatedSlugs: [
      'aumentar-taxa-sucesso-clientes-20-porcento',
      'aumentar-retencao-clientes-inteligencia-editais',
      'analise-edital-diferencial-competitivo-consultoria',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-06
  {
    slug: 'consultorias-modernas-inteligencia-priorizar-oportunidades',
    title: 'Consultorias Modernas Estão Usando Inteligência para Priorizar Oportunidades',
    description:
      'O mercado de consultoria de licitação está se dividindo: operacional vs. inteligente. Veja o que consultorias de alta performance fazem diferente.',
    category: 'Consultorias de Licitação',
    tags: ['consultoria moderna', 'inteligência artificial', 'priorização', 'alta performance'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'consultoria de licitação moderna',
      'inteligência artificial consultoria',
      'priorizar oportunidades licitação',
      'consultoria licitação 2026',
    ],
    relatedSlugs: [
      'inteligencia-artificial-consultoria-licitacao-2026',
      'nova-geracao-ferramentas-mercado-licitacoes',
      'analise-edital-diferencial-competitivo-consultoria',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-07
  {
    slug: 'triagem-editais-vantagem-estrategica-clientes',
    title: 'Como Transformar Triagem de Editais em Vantagem Estratégica para seus Clientes',
    description:
      'A triagem de editais não precisa ser custo operacional — pode ser o serviço de maior valor percebido e maior diferencial competitivo da sua consultoria.',
    category: 'Consultorias de Licitação',
    tags: ['triagem de editais', 'vantagem estratégica', 'curadoria', 'precificação'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2300),
    wordCount: 2300,
    keywords: [
      'triagem de editais como serviço',
      'vantagem estratégica consultoria',
      'valor da triagem licitação',
      'curadoria de editais',
    ],
    relatedSlugs: [
      'analise-edital-diferencial-competitivo-consultoria',
      'diagnostico-eficiencia-licitacao-servico-premium',
      'vale-a-pena-disputar-pregao',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-08
  {
    slug: 'nova-geracao-ferramentas-mercado-licitacoes',
    title: 'A Nova Geração de Ferramentas que Estão Mudando o Mercado de Licitações',
    description:
      'GovTech, IA classificadora e análise de viabilidade: conheça as novas ferramentas que estão transformando como empresas e consultorias operam em 2026.',
    category: 'Consultorias de Licitação',
    tags: ['GovTech', 'ferramentas de licitação', 'IA', 'evolução do mercado'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'ferramentas para licitação',
      'GovTech Brasil',
      'tecnologia licitação 2026',
      'plataforma de licitação inteligente',
    ],
    relatedSlugs: [
      'inteligencia-artificial-consultoria-licitacao-2026',
      'consultorias-modernas-inteligencia-priorizar-oportunidades',
      'licitacao-volume-ou-inteligencia',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-09
  {
    slug: 'reduzir-ruido-aumentar-performance-pregoes',
    title: 'Como Reduzir Ruído e Aumentar Performance nos Clientes que Disputam Pregões',
    description:
      'O excesso de editais irrelevantes é o maior inimigo da performance. Veja como consultorias aplicam filtros inteligentes para aumentar a taxa de vitória.',
    category: 'Consultorias de Licitação',
    tags: ['reduzir ruído', 'performance', 'filtros inteligentes', 'sinal vs ruído'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2300),
    wordCount: 2300,
    keywords: [
      'reduzir ruído editais',
      'performance em pregões',
      'filtrar editais relevantes',
      'produtividade licitação',
    ],
    relatedSlugs: [
      'entregar-mais-resultado-clientes-sem-aumentar-equipe',
      'reduzir-tempo-analisando-editais-irrelevantes',
      'equipe-40-horas-mes-editais-descartados',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-10
  {
    slug: 'inteligencia-artificial-consultoria-licitacao-2026',
    title: 'O Papel da Inteligência Artificial na Consultoria de Licitação em 2026',
    description:
      'Como a IA está transformando consultorias de licitação em 2026: classificação setorial, análise de viabilidade, priorização e geração de relatórios.',
    category: 'Consultorias de Licitação',
    tags: ['inteligência artificial', 'IA em licitações', 'LLM', 'automação'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'IA em licitações',
      'inteligência artificial consultoria',
      'IA para consultoria de licitação',
      'automação de licitações com IA',
    ],
    relatedSlugs: [
      'consultorias-modernas-inteligencia-priorizar-oportunidades',
      'nova-geracao-ferramentas-mercado-licitacoes',
      'como-aumentar-taxa-vitoria-licitacoes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-11
  {
    slug: 'escalar-consultoria-sem-depender-horas-tecnicas',
    title: 'Como Escalar sua Consultoria sem Depender Apenas de Horas Técnicas',
    description:
      'O modelo de horas técnicas limita o crescimento da consultoria. Conheça 4 modelos de escala que permitem atender mais clientes com a mesma equipe.',
    category: 'Consultorias de Licitação',
    tags: ['escalar consultoria', 'modelo de negócio', 'produtização', 'receita recorrente'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'escalar consultoria de licitação',
      'modelo de negócio consultoria',
      'crescer consultoria B2G',
      'consultoria escalável',
    ],
    relatedSlugs: [
      'entregar-mais-resultado-clientes-sem-aumentar-equipe',
      'diagnostico-eficiencia-licitacao-servico-premium',
      'analise-edital-diferencial-competitivo-consultoria',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-12
  {
    slug: 'identificar-clientes-gargalo-operacional-licitacoes',
    title: 'Como Identificar Clientes com Gargalo Operacional em Licitações',
    description:
      'Guia para consultorias identificarem prospects com dor operacional: os 7 sinais de que uma empresa precisa da sua ajuda e como abordar cada perfil.',
    category: 'Consultorias de Licitação',
    tags: ['prospecção', 'gargalo operacional', 'diagnóstico', 'abordagem comercial'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'prospectar clientes consultoria licitação',
      'gargalo operacional licitação',
      'identificar prospects B2G',
      'vender consultoria de licitação',
    ],
    relatedSlugs: [
      'diagnostico-eficiencia-licitacao-servico-premium',
      'usar-dados-provar-eficiencia-licitacoes',
      'aumentar-retencao-clientes-inteligencia-editais',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-13
  {
    slug: 'diagnostico-eficiencia-licitacao-servico-premium',
    title: 'Diagnóstico de Eficiência em Licitação — Novo Serviço Premium para Consultorias',
    description:
      'Como criar e precificar um serviço de diagnóstico de eficiência em licitação: metodologia, entregáveis e como transformá-lo em contratos recorrentes.',
    category: 'Consultorias de Licitação',
    tags: ['diagnóstico', 'serviço premium', 'metodologia', 'funil de vendas'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'diagnóstico de eficiência em licitação',
      'serviço premium consultoria',
      'como vender consultoria de licitação',
      'assessment licitação',
    ],
    relatedSlugs: [
      'identificar-clientes-gargalo-operacional-licitacoes',
      'usar-dados-provar-eficiencia-licitacoes',
      'triagem-editais-vantagem-estrategica-clientes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-14
  {
    slug: 'aumentar-taxa-sucesso-clientes-20-porcento',
    title: 'Como Aumentar a Taxa de Sucesso dos seus Clientes em até 20%',
    description:
      'Framework comprovado para consultorias aumentarem a taxa de adjudicação dos seus clientes B2G: da triagem inteligente à análise pós-pregão, em 5 etapas.',
    category: 'Consultorias de Licitação',
    tags: ['taxa de sucesso', 'framework', 'adjudicação', 'melhoria contínua'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'aumentar taxa de vitória clientes',
      'consultoria que dá resultado',
      'melhorar performance licitação',
      'taxa de adjudicação',
    ],
    relatedSlugs: [
      'aumentar-retencao-clientes-inteligencia-editais',
      'usar-dados-provar-eficiencia-licitacoes',
      'como-aumentar-taxa-vitoria-licitacoes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // CONS-15
  {
    slug: 'consultorias-dados-retem-mais-clientes-b2g',
    title: 'Por que Consultorias que Usam Dados Retêm mais Clientes B2G',
    description:
      'Consultorias data-driven retêm 3x mais clientes B2G do que as tradicionais. Veja os dados, o framework e como implementar uma cultura de dados na prática.',
    category: 'Consultorias de Licitação',
    tags: ['data-driven', 'retenção', 'relatórios', 'cultura de dados'],
    publishDate: '2026-02-24',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'consultoria data-driven',
      'retenção de clientes B2G',
      'dados em consultoria de licitação',
      'cultura de dados consultoria',
    ],
    relatedSlugs: [
      'aumentar-retencao-clientes-inteligencia-editais',
      'usar-dados-provar-eficiencia-licitacoes',
      'aumentar-taxa-sucesso-clientes-20-porcento',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // ──────────────────────────────────────────────
  // SEO Q2/2026: Guias Setoriais — 5 articles
  // ──────────────────────────────────────────────

  // GUIA-S1
  {
    slug: 'licitacoes-engenharia-2026',
    title: 'Licitações de Engenharia e Construção 2026 — Guia Completo',
    description:
      'Guia definitivo sobre licitações de engenharia e construção civil em 2026: modalidades, faixas de valor, UFs com maior volume, habilitação técnica e como analisar viabilidade.',
    category: 'Guias',
    tags: ['engenharia', 'construção civil', 'licitações 2026', 'guia setorial'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3400),
    wordCount: 3400,
    keywords: [
      'licitações engenharia',
      'licitações construção civil 2026',
      'edital de obra pública',
      'como participar licitação engenharia',
    ],
    relatedSlugs: [
      'licitacoes-ti-software-2026',
      'licitacoes-saude-2026',
      'como-participar-primeira-licitacao-2026',
      'analise-viabilidade-editais-guia',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'CONFEA/CREA — Conselho Federal de Engenharia e Agronomia',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // GUIA-S2
  {
    slug: 'licitacoes-ti-software-2026',
    title: 'Licitações de TI e Software 2026 — Guia Completo',
    description:
      'Tudo sobre licitações de tecnologia da informação e software em 2026: pregão eletrônico, atas de registro de preço, exigências técnicas e estratégias de participação.',
    category: 'Guias',
    tags: ['tecnologia', 'software', 'TI', 'licitações 2026', 'guia setorial'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3400),
    wordCount: 3400,
    keywords: [
      'licitações tecnologia',
      'licitações TI 2026',
      'pregão eletrônico software',
      'edital de tecnologia da informação',
    ],
    relatedSlugs: [
      'licitacoes-engenharia-2026',
      'licitacoes-saude-2026',
      'inteligencia-artificial-licitacoes-como-funciona',
      'analise-viabilidade-editais-guia',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'ComprasGov — Portal de Compras do Governo Federal',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // GUIA-S3
  {
    slug: 'licitacoes-saude-2026',
    title: 'Licitações de Saúde 2026 — Guia Completo',
    description:
      'Guia completo sobre licitações de saúde em 2026: medicamentos, equipamentos médicos, insumos hospitalares, registros na Anvisa e estratégias de participação.',
    category: 'Guias',
    tags: ['saúde', 'medicamentos', 'equipamentos médicos', 'licitações 2026', 'guia setorial'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3400),
    wordCount: 3400,
    keywords: [
      'licitações saúde',
      'licitações medicamentos 2026',
      'edital de equipamento médico',
      'como vender para hospitais públicos',
    ],
    relatedSlugs: [
      'licitacoes-engenharia-2026',
      'licitacoes-limpeza-facilities-2026',
      'como-participar-primeira-licitacao-2026',
      'lei-14133-guia-fornecedores',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Anvisa — Agência Nacional de Vigilância Sanitária',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // GUIA-S4
  {
    slug: 'licitacoes-limpeza-facilities-2026',
    title: 'Licitações de Limpeza e Facilities 2026 — Guia Completo',
    description:
      'Guia definitivo sobre licitações de limpeza, conservação e facilities management em 2026: planilha de custos, convenção coletiva, BDI e requisitos de habilitação.',
    category: 'Guias',
    tags: ['limpeza', 'facilities', 'serviços prediais', 'licitações 2026', 'guia setorial'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'licitações limpeza',
      'licitações facilities 2026',
      'edital de limpeza pública',
      'como ganhar licitação de limpeza',
    ],
    relatedSlugs: [
      'licitacoes-alimentacao-2026',
      'licitacoes-engenharia-2026',
      'analise-viabilidade-editais-guia',
      'lei-14133-guia-fornecedores',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // GUIA-S5
  {
    slug: 'licitacoes-alimentacao-2026',
    title: 'Licitações de Alimentação 2026 — Guia Completo',
    description:
      'Guia completo sobre licitações de alimentação em 2026: merenda escolar, refeições hospitalares, PNAE, atas de registro de preço e logística de distribuição.',
    category: 'Guias',
    tags: ['alimentação', 'merenda escolar', 'PNAE', 'licitações 2026', 'guia setorial'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'licitações alimentação',
      'licitações merenda escolar 2026',
      'edital de alimentação escolar',
      'PNAE fornecedores',
    ],
    relatedSlugs: [
      'licitacoes-limpeza-facilities-2026',
      'licitacoes-saude-2026',
      'como-participar-primeira-licitacao-2026',
      'pncp-guia-completo-empresas',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'FNDE — Fundo Nacional de Desenvolvimento da Educação (PNAE)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // ─────────────────────────────��────────────────
  // SEO Q2/2026: Guias Transversais — 5 articles
  // ──────────────────────────────────────────────

  // GUIA-T1
  {
    slug: 'como-participar-primeira-licitacao-2026',
    title: 'Como Participar da Primeira Licitação em 2026 — Guia Completo',
    description:
      'Passo a passo completo para participar da sua primeira licitação pública em 2026: cadastro, documentação, portais, pregão eletrônico e erros a evitar.',
    category: 'Guias',
    tags: ['primeira licitação', 'guia iniciante', 'passo a passo', 'cadastro'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3600),
    wordCount: 3600,
    keywords: [
      'como participar de licitações',
      'primeira licitação passo a passo',
      'como começar em licitações públicas',
      'guia iniciante licitações 2026',
    ],
    relatedSlugs: [
      'lei-14133-guia-fornecedores',
      'checklist-habilitacao-licitacao-2026',
      'pncp-guia-completo-empresas',
      'sicaf-como-cadastrar-manter-ativo-2026',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'ComprasGov — Portal de Compras do Governo Federal',
      'SICAF — Sistema de Cadastramento Unificado de Fornecedores',
    ],
  },

  // GUIA-T2
  {
    slug: 'lei-14133-guia-fornecedores',
    title: 'Lei 14.133/2021: O que Mudou para Fornecedores — Guia Prático',
    description:
      'Guia prático da Nova Lei de Licitações (14.133/2021) para fornecedores: novas modalidades, prazos, sanções, diálogo competitivo e o que muda na prática.',
    category: 'Guias',
    tags: ['Lei 14.133', 'nova lei de licitações', 'fornecedores', 'guia prático'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3600),
    wordCount: 3600,
    keywords: [
      'lei 14133 fornecedores',
      'nova lei de licitações 2026',
      'o que mudou na lei de licitações',
      'lei 14133 guia prático',
    ],
    relatedSlugs: [
      'como-participar-primeira-licitacao-2026',
      'checklist-habilitacao-licitacao-2026',
      'pncp-guia-completo-empresas',
      'clausulas-escondidas-editais-licitacao',
    ],
    sources: [
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Lei 8.666/1993 (revogada — transição)',
      'Decreto 10.024/2019 — Pregão Eletrônico',
    ],
  },

  // GUIA-T3
  {
    slug: 'pncp-guia-completo-empresas',
    title: 'Como Usar o PNCP em 2026: Guia Prático para Encontrar Editais por Setor e UF',
    description:
      'Aprenda a buscar editais no PNCP, filtrar por setor e UF, e entenda por que empresas B2G complementam o PNCP com monitoramento automatizado. Guia atualizado abril/2026.',
    category: 'Guias',
    tags: ['PNCP', 'portal de contratações', 'busca de editais', 'monitoramento'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3400),
    wordCount: 3400,
    keywords: [
      'pncp como usar',
      'portal nacional de contratações públicas',
      'como buscar editais no pncp',
      'pncp guia empresas',
    ],
    relatedSlugs: [
      'lei-14133-guia-fornecedores',
      'como-participar-primeira-licitacao-2026',
      'inteligencia-artificial-licitacoes-como-funciona',
      'licitacoes-ti-software-2026',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Decreto 10.764/2021 — Regulamenta o PNCP',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // GUIA-T4
  {
    slug: 'inteligencia-artificial-licitacoes-como-funciona',
    title: 'Inteligência Artificial em Licitações: Como Funciona na Prática',
    description:
      'Como a inteligência artificial está transformando a análise de editais: classificação automática, análise de viabilidade, e o futuro da participação em licitações.',
    category: 'Guias',
    tags: ['inteligência artificial', 'IA', 'automação', 'análise de editais'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'inteligência artificial licitações',
      'IA em licitações públicas',
      'automação de editais',
      'como IA analisa licitações',
    ],
    relatedSlugs: [
      'ia-triagem-editais-filtrar-licitacoes',
      'precisao-ia-licitacoes-taxa-acerto',
      'roi-ia-licitacoes-calculadora-retorno',
      'como-escolher-plataforma-ia-licitacoes',
      'ia-licitacoes-limitacoes-o-que-nao-faz',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // GUIA-T5
  {
    slug: 'analise-viabilidade-editais-guia',
    title: 'Análise de Viabilidade de Editais: O que Considerar antes de Participar',
    description:
      'Os 4 fatores objetivos para avaliar a viabilidade de um edital antes de investir recursos: modalidade, prazo, valor estimado e localização geográfica.',
    category: 'Guias',
    tags: ['viabilidade', 'análise de editais', 'go/no-go', 'decisão de participação'],
    publishDate: '2026-04-04',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'análise viabilidade editais',
      'como avaliar edital de licitação',
      'viabilidade de licitação',
      'critérios para participar de licitação',
    ],
    relatedSlugs: [
      'vale-a-pena-disputar-pregao',
      'como-participar-primeira-licitacao-2026',
      'licitacoes-engenharia-2026',
      'erros-desclassificam-propostas-licitacao',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'Dados agregados da plataforma SmartLic (2025-2026)',
    ],
  },

  // ──────────────────────────────────────────────
  // SEO-PLAYBOOK P7: Buyer-Intent Articles — 8 articles
  // ──────────────────────────────────────────────

  // P7-01
  {
    slug: 'checklist-habilitacao-licitacao-2026',
    title: 'Checklist Completo de Habilitação para Licitação em 2026 (Lei 14.133)',
    description:
      'Lista completa dos documentos de habilitação exigidos na Lei 14.133/2021: jurídica, fiscal, técnica, econômico-financeira e trabalhista — com prazos e armadilhas.',
    category: 'Guias',
    tags: ['habilitação', 'documentos', 'Lei 14.133', 'checklist', 'compliance'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3000),
    wordCount: 3000,
    keywords: [
      'checklist habilitação licitação',
      'documentos habilitação licitação 2026',
      'habilitação Lei 14.133',
      'documentos para participar de licitação',
    ],
    relatedSlugs: [
      'como-participar-primeira-licitacao-2026',
      'sicaf-como-cadastrar-manter-ativo-2026',
      'lei-14133-guia-fornecedores',
      'erros-desclassificam-propostas-licitacao',
    ],
    sources: [
      'Lei 14.133/2021, arts. 62 a 70 — Habilitação',
      'SICAF — Sistema de Cadastramento Unificado de Fornecedores',
      'TCU — Acórdãos sobre habilitação em licitações',
    ],
  },

  // P7-02
  {
    slug: 'pregao-eletronico-guia-passo-a-passo',
    title: 'Pregão Eletrônico: Guia Passo a Passo para Primeira Participação',
    description:
      'Do cadastro à disputa de lances: guia prático com os 10 passos para participar do primeiro pregão eletrônico em 2026 — tempos, portais e erros fatais.',
    category: 'Guias',
    tags: ['pregão eletrônico', 'passo a passo', 'ComprasNet', 'disputa de lances'],
    publishDate: '2026-04-09',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'pregão eletrônico como participar',
      'guia pregão eletrônico 2026',
      'passo a passo pregão eletrônico',
      'como dar lance em pregão',
    ],
    relatedSlugs: [
      'como-participar-primeira-licitacao-2026',
      'checklist-habilitacao-licitacao-2026',
      'erros-desclassificam-propostas-licitacao',
      'como-calcular-preco-proposta-licitacao',
    ],
    sources: [
      'Lei 14.133/2021, arts. 28 e 29 — Pregão',
      'Decreto 10.024/2019 — Pregão Eletrônico',
      'ComprasNet / ComprasGov — Portal de Compras do Governo Federal',
    ],
  },

  // P7-03
  {
    slug: 'como-calcular-preco-proposta-licitacao',
    title: 'Como Calcular o Preço de Proposta para Não Perder Dinheiro em Licitação',
    description:
      'Metodologia prática para calcular preço de proposta em licitações: BDI, planilha de custos, margem mínima e os 5 erros de precificação que eliminam propostas.',
    category: 'Guias',
    tags: ['precificação', 'proposta', 'BDI', 'custos', 'margem'],
    publishDate: '2026-04-11',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'como calcular preço licitação',
      'precificação proposta pregão',
      'BDI licitação',
      'planilha de custos licitação',
    ],
    relatedSlugs: [
      'pregao-eletronico-guia-passo-a-passo',
      'ata-registro-precos-estrategia-licitacao',
      'vale-a-pena-disputar-pregao',
      'ata-registro-precos-como-escolher',
    ],
    sources: [
      'Lei 14.133/2021, arts. 23 a 27 — Preço Estimado',
      'TCU — Acórdão 2.637/2015 sobre BDI',
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
    ],
  },

  // P7-04
  {
    slug: 'mei-microempresa-vantagens-licitacoes',
    title: 'MEI e Microempresa: Vantagens e Limites para Participar de Licitações',
    description:
      'Guia completo das vantagens legais de ME, EPP e MEI em licitações: empate ficto, exclusividade até R$80k, regularização tardia e limites práticos.',
    category: 'Guias',
    tags: ['MEI', 'microempresa', 'EPP', 'vantagens', 'LC 123'],
    publishDate: '2026-04-13',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'MEI licitação',
      'microempresa licitação vantagens',
      'EPP pode participar de licitação',
      'licitação exclusiva microempresa',
    ],
    relatedSlugs: [
      'como-participar-primeira-licitacao-2026',
      'checklist-habilitacao-licitacao-2026',
      'sicaf-como-cadastrar-manter-ativo-2026',
      'pregao-eletronico-guia-passo-a-passo',
    ],
    sources: [
      'Lei Complementar 123/2006, arts. 42 a 49 — Tratamento Diferenciado',
      'Lei 14.133/2021, art. 4º — ME/EPP',
      'Decreto 8.538/2015 — Tratamento Favorecido ME/EPP',
    ],
  },

  // P7-05
  {
    slug: 'sicaf-como-cadastrar-manter-ativo-2026',
    title: 'SICAF: Como se Cadastrar e Manter Ativo em 2026',
    description:
      'Passo a passo do cadastro no SICAF em 2026: níveis, documentos, prazos de validade, renovação e como resolver pendências que bloqueiam sua habilitação.',
    category: 'Guias',
    tags: ['SICAF', 'cadastro', 'renovação', 'habilitação', 'gov.br'],
    publishDate: '2026-04-15',
    readingTime: calculateReadingTime(2500),
    wordCount: 2500,
    keywords: [
      'SICAF cadastro',
      'como se cadastrar SICAF 2026',
      'SICAF renovação',
      'SICAF documentos necessários',
    ],
    relatedSlugs: [
      'checklist-habilitacao-licitacao-2026',
      'como-participar-primeira-licitacao-2026',
      'lei-14133-guia-fornecedores',
      'pncp-guia-completo-empresas',
    ],
    sources: [
      'SICAF — Sistema de Cadastramento Unificado de Fornecedores (sicaf.gov.br)',
      'Instrução Normativa SEGES/ME nº 3/2018',
      'Lei 14.133/2021, art. 87 — Registro Cadastral',
    ],
  },

  // P7-06
  {
    slug: 'erros-desclassificam-propostas-licitacao',
    title: 'Principais Erros que Desclassificam Propostas — e Como Evitá-los',
    description:
      'Os 12 erros mais frequentes que causam desclassificação em licitações: documentação, preço, prazo, assinatura digital e os que parecem bobos mas eliminam.',
    category: 'Guias',
    tags: ['desclassificação', 'erros em licitação', 'proposta', 'compliance'],
    publishDate: '2026-04-17',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'erros em licitação',
      'desclassificação proposta pregão',
      'motivos de inabilitação licitação',
      'erros comuns em pregão eletrônico',
    ],
    relatedSlugs: [
      'checklist-habilitacao-licitacao-2026',
      'pregao-eletronico-guia-passo-a-passo',
      'clausulas-escondidas-editais-licitacao',
      'impugnacao-edital-quando-como-contestar',
    ],
    sources: [
      'Lei 14.133/2021, arts. 59 e 60 — Julgamento de Propostas',
      'TCU — Jurisprudência sobre desclassificação em licitações',
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
    ],
  },

  // P7-07
  {
    slug: 'impugnacao-edital-quando-como-contestar',
    title: 'Impugnação de Edital: Quando e Como Contestar',
    description:
      'Guia prático de impugnação de editais: prazos legais, fundamentos válidos, modelo de petição, quando vale a pena contestar e quando é melhor não participar.',
    category: 'Guias',
    tags: ['impugnação', 'edital', 'recurso', 'contestação', 'prazos'],
    publishDate: '2026-04-19',
    readingTime: calculateReadingTime(2500),
    wordCount: 2500,
    keywords: [
      'impugnação edital licitação',
      'como impugnar edital',
      'prazo impugnação licitação',
      'modelo impugnação edital',
    ],
    relatedSlugs: [
      'lei-14133-guia-fornecedores',
      'clausulas-escondidas-editais-licitacao',
      'erros-desclassificam-propostas-licitacao',
      'analise-viabilidade-editais-guia',
    ],
    sources: [
      'Lei 14.133/2021, art. 164 — Impugnação',
      'Lei 14.133/2021, arts. 165 a 168 — Recursos',
      'TCU — Súmula 369 — Direcionamento em Editais',
    ],
  },

  // P7-08
  {
    slug: 'ata-registro-precos-estrategia-licitacao',
    title: 'Ata de Registro de Preços: Estratégia de Licitação sem Comprar',
    description:
      'Como usar o Sistema de Registro de Preços (SRP) como estratégia: vantagens para fornecedor, carona, vigência, riscos e quando é melhor que licitação convencional.',
    category: 'Guias',
    tags: ['ata de registro de preços', 'SRP', 'carona', 'estratégia', 'fornecedor'],
    publishDate: '2026-04-21',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'ata de registro de preços',
      'SRP licitação estratégia',
      'carona ata de registro',
      'registro de preços fornecedor',
    ],
    relatedSlugs: [
      'ata-registro-precos-como-escolher',
      'como-calcular-preco-proposta-licitacao',
      'pregao-eletronico-guia-passo-a-passo',
      'lei-14133-guia-fornecedores',
    ],
    sources: [
      'Lei 14.133/2021, arts. 82 a 86 — Sistema de Registro de Preços',
      'Decreto 11.462/2023 — Regulamenta o SRP',
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
    ],
  },

  // ──────────────────────────────────────────────
  // SEO Q2/2026: Onda 4 — Artigos BOFU (comparação)
  // ──────────────────────────────────────────────

  // BOFU-01
  {
    slug: 'smartlic-vs-planilha-excel-quando-automatizar',
    title: 'SmartLic vs Planilha Excel: Quando Automatizar Licitações Vale a Pena',
    description:
      'Comparação detalhada entre gerenciar licitações em planilha Excel e usar uma plataforma como o SmartLic. Números reais de tempo, custo e ROI para decidir quando automatizar.',
    category: 'Guias',
    tags: ['comparação', 'planilha excel', 'automação', 'ROI', 'SmartLic'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3000),
    wordCount: 3000,
    keywords: [
      'smartlic vs planilha excel',
      'automatizar licitações',
      'plataforma de licitação vs excel',
      'quando automatizar licitações',
      'gestão de editais excel',
    ],
    relatedSlugs: [
      'como-aumentar-taxa-vitoria-licitacoes',
      'reduzir-tempo-analisando-editais-irrelevantes',
      'analise-viabilidade-editais-guia',
      'melhores-plataformas-licitacao-2026-ranking',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021, art. 55 — prazos mínimos por modalidade',
      'SmartLic datalake — dados de processamento jan-mar 2026',
    ],
    authorSlug: 'tiago',
  },

  // BOFU-02
  {
    slug: 'melhores-plataformas-licitacao-2026-ranking',
    title: 'Melhores Plataformas de Licitação 2026: Ranking Completo e Honesto',
    description:
      'Ranking das principais plataformas de licitação em 2026: SmartLic, Effecti, Licitanet, LicitaWeb e PCP. Comparação por IA, cobertura, preço e fase do processo atendida.',
    category: 'Guias',
    tags: ['ranking', 'plataformas de licitação', 'comparação', '2026', 'SmartLic'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3100),
    wordCount: 3100,
    keywords: [
      'melhores plataformas de licitação',
      'ranking plataformas licitação 2026',
      'comparar plataformas de licitação',
      'effecti vs smartlic vs licitanet',
      'ferramenta para licitação',
    ],
    relatedSlugs: [
      'smartlic-vs-planilha-excel-quando-automatizar',
      'smartlic-vs-effecti-comparacao-2026',
      'inteligencia-artificial-licitacoes-como-funciona',
      'pncp-guia-completo-empresas',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações',
      'Sites oficiais das plataformas — preços abril/2026',
      'SmartLic datalake — 800K+ publicações analisadas',
    ],
    authorSlug: 'tiago',
  },

  // BOFU-03
  {
    slug: 'smartlic-vs-effecti-comparacao-2026',
    title: 'SmartLic vs Effecti: Comparação Completa 2026 — Qual Escolher',
    description:
      'Comparação detalhada entre SmartLic e Effecti: IA vs automação documental, preço, cobertura, pontos fortes e fracos de cada plataforma. Veredito honesto por perfil de empresa.',
    category: 'Guias',
    tags: ['comparação', 'Effecti', 'SmartLic', 'plataformas de licitação', '2026'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3100),
    wordCount: 3100,
    keywords: [
      'smartlic vs effecti',
      'effecti ou smartlic',
      'comparar plataformas licitação',
      'effecti preço funcionalidades',
      'melhor plataforma licitação 2026',
    ],
    relatedSlugs: [
      'melhores-plataformas-licitacao-2026-ranking',
      'smartlic-vs-planilha-excel-quando-automatizar',
      'como-aumentar-taxa-vitoria-licitacoes',
      'triagem-editais-vantagem-estrategica-clientes',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações',
      'SmartLic datalake — classificação e triagem jan-mar 2026',
      'Effecti — site oficial, funcionalidades e preços abril/2026',
    ],
    authorSlug: 'tiago',
  },

  // BOFU-04
  {
    slug: 'smartlic-vs-licitanet-comparacao',
    title: 'SmartLic vs Licitanet: Qual Plataforma Escolher em 2026',
    description:
      'Comparação entre SmartLic e Licitanet: inteligência na triagem de editais vs plataforma de pregão eletrônico. Entenda o que cada uma faz, onde cada uma é superior e quando usar ambas.',
    category: 'Guias',
    tags: ['comparação', 'Licitanet', 'SmartLic', 'pregão eletrônico', '2026'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3000),
    wordCount: 3000,
    keywords: [
      'smartlic vs licitanet',
      'licitanet ou smartlic',
      'plataforma pregão eletrônico',
      'licitanet plataforma licitação',
      'comparar smartlic licitanet',
    ],
    relatedSlugs: [
      'melhores-plataformas-licitacao-2026-ranking',
      'smartlic-vs-effecti-comparacao-2026',
      'smartlic-vs-planilha-excel-quando-automatizar',
      'pregao-eletronico-guia-passo-a-passo',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações',
      'SmartLic datalake — classificação e triagem jan-mar 2026',
      'Licitanet — funcionalidades conforme site oficial, abril/2026',
    ],
    authorSlug: 'tiago',
  },

  // ── Cluster "IA em Licitações" — 8 spokes (Onda 4) ──

  // CLUSTER-IA-01
  {
    slug: 'roi-ia-licitacoes-calculadora-retorno',
    title: 'ROI de IA em Licitações: Quanto sua Empresa Economiza com Triagem Automatizada',
    description:
      'Cálculo detalhado do retorno sobre investimento de ferramentas de IA para licitações. 3 perfis de empresa, custos reais e dados do PNCP.',
    category: 'Empresas B2G',
    tags: ['ROI', 'inteligência artificial', 'economia', 'triagem automatizada'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3000),
    wordCount: 3000,
    keywords: [
      'ROI inteligência artificial licitações',
      'retorno investimento plataforma licitação',
      'quanto custa IA para licitação',
      'vale a pena pagar ferramenta licitação',
    ],
    relatedSlugs: [
      'inteligencia-artificial-licitacoes-como-funciona',
      'ia-triagem-editais-filtrar-licitacoes',
      'ia-licitacoes-limitacoes-o-que-nao-faz',
      'vale-a-pena-disputar-pregao',
      'smartlic-vs-planilha-excel-quando-automatizar',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'SmartLic datalake — dados de classificação e triagem, jan-mar 2026',
    ],
    authorSlug: 'tiago',
  },

  // CLUSTER-IA-02
  {
    slug: 'como-escolher-plataforma-ia-licitacoes',
    title: 'Como Escolher uma Plataforma de IA para Licitações: 7 Critérios Objetivos',
    description:
      'Framework de avaliação com 7 critérios objetivos para comparar plataformas de IA para licitações. Tabela comparativa e perguntas para o vendedor.',
    category: 'Guias',
    tags: ['plataforma de licitação', 'IA', 'comparação', 'critérios de avaliação'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'como escolher plataforma licitação com IA',
      'comparar ferramentas licitação IA',
      'critérios plataforma licitação',
      'o que avaliar ferramenta licitação',
    ],
    relatedSlugs: [
      'inteligencia-artificial-licitacoes-como-funciona',
      'precisao-ia-licitacoes-taxa-acerto',
      'melhores-plataformas-licitacao-2026-ranking',
      'smartlic-vs-effecti-comparacao-2026',
      'smartlic-vs-licitanet-comparacao',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações',
      'Sites oficiais das plataformas — preços e funcionalidades abril/2026',
      'SmartLic datalake — métricas de freshness e cobertura',
    ],
    authorSlug: 'tiago',
  },

  // CLUSTER-IA-03
  {
    slug: 'ia-licitacoes-limitacoes-o-que-nao-faz',
    title: 'O que IA NÃO Faz em Licitações: 5 Limitações que Ninguém Conta',
    description:
      'Transparência radical: 5 coisas que a inteligência artificial não consegue fazer em licitações públicas — e por que entender isso é uma vantagem competitiva.',
    category: 'Guias',
    tags: ['limitações IA', 'licitações', 'transparência', 'análise crítica'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(2800),
    wordCount: 2800,
    keywords: [
      'limitações IA licitações',
      'IA não substitui analista licitação',
      'problemas IA editais',
      'IA licitações funciona mesmo',
    ],
    relatedSlugs: [
      'inteligencia-artificial-licitacoes-como-funciona',
      'precisao-ia-licitacoes-taxa-acerto',
      'roi-ia-licitacoes-calculadora-retorno',
      'inteligencia-artificial-consultoria-licitacao-2026',
      'clausulas-escondidas-editais-licitacao',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'SmartLic datalake — dados de classificação e revisão humana, jan-mar 2026',
    ],
    authorSlug: 'tiago',
  },

  // CLUSTER-IA-04
  {
    slug: 'ia-triagem-editais-filtrar-licitacoes',
    title: 'IA para Triagem de Editais: Como Filtrar 500 Licitações por Dia sem Analista',
    description:
      'Como a inteligência artificial transforma 3.200 publicações diárias do PNCP em 15 editais relevantes. Pipeline de triagem em 3 camadas com dados reais.',
    category: 'Empresas B2G',
    tags: ['triagem de editais', 'IA', 'filtro automático', 'produtividade'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3000),
    wordCount: 3000,
    keywords: [
      'triagem de editais com IA',
      'filtrar licitações automaticamente',
      'automação triagem editais',
      'IA classificação editais',
    ],
    relatedSlugs: [
      'inteligencia-artificial-licitacoes-como-funciona',
      'precisao-ia-licitacoes-taxa-acerto',
      'ia-licitacoes-por-setor-saude-ti-engenharia',
      'reduzir-tempo-analisando-editais-irrelevantes',
      'equipe-40-horas-mes-editais-descartados',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'SmartLic datalake — pipeline de triagem, jan-mar 2026 (800K+ publicações)',
    ],
    authorSlug: 'tiago',
  },

  // CLUSTER-IA-05
  {
    slug: 'precisao-ia-licitacoes-taxa-acerto',
    title: 'Precisão da IA em Licitações: O que 85-93% de Acerto Significa na Prática',
    description:
      'Dados reais de acurácia por setor na classificação de editais por IA. Tabela com 15 setores, tipos de erro e o custo de cada um.',
    category: 'Guias',
    tags: ['precisão IA', 'acurácia', 'classificação setorial', 'taxa de acerto'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3000),
    wordCount: 3000,
    keywords: [
      'precisão IA licitações',
      'taxa de acerto IA editais',
      'IA classificação setorial precisão',
      'erro IA licitação',
    ],
    relatedSlugs: [
      'inteligencia-artificial-licitacoes-como-funciona',
      'ia-licitacoes-por-setor-saude-ti-engenharia',
      'roi-ia-licitacoes-calculadora-retorno',
      'ia-licitacoes-limitacoes-o-que-nao-faz',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'SmartLic datalake — métricas de classificação por setor, jan-mar 2026',
    ],
    authorSlug: 'tiago',
  },

  // CLUSTER-IA-06
  {
    slug: 'ia-licitacoes-por-setor-saude-ti-engenharia',
    title: 'IA em Licitações por Setor: Saúde, TI, Engenharia e Facilities',
    description:
      'Análise detalhada de como a IA classifica editais em 4 setores-chave: volume, valor médio, precisão de classificação e desafios específicos de cada setor.',
    category: 'Guias',
    tags: ['IA por setor', 'licitações saúde', 'licitações TI', 'engenharia', 'facilities'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3200),
    wordCount: 3200,
    keywords: [
      'IA licitações saúde TI engenharia',
      'inteligência artificial licitações saúde',
      'IA editais TI',
      'licitações engenharia ferramenta IA',
    ],
    relatedSlugs: [
      'inteligencia-artificial-licitacoes-como-funciona',
      'ia-triagem-editais-filtrar-licitacoes',
      'precisao-ia-licitacoes-taxa-acerto',
      'licitacoes-saude-2026',
      'licitacoes-ti-software-2026',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei 14.133/2021 — Nova Lei de Licitações',
      'SmartLic datalake — classificação por setor, jan-mar 2026',
    ],
    authorSlug: 'tiago',
  },

  // CLUSTER-IA-07
  {
    slug: 'ia-licitacoes-pequenas-empresas-mei-epp',
    title: 'IA em Licitações para Pequenas Empresas: Guia para Quem Fatura até R$4,8M',
    description:
      'Como microempresas e EPPs podem usar inteligência artificial para competir em licitações. Vantagens da LC 123 potencializadas por IA, ROI e workflow prático.',
    category: 'Empresas B2G',
    tags: ['pequenas empresas', 'MEI', 'EPP', 'IA em licitações', 'LC 123'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3000),
    wordCount: 3000,
    keywords: [
      'IA licitações pequenas empresas',
      'ferramenta licitação MEI',
      'plataforma licitação microempresa',
      'EPP licitação automatizar',
    ],
    relatedSlugs: [
      'inteligencia-artificial-licitacoes-como-funciona',
      'roi-ia-licitacoes-calculadora-retorno',
      'ia-nova-lei-licitacoes-14133-fornecedores',
      'mei-microempresa-vantagens-licitacoes',
      'como-participar-primeira-licitacao-2026',
    ],
    sources: [
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Lei Complementar 123/2006 — Estatuto da Microempresa e EPP',
      'Lei 14.133/2021 — Nova Lei de Licitações',
      'SmartLic datalake — editais com preferência ME/EPP, jan-mar 2026',
    ],
    authorSlug: 'tiago',
  },

  // CLUSTER-IA-08
  {
    slug: 'ia-nova-lei-licitacoes-14133-fornecedores',
    title: 'IA e a Nova Lei de Licitações (14.133): O que Muda para Fornecedores em 2026',
    description:
      'Como a Lei 14.133/2021 criou uma sobrecarga de informação que só a IA resolve. Análise artigo por artigo das mudanças e como ferramentas inteligentes se adaptam.',
    category: 'Guias',
    tags: ['Lei 14.133', 'nova lei licitações', 'IA', 'PNCP', 'fornecedores'],
    publishDate: '2026-04-07',
    readingTime: calculateReadingTime(3000),
    wordCount: 3000,
    keywords: [
      'IA nova lei licitações 14133',
      'lei 14133 tecnologia fornecedores',
      'PNCP inteligência artificial',
      'automação lei licitações 2026',
    ],
    relatedSlugs: [
      'inteligencia-artificial-licitacoes-como-funciona',
      'ia-licitacoes-pequenas-empresas-mei-epp',
      'ia-licitacoes-limitacoes-o-que-nao-faz',
      'lei-14133-guia-fornecedores',
      'pncp-guia-completo-empresas',
    ],
    sources: [
      'Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos',
      'PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)',
      'Decreto 10.764/2021 — Regulamenta o PNCP',
      'SmartLic datalake — volume de publicações PNCP, 2024-2026',
    ],
    authorSlug: 'tiago',
  },
];

export function getArticleBySlug(slug: string): BlogArticleMeta | undefined {
  return BLOG_ARTICLES.find((article) => article.slug === slug);
}

export function getArticlesByCategory(category: string): BlogArticleMeta[] {
  return BLOG_ARTICLES.filter((article) => article.category === category);
}

export function getRelatedArticles(slug: string): BlogArticleMeta[] {
  const article = getArticleBySlug(slug);
  if (!article) return [];
  return article.relatedSlugs
    .map((relSlug) => getArticleBySlug(relSlug))
    .filter((a): a is BlogArticleMeta => a !== undefined);
}

export function getAllSlugs(): string[] {
  return BLOG_ARTICLES.map((article) => article.slug);
}

/**
 * S7+S11: Get articles by author slug.
 * Articles without explicit authorSlug default to 'tiago-sasaki'.
 */
export function getArticlesByAuthor(authorSlug: string): BlogArticleMeta[] {
  return BLOG_ARTICLES.filter(
    (a) => (a.authorSlug || 'tiago-sasaki') === authorSlug
  );
}
