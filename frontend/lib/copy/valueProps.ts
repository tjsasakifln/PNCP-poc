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
  // Primary headline variants (A/B test candidates)
  headlines: {
    decisionFocus: "Saiba Onde Investir para Ganhar Mais Licitações",
    competitiveFocus: "Seus Concorrentes Já Estão Se Posicionando. E Você?",
    intelligenceFocus: "Inteligência de Decisão para Quem Compete em Licitações",
    visibilityFocus: "Visibilidade Total do Mercado de Licitações",
    // Recommended for initial launch
    default: "Saiba Onde Investir para Ganhar Mais Licitações",
  },

  // Supporting subheadlines
  subheadlines: {
    decisionGuide: "Inteligência que avalia oportunidades, prioriza o que importa e guia suas decisões",
    competitive: "Enquanto outros buscam, você já sabe onde investir. Avaliação objetiva de cada oportunidade do mercado",
    visibility: "Visibilidade completa do mercado com avaliação inteligente. Saiba o que merece sua atenção",
    default: "Inteligência que avalia oportunidades, prioriza o que importa e guia suas decisões",
  },

  // Trust badges (displayed below hero)
  trustBadges: [
    {
      icon: Target,
      text: "R$ 2.3 bi em oportunidades",
      detail: "Mapeadas mensalmente",
    },
    {
      icon: Search,
      text: "12 setores cobertos",
      detail: "Especialização por mercado",
    },
    {
      icon: Globe,
      text: "27 estados monitorados",
      detail: "Cobertura nacional completa",
    },
    {
      icon: Bot,
      text: "Avaliação por IA",
      detail: "Análise objetiva de cada oportunidade",
    },
  ],

  // Call-to-action button text
  cta: {
    discovery: "Descobrir Minhas Oportunidades",
    competitive: "Ver Oportunidades do Meu Mercado",
    trial: "Experimentar Sem Compromisso",
    default: "Descobrir Minhas Oportunidades",
  },
};

// ============================================================================
// VALUE PROPOSITIONS (4 Key Differentiators — Decision Intelligence)
// ============================================================================

export const valueProps = {
  prioritization: {
    title: "Priorização Inteligente",
    shortDescription: "Saiba onde focar. O sistema avalia e indica o que merece sua atenção",
    longDescription:
      "Não perca tempo analisando oportunidades que não se encaixam no seu perfil. O SmartLic avalia cada oportunidade e prioriza as que mais se adequam ao seu negócio. Invista energia onde o retorno é maior.",
    icon: Target,
    metric: "Foco",
    proof: "Análise de adequação por setor, região e perfil de atuação",
  },

  analysis: {
    title: "Análise Automatizada",
    shortDescription: "Não leia editais para decidir. IA avalia requisitos, prazos e contexto",
    longDescription:
      "IA avalia cada oportunidade e extrai os critérios decisivos: valor, prazo, requisitos de elegibilidade, competitividade. Você recebe uma avaliação objetiva — vale a pena ou não, e por quê.",
    icon: Bot,
    metric: "Objetiva",
    proof: "Avaliação automatizada com critérios objetivos por IA",
  },

  uncertainty: {
    title: "Redução de Incerteza",
    shortDescription: "Entre preparado. Decisões baseadas em critérios objetivos, não intuição",
    longDescription:
      "Elimine o achismo. Cada oportunidade vem com dados consolidados de múltiplas fontes oficiais, avaliação de adequação e critérios objetivos. Decida com confiança em vez de apostar no escuro.",
    icon: ShieldCheck,
    metric: "Confiança",
    proof: "Dados consolidados de dezenas de fontes oficiais",
  },

  coverage: {
    title: "Cobertura Nacional",
    shortDescription: "Nunca perca uma oportunidade por falta de visibilidade",
    longDescription:
      "Monitoramos dezenas de fontes oficiais em todos os 27 estados, todos os dias. Cada oportunidade relevante para o seu setor é identificada, avaliada e entregue. Visibilidade completa do mercado.",
    icon: Globe,
    metric: "27 UFs",
    proof: "Monitoramento contínuo de fontes federais, estaduais e municipais",
  },
};

// ============================================================================
// FEATURES PAGE COPY
// ============================================================================

