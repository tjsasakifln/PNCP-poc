/**
 * SmartLic Value Proposition Copy Library
 *
 * GTM-001: Complete rewrite — Decision Intelligence positioning
 * GTM-007: PNCP sanitization — Zero user-visible PNCP mentions
 *
 * Guiding principle: "We sell decision intelligence, not search speed"
 *
 * @date 2026-02-15
 */

import { Target, Globe, Bot, Search, ShieldCheck } from '@/lib/icons';

// ============================================================================
// HERO SECTION (Landing Page)
// ============================================================================

export const hero = {
  // GTM-COPY-001: Financial impact positioning
  headlines: {
    financialImpact: "Pare de perder dinheiro com licitações erradas.",
    filterFocus: "Só o que vale a pena chega até você.",
    wasteCut: "Licitações que realmente pagam. O resto, a gente descarta.",
    // Recommended for GTM-COPY-001
    default: "Pare de perder dinheiro com licitações erradas.",
  },

  // GTM-COPY-001 AC2: Mechanism of value (not abstract)
  subheadlines: {
    mechanism: "O SmartLic analisa cada edital contra o perfil da sua empresa. Elimina o que não faz sentido. Entrega só o que tem chance real de retorno — com justificativa objetiva.",
    filter: "Cada edital passa por análise de compatibilidade com seu perfil. Você só vê o que merece investimento de tempo e proposta.",
    default: "O SmartLic analisa cada edital contra o perfil da sua empresa. Elimina o que não faz sentido. Entrega só o que tem chance real de retorno — com justificativa objetiva.",
  },

  // GTM-COPY-001 AC3: Trust badges — practical confidence, not abstract metrics
  trustBadges: [
    {
      icon: Target,
      text: "87% descartados",
      detail: "Editais eliminados por irrelevância ao seu perfil",
    },
    {
      icon: Search,
      text: "15 setores",
      detail: "Filtragem especializada por mercado",
    },
    {
      icon: Globe,
      text: "27 UFs cobertas",
      detail: "Cobertura nacional de fontes oficiais",
    },
  ],

  // GTM-COPY-002: Action-oriented CTAs
  cta: {
    primary: "Ver oportunidades para meu setor",
    secondary: "Ver exemplo de análise real",
    pricing: "Começar a filtrar oportunidades",
    default: "Ver oportunidades para meu setor",
  },
};

// ============================================================================
// VALUE PROPOSITIONS (4 Key Differentiators — Decision Intelligence)
// ============================================================================

// GTM-COPY-001 AC4: Consequence-focused value props
export const valueProps = {
  prioritization: {
    title: "Foque só no que paga",
    shortDescription: "O sistema cruza cada edital com o perfil da sua empresa e descarta o que não se encaixa",
    longDescription:
      "Você para de gastar horas avaliando editais incompatíveis. O SmartLic aplica mais de 1.000 regras por setor para separar o que tem potencial real de retorno do que é ruído. Sobra só o que vale sua proposta.",
    icon: Target,
    metric: "Foco",
    proof: "87% dos editais descartados antes de chegar até você",
  },

  analysis: {
    title: "Descarte sem ler 100 páginas",
    shortDescription: "IA avalia setor, valor, prazo e requisitos — e diz se vale a pena ou não",
    longDescription:
      "Cada edital recebe avaliação objetiva com justificativa: compatibilidade com seu perfil, faixa de valor, prazo viável, região de atuação. Você decide em segundos, não em horas.",
    icon: Bot,
    metric: "Objetiva",
    proof: "Avaliação automatizada com 4 critérios de viabilidade",
  },

  uncertainty: {
    title: "Saiba por que cada edital foi selecionado",
    shortDescription: "Cada oportunidade vem com critérios objetivos — não com palpite",
    longDescription:
      "Nada de confiar em intuição. Toda recomendação mostra exatamente por que aquele edital é compatível com sua empresa: setor, valor, prazo e região. Decida com dados, não com achismo.",
    icon: ShieldCheck,
    metric: "Transparente",
    proof: "Justificativa objetiva para cada recomendação",
  },

  coverage: {
    title: "Nenhuma oportunidade invisível",
    shortDescription: "Fontes oficiais de 27 estados consolidadas automaticamente",
    longDescription:
      "Se um edital compatível com seu perfil é publicado em qualquer estado do Brasil, você sabe. Cobertura nacional de fontes oficiais sem precisar monitorar dezenas de portais manualmente.",
    icon: Globe,
    metric: "27 UFs",
    proof: "Consolidação automática de fontes oficiais de todas as esferas",
  },
};

// ============================================================================
// TRUST CRITERIA (GTM-COPY-004: Decision Safety Elements)
// ============================================================================

export const trustCriteria = {
  sectionBadge: 'Transparência de critérios',
  headline: 'Cada recomendação tem uma justificativa',
  subheadline:
    'Você sabe exatamente por que cada oportunidade foi selecionada — e por que as outras foram descartadas. Sem caixa preta, sem palpite.',
  criteria: [
    'Compatibilidade setorial',
    'Faixa de valor adequada',
    'Prazo viável para preparação',
    'Região de atuação',
    'Modalidade favorável',
  ],
  adherenceLevels: {
    alta: '3 ou mais critérios atendem seu perfil — oportunidade prioritária',
    media: '2 critérios atendem — vale avaliar com atenção',
    baixa: '1 critério ou menos — considere apenas se estratégico',
  },
  falsePositiveReduction:
    'Você recebe 20 recomendações qualificadas, não 2.000 resultados genéricos',
  falseNegativeReduction:
    'Se existe algo compatível em qualquer lugar do Brasil, você sabe',
  trustIndicators: [
    'Fontes oficiais verificadas',
    'Critérios objetivos, não opinião',
    'Cancelamento em 1 clique',
    'Sem dados fabricados',
  ],
};

// ============================================================================
// FEATURES PAGE COPY
// ============================================================================

export const features = {
  // GTM-009: Transformation narratives — "Sem SmartLic" → "Com SmartLic"
  prioritization: {
    title: "Foco no Que Realmente Importa",
    without:
      "Você gasta tempo lendo editais incompatíveis com seu perfil, perde oportunidades boas por não saber que existem.",
    withSmartLic:
      "O sistema avalia cada oportunidade com base no seu perfil (porte, região, ticket médio) e indica quais merecem sua atenção. Você para de desperdiçar tempo com licitações ruins e foca nas que pode ganhar.",
    gemAccent: "sapphire" as const,
  },

  adequacy: {
    title: "Você Decide Sem Ler 100 Páginas de Edital",
    without:
      "Você baixa edital de 120 páginas, lê por 40 minutos, descobre que requisitos são incompatíveis. Tempo perdido.",
    withSmartLic:
      "Não precisa ler editais para decidir se vale a pena. O SmartLic avalia requisitos, prazos e valores contra seu perfil e diz: \"Vale a pena\" ou \"Pule esta\". Você decide em segundos com base em critérios objetivos.",
    gemAccent: "emerald" as const,
  },

  nationalCoverage: {
    title: "Você Nunca Perde uma Oportunidade Por Não Saber Que Ela Existe",
    without:
      "Você consulta 3-4 fontes manualmente. Oportunidades em portais estaduais passam despercebidas. Seu concorrente descobre antes.",
    withSmartLic:
      "Cobertura nacional via fontes oficiais consolidadas. Se uma licitação compatível com seu perfil é publicada em qualquer lugar do Brasil, você sabe.",
    gemAccent: "emerald" as const,
  },

  decisionIntelligence: {
    title: "Decisões Melhores, Não Apenas Mais Rápidas",
    without:
      "Você encontra licitações, mas não sabe quais priorizar. Entra em todas e se dispersa. Taxa de sucesso baixa.",
    withSmartLic:
      "Avalie uma oportunidade em segundos com base em critérios objetivos (adequação, competitividade, requisitos). Não é sobre ser rápido — é sobre decidir melhor. Você investe tempo onde tem chance real de ganhar.",
    gemAccent: "sapphire" as const,
  },

  competitiveAdvantage: {
    title: "Seu Concorrente Ainda Está Procurando. Você Já Está Se Posicionando.",
    without:
      "Você descobre oportunidades dias depois da publicação. Concorrentes já estão preparando propostas. Você entra atrasado.",
    withSmartLic:
      "Acesso sob demanda às bases oficiais com busca inteligente por setor. Você descobre antes consultando diretamente as fontes, se posiciona antes, compete melhor. Quem vê primeiro tem vantagem.",
    gemAccent: "ruby" as const,
  },
};