export const features = {
  sectorSearch: {
    title: "Busca por Setor, Não por Termos",
    painPoint:
      "Outras plataformas exigem que você adivinhe dezenas de palavras-chave",
    solution:
      "No SmartLic, você seleciona seu setor e nosso algoritmo encontra todas as variações",
    details:
      "Selecione seu setor de atuação e receba oportunidades específicas do seu mercado. Sem adivinhação de termos, sem resultados fora de contexto.",
    benefits: [
      "Seleção intuitiva por setor de atuação",
      "Nunca perca oportunidades por terminologia",
      "Cobertura abrangente do seu mercado",
    ],
  },

  intelligentFiltering: {
    title: "Filtragem Inteligente com Precisão",
    painPoint:
      "Outras plataformas entregam milhares de resultados irrelevantes",
    solution:
      "No SmartLic, algoritmos proprietários garantem que você analise apenas o que realmente importa",
    details:
      "Algoritmos proprietários aplicam múltiplas camadas de filtragem: setor, valor, status, exclusão de falsos positivos. Apenas oportunidades relevantes para o seu perfil.",
    benefits: [
      "Foco total no que é relevante",
      "Alta confiança nos resultados",
      "Decisões mais rápidas e assertivas",
    ],
  },

  multiSourceConsolidation: {
    title: "Consolidação Automática de Fontes Oficiais",
    painPoint:
      "Outras plataformas exigem que você busque em dezenas de portais separadamente",
    solution:
      "No SmartLic, consolidamos dezenas de fontes oficiais em uma única busca automática",
    details:
      "Monitoramento automático de fontes federais, estaduais e municipais. Cobertura nacional completa sem precisar acessar múltiplos portais.",
    benefits: [
      "Nunca perca oportunidades em outros portais",
      "Visibilidade completa do mercado",
      "Monitoramento contínuo de todas as fontes",
    ],
  },

  decisionIntelligence: {
    title: "Inteligência de Decisão por IA",
    painPoint: "Outras plataformas exigem leitura manual de editais extensos",
    solution: "No SmartLic, IA avalia cada oportunidade e indica se vale a pena",
    details:
      "IA analisa oportunidades e extrai informações críticas: valor estimado, prazo, requisitos de elegibilidade, pontos de atenção. Avaliação objetiva para decisão informada.",
    benefits: [
      "Avaliação objetiva de cada oportunidade",
      "Decisões go/no-go informadas",
      "Nunca perca detalhes críticos",
    ],
  },

  competitiveAdvantage: {
    title: "Vantagem Competitiva Real",
    painPoint: "Sem visibilidade, você perde oportunidades para concorrentes",
    solution: "No SmartLic, posicione-se antes da concorrência com visibilidade completa",
    details:
      "Quem tem visibilidade completa do mercado se posiciona primeiro. Receba oportunidades priorizadas assim que são publicadas. Sua vantagem é saber antes.",
    benefits: [
      "Posicione-se antes da concorrência",
      "Oportunidades assim que são publicadas",
      "Vantagem competitiva sustentável",
    ],
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
        smartLicInvestment: 1_999,
        potentialReturn: "100x",
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
      smartlic: "7 dias do produto completo",
    },
  },

  // Guarantee messaging
  guarantee: {
    headline: "Avalie Sem Compromisso",
    description:
      "Produto completo por 7 dias para você conhecer o poder da inteligência de decisão. Sem cartão, sem compromisso.",
  },

  // Transparency statement
  transparency:
    "Investimento transparente. Sem pegadinhas, sem letras pequenas. Cancele quando quiser em 1 clique.",

  // CTA
  cta: "Descobrir Minhas Oportunidades",
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

  finalCta: "Descobrir Minhas Oportunidades",
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
  sectionTitle: "SmartLic em Acao",
  sectionSubtitle:
    "Veja como analisamos oportunidades reais e sugerimos decisoes objetivas",
  flow: ["Licitacao Real", "Analise SmartLic", "Decisao Sugerida"],
  labels: {
    timeline: "Prazo",
    requirements: "Requisitos",
    competitiveness: "Concorrencia",
    score: "Compatibilidade",
    decision: "Decisao Sugerida",
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
];

// ============================================================================
// PREFERRED PHRASES (ALWAYS USE — GTM-001 AC12-AC13)
// ============================================================================

export const PREFERRED_PHRASES = {
  primaryValue: "Inteligência de decisão em licitações",
  decision: ["avaliação objetiva", "decisão informada", "vale a pena ou não"],
  competitive: ["vantagem competitiva", "posicione-se antes", "visibilidade de mercado"],
  intelligence: ["priorização inteligente", "análise automatizada", "inteligência de fontes"],
  coverage: ["fontes oficiais", "cobertura nacional", "dezenas de fontes consolidadas"],
  uncertainty: ["redução de incerteza", "critérios objetivos", "confiança na decisão"],
  cost: ["custo de não ter visibilidade", "licitação perdida", "oportunidade que vai para outro"],
  trust: "Cancele em 1 clique, sem burocracia",
  // GTM-008: IA as decision evaluator, not summary generator
  aiEvaluation: [
    "avaliação de oportunidade",
    "orientação de decisão",
    "análise de adequação",
    "redução de incerteza",
    "inteligência de decisão",
    "avaliação objetiva",
    "critérios de elegibilidade",
    "análise automatizada",
  ],
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