// ============================================================================
// PRICING PAGE COPY
// ============================================================================

export const pricing = {
  headline: "Invista em Visibilidade, Colha em Contratos",
  subheadline:
    "O custo de perder uma licitação por falta de visibilidade é muito maior que o investimento em inteligência de mercado.",

  // ROI messaging
  roi: {
    headline: "Quanto Custa Não Ter Visibilidade?",
    calculator: {
      defaultContractValue: 200_000,
      defaultWinRate: 0.05,
      exampleCalculation: {
        missedOpportunityCost: 200_000,
        smartLicInvestment: 397,
        potentialReturn: "500x",
      },
    },
    tagline: "Uma única licitação ganha paga o investimento do ano inteiro.",
  },

  // Pricing comparison table
  comparison: {
    pricingModel: {
      traditional: "Por consulta ou mensalidade + extras ocultos",
      smartlic: "Investimento fixo mensal, sem surpresas",
    },
    hiddenFees: {
      traditional: "Comuns (visitas, suporte premium, extras)",
      smartlic: "Nenhuma (tudo incluso)",
    },
    cancellation: {
      traditional: "Burocrático (ligações, retenção)",
      smartlic: "1 clique (sem retenção)",
    },
    guarantee: {
      traditional: "Raro",
      smartlic: "14 dias do produto completo",
    },
  },

  // Guarantee messaging
  guarantee: {
    headline: "Avalie Sem Compromisso",
    description:
      "Produto completo por 14 dias para você conhecer o poder da inteligência de decisão. Sem cartão, sem compromisso.",
  },

  // Transparency statement
  transparency:
    "Investimento transparente. Sem pegadinhas, sem letras pequenas. Cancele quando quiser em 1 clique.",

  // GTM-COPY-002: Action-oriented CTA
  cta: "Começar a filtrar oportunidades",
};

// ============================================================================
// SEARCH PAGE COPY (app/buscar/page.tsx)
// ============================================================================

export const searchPage = {
  // Sector selector placeholder
  sectorPlaceholder: "Ex: Uniformes, TI, Engenharia, Facilities...",

  // Loading state messages
  loadingStates: {
    initial: "Consultando fontes oficiais e aplicando inteligência de decisão...",
    progress: [
      "Consultando fontes oficiais...",
      "Aplicando filtros inteligentes...",
      "Avaliando oportunidades...",
      "Priorizando resultados...",
      "Resultados prontos!",
    ],
  },

  // Empty state (no results found)
  emptyState: {
    title: "Nenhuma Oportunidade Relevante Encontrada",
    description:
      "Nossos filtros avaliaram {count} resultados e nenhum se adequa ao seu perfil atual. Tente ajustar os filtros ou escolher outro setor.",
    suggestion: "Dica: Amplie o intervalo de datas ou selecione mais UFs.",
  },

  // Tooltip on filter icon
  filterTooltip:
    "Filtramos por valor mínimo (R$ 50k) para focar em oportunidades com retorno significativo.",

  // Success state (results found)
  successState: {
    title: "{count} Oportunidades Relevantes Encontradas",
    subtitle:
      "Avaliadas e priorizadas de {total} licitações. Apenas o que merece sua atenção.",
  },
};

// ============================================================================
// ONBOARDING/TUTORIAL COPY
// ============================================================================

export const onboarding = {
  steps: [
    {
      title: "Defina Seu Mercado",
      description:
        "Selecione seu setor de atuação e região. O sistema entende seu perfil e encontra oportunidades específicas para você.",
      icon: Search,
    },
    {
      title: "Receba Oportunidades Priorizadas",
      description:
        "Inteligência avalia cada oportunidade e indica o que merece sua atenção. Foco no que gera resultado.",
      icon: Target,
    },
    {
      title: "Avaliação Objetiva por IA",
      description:
        "Cada oportunidade vem com avaliação objetiva: vale a pena ou não, e por quê. Decisão informada.",
      icon: Bot,
    },
    {
      title: "Posicione-se Antes",
      description:
        "Visibilidade completa do mercado. Quem vê primeiro, se posiciona primeiro e vence mais.",
      icon: Globe,
    },
  ],

  finalCta: "Ver oportunidades para meu setor",
};

// ============================================================================
// FOOTER TRANSPARENCY DISCLAIMER
// ============================================================================

export const footer = {
  dataSource: "Dados consolidados de fontes oficiais de contratações públicas",
  disclaimer:
    "SmartLic não é afiliado ao governo. Somos uma plataforma de inteligência de decisão para licitações.",
  trustBadge: "Inteligência proprietária de avaliação e priorização",
};

// ============================================================================
// EMAIL MARKETING COPY
// ============================================================================

export const email = {
  opportunityAlert: {
    subjectLine: "{count} novas oportunidades avaliadas para {sector}",
    preheader: "Priorizadas por relevância para o seu perfil.",
    body: {
      greeting: "Olá {userName},",
      intro:
        "Avaliamos {total} licitações e identificamos {count} oportunidades relevantes para {sector}:",
      cta: "Ver Oportunidades Priorizadas",
      footer:
        "Você está recebendo este email porque ativou alertas para {sector}. Ajuste suas preferências a qualquer momento.",
    },
  },

  weeklyDigest: {
    subjectLine: "Suas oportunidades da semana — {count} priorizadas",
    preheader: "{count} oportunidades avaliadas + insights semanais",
    body: {
      intro:
        "Esta semana, avaliamos {total} licitações e priorizamos {count} oportunidades relevantes para o seu perfil.",
      cta: "Ver Oportunidades da Semana",
    },
  },
};

// ============================================================================
// ANALYSIS EXAMPLES — Real Social Proof (GTM-005)
// ============================================================================

export const analysisExamples = {
  sectionTitle: "SmartLic em Ação",
  sectionSubtitle:
    "Veja como analisamos oportunidades reais e sugerimos decisões objetivas",
  flow: ["Licitação Real", "Análise SmartLic", "Decisão Sugerida"],
  labels: {
    timeline: "Prazo",
    requirements: "Requisitos",
    competitiveness: "Concorrência",
    score: "Compatibilidade",
    decision: "Decisão Sugerida",
  },
};

// ============================================================================
// BANNED PHRASES (DO NOT USE — GTM-001 AC9-AC11)
// ============================================================================

export const BANNED_PHRASES = [
  // Speed/efficiency metrics (commodity positioning)
  "160x",
  "160x mais rápido",
  "95%",
  "95% de precisão",
  "3 minutos",
  "em 3 minutos",
  "8 horas",
  "8+ horas",
  "economize tempo",
  "save time",
  "economize 10h",
  "10h/semana",
  "10 horas por semana",
  // PNCP references (GTM-007)
  "PNCP",
  "Portal Nacional de Contratações",
  "Dados do PNCP",
  "Resultados do PNCP",
  "Simplificamos o PNCP",
  "Consulta ao Portal Nacional",
  "PNCP + 27",
  // Source counting/enumeration (GTM-RESILIENCE-C01)
  "2 fontes",
  "duas fontes",
  "2 bases",
  "duas bases",
  "3 fontes",
  "três fontes",
  "Portal de Compras Públicas",
  "Portal Nacional de Contratações Públicas",
  // Generic/commodity positioning
  "Agregador de dados",
  "Portal governamental",
  "Busque por termos",
  "Acesse licitações públicas",
  // Fictional personas
  "João Silva",
  "Maria Santos",
  "Carlos Oliveira",
  "Ana Costa",
  // AI as commodity / summary language (GTM-008)
  "resumo",
  "resumo executivo",
  "resumos",
  "resumir",
  "sintetizar",
  "GPT-4",
  "3 linhas",
  "reduzir texto",
  // GTM-COPY-001: Abstract/commodity positioning
  "inteligência automatizada",
  "inovador",
  // GTM-COPY-002: Exploratory CTA verbs
  "descobrir",
  "explorar",
  "experimentar",
  // STORY-352: Human support 24/7 is not realistic for pre-revenue team
  "Suporte 24/7",
  // STORY-350: Unverifiable coverage claims
  "+98%",
  "+98% cobertura",
  "+98% das oportunidades",
];

// ============================================================================
// PREFERRED PHRASES (ALWAYS USE — GTM-001 AC12-AC13)
// ============================================================================

export const PREFERRED_PHRASES = {
  primaryValue: "Filtro estratégico para licitações",
  decision: ["avaliação objetiva", "vale a pena ou não", "justificativa objetiva"],
  competitive: ["filtro estratégico", "foco no retorno", "elimina ruído"],
  intelligence: ["análise de compatibilidade", "critérios de viabilidade", "perfil da empresa"],
  coverage: ["fontes oficiais", "cobertura nacional", "27 UFs"],
  uncertainty: ["critérios objetivos", "justificativa para cada recomendação", "dados, não achismo"],
  cost: ["perder dinheiro com licitações erradas", "risco operacional", "operar no escuro"],
  trust: "Cancele em 1 clique, sem burocracia",
  // GTM-COPY-001: Impact-focused vocabulary
  impact: [
    "elimina o que não faz sentido",
    "chance real de retorno",
    "descarta por irrelevância",
    "protege seu tempo",
    "foco no que paga",
  ],
  // GTM-COPY-002: Action verbs for CTAs
  actionVerbs: ["ver", "filtrar", "analisar", "começar"],
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get hero copy with optional variant selection
 */
export function getHeroCopy(variant: keyof typeof hero.headlines = "default") {
  return {
    headline: hero.headlines[variant],
    subheadline: hero.subheadlines.default,
    trustBadges: hero.trustBadges,
    cta: hero.cta.default,
  };
}

/**
 * Get value prop by key
 */
export function getValueProp(key: keyof typeof valueProps) {
  return valueProps[key];
}

/**
 * Get feature copy by key
 */
export function getFeature(key: keyof typeof features) {
  return features[key];
}

/**
 * Validate that copy doesn't contain banned phrases
 */
export function validateCopy(text: string): { isValid: boolean; violations: string[] } {
  const violations = BANNED_PHRASES.filter((phrase) =>
    text.toLowerCase().includes(phrase.toLowerCase())
  );

  return {
    isValid: violations.length === 0,
    violations,
  };
}

/**
 * Format number with metric suffix
 */
export function formatMetric(value: number, suffix: string): string {
  return `${value}${suffix}`;
}

// ============================================================================
// EXPORT ALL
// ============================================================================

export default {
  hero,
  valueProps,
  trustCriteria,
  features,
  pricing,
  searchPage,
  onboarding,
  footer,
  email,
  analysisExamples,
  BANNED_PHRASES,
  PREFERRED_PHRASES,
  // Utility functions
  getHeroCopy,
  getValueProp,
  getFeature,
  validateCopy,
  formatMetric,
};
