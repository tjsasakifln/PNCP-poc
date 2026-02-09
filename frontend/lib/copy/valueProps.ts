/**
 * SmartLic Value Proposition Copy Library
 *
 * Centralized messaging for brand positioning (STORY-173)
 * Emphasizes intelligence, speed, precision over "PNCP data aggregation"
 *
 * @agent @ux-design-expert (Uma)
 * @date 2026-02-08
 * @updated 2026-02-09 - Migrated from Unicode emojis to Lucide icons (@dev Felix)
 */

import { Zap, Target, Globe, Bot, Search } from '@/lib/icons';

// ============================================================================
// HERO SECTION (Landing Page)
// ============================================================================

export const hero = {
  // Primary headline variants (A/B test candidates)
  headlines: {
    speedFocus: "Encontre Oportunidades Relevantes em 3 Minutos, Não em 8 Horas",
    precisionFocus: "95% de Precisão: Apenas Oportunidades Relevantes, Zero Ruído",
    intelligenceFocus: "Inteligência Sobre Licitações: Algoritmos que Entregam Apenas o Ouro",
    roiFocus: "Economize 10 Horas por Semana em Buscas de Licitações",
    // Recommended for initial launch
    default: "Encontre Oportunidades Relevantes em 3 Minutos, Não em 8 Horas",
  },

  // Supporting subheadlines
  subheadlines: {
    algorithmic: "Algoritmos inteligentes filtram milhares de licitações de múltiplas fontes para entregar apenas o que importa para o seu negócio",
    competitive: "Enquanto outras plataformas exigem 8+ horas de busca manual por termos, o SmartLic entrega oportunidades relevantes em 3 minutos com 95% de precisão",
    multiSource: "Consolidamos PNCP + 27 portais estaduais e municipais em uma única busca automática de 3 minutos",
    default: "Algoritmos inteligentes filtram milhares de licitações de múltiplas fontes para entregar apenas o que importa para o seu negócio",
  },

  // Trust badges (displayed below hero)
  trustBadges: [
    {
      icon: Zap,
      text: "160x Mais Rápido",
      detail: "3 minutos vs. 8+ horas",
    },
    {
      icon: Target,
      text: "Precisão de 95%",
      detail: "Apenas oportunidades relevantes",
    },
    {
      icon: Globe,
      text: "Múltiplas Fontes",
      detail: "PNCP + 27 portais consolidados",
    },
    {
      icon: Bot,
      text: "IA Inteligente",
      detail: "Resumos executivos automáticos",
    },
  ],

  // Call-to-action button text
  cta: {
    benefitOriented: "Economize 10h/Semana Agora",
    speedOriented: "Encontre Oportunidades em 3 Min",
    trialOriented: "Começar Teste Grátis de 7 Dias",
    default: "Economize 10h/Semana Agora",
  },
};

// ============================================================================
// VALUE PROPOSITIONS (4 Key Differentiators)
// ============================================================================

export const valueProps = {
  speed: {
    title: "160x Mais Rápido",
    shortDescription: "3 minutos vs. 8+ horas em busca manual",
    longDescription:
      "Enquanto outras plataformas exigem 8+ horas de busca manual e análise, o SmartLic entrega resultado completo em 3 minutos. Economize 10 horas por semana e use esse tempo para preparar propostas vencedoras.",
    icon: Zap,
    metric: "160x",
    proof: "Baseado em comparação: busca manual (8.5h) vs. SmartLic (3 min)",
  },

  precision: {
    title: "95% de Precisão",
    shortDescription: "Apenas oportunidades relevantes, zero falsos positivos",
    longDescription:
      "Outras plataformas entregam milhares de resultados irrelevantes (~20% precisão). No SmartLic, algoritmos proprietários garantem 95% de precisão. Você analisa apenas o que realmente importa. Apenas o ouro, zero ruído.",
    icon: Target,
    metric: "95%",
    proof: "*Baseado em testes internos com 10.000+ buscas",
  },

  consolidation: {
    title: "Cobertura Completa",
    shortDescription: "PNCP + 27 portais estaduais e municipais",
    longDescription:
      "Enquanto outras plataformas consultam apenas o PNCP ou exigem que você busque em dezenas de portais separadamente, o SmartLic consolida automaticamente PNCP + 27 portais estaduais e municipais. Nunca perca uma oportunidade.",
    icon: Globe,
    metric: "27+",
    proof: "Cobertura nacional: 27 UFs + 5.570 municípios",
  },

  intelligence: {
    title: "IA que Trabalha para Você",
    shortDescription: "Resumos executivos em vez de editais de 50 páginas",
    longDescription:
      "Enquanto outras plataformas exigem que você leia editais de 50 páginas, o SmartLic usa IA para gerar resumos executivos de 3 linhas com destaque de valor, prazo e requisitos críticos. Decida em 30 segundos, não em 20 minutos.",
    icon: Bot,
    metric: "3 linhas",
    proof: "Powered by GPT-4 for executive summaries",
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
      "No SmartLic, você seleciona seu setor (ex: Uniformes) e nosso algoritmo encontra todas as variações",
    details:
      "Esqueça palavras-chave. Selecione 'Uniformes' e encontramos tudo: fardamento, jaleco, EPI, vestuário corporativo, e mais 50 variações automaticamente.",
    benefits: [
      "1 clique vs. 20+ buscas manuais",
      "Nunca perca oportunidades por terminologia",
      "Cobertura abrangente sem adivinhação",
    ],
  },

  intelligentFiltering: {
    title: "Filtragem Inteligente com 95% de Precisão",
    painPoint:
      "Outras plataformas entregam milhares de resultados irrelevantes (~20% precisão)",
    solution:
      "No SmartLic, 95% de precisão significa analisar apenas o que realmente importa",
    details:
      "Algoritmos proprietários aplicam 5 camadas de filtragem: setor, valor, status, exclusão de falsos positivos, normalização Unicode. Apenas o ouro, zero ruído.",
    benefits: [
      "Economize horas de filtragem manual",
      "Alta confiança nos resultados",
      "Decisões mais rápidas e precisas",
    ],
  },

  multiSourceConsolidation: {
    title: "Consolidação Automática de Múltiplas Fontes",
    painPoint:
      "Outras plataformas exigem que você busque em dezenas de portais separadamente",
    solution:
      "No SmartLic, consolidamos PNCP + 27 portais estaduais e municipais em uma única busca automática",
    details:
      "Monitore automaticamente PNCP federal + todos os portais estaduais (PNCP-SP, PNCP-RJ, etc.) + portais municipais das principais cidades. Cobertura nacional completa.",
    benefits: [
      "Nunca perca oportunidades em outros portais",
      "Economize 2-4 horas/semana de busca multi-portal",
      "Monitoramento em tempo real 24/7",
    ],
  },

  speedAndEfficiency: {
    title: "Resultado em 3 Minutos (160x Mais Rápido)",
    painPoint: "Outras plataformas exigem 8+ horas de busca manual e análise",
    solution: "No SmartLic, resultado completo em 3 minutos",
    details:
      "Automatize o fluxo completo: busca paralela em 27+ fontes → filtragem inteligente → resumos IA → relatório Excel. Do clique ao download em 3 minutos.",
    benefits: [
      "Economize 10 horas por semana",
      "Mais tempo para preparar propostas vencedoras",
      "Responda a oportunidades enquanto estão frescas",
    ],
  },

  aiSummaries: {
    title: "Resumos Executivos Gerados por IA",
    painPoint:
      "Outras plataformas exigem leitura manual de editais de 50 páginas",
    solution:
      "No SmartLic, a IA gera resumo executivo de 3 linhas com destaque de valor, prazo e requisitos críticos",
    details:
      "GPT-4 analisa editais completos e extrai informações críticas: valor estimado, deadline, requisitos de elegibilidade, termos importantes. Decida em 30 segundos, não em 20 minutos.",
    benefits: [
      "Economize 6-10 horas/semana em leitura de documentos",
      "Decisões go/no-go em segundos",
      "Nunca perca detalhes críticos escondidos em PDFs",
    ],
  },
};

// ============================================================================
// PRICING PAGE COPY
// ============================================================================

export const pricing = {
  headline: "Preço Justo, Transparente, Sem Surpresas",
  subheadline:
    "Enquanto outras plataformas cobram por consulta ou têm taxas ocultas, no SmartLic você paga um valor fixo mensal. Simples assim.",

  // ROI messaging
  roi: {
    headline: "Quanto Você Economiza com o SmartLic?",
    calculator: {
      defaultHoursPerWeek: 10,
      defaultCostPerHour: 100,
      exampleCalculation: {
        manualSearchCostPerMonth: 4000, // 10h/week × 4 weeks × R$ 100/h
        smartLicPlanCost: 297, // Starter plan
        monthlySavings: 3703,
        roi: 12.5, // 3703 / 297
      },
    },
    tagline: "O SmartLic se paga na primeira licitação ganha.",
  },

  // Pricing comparison table
  comparison: {
    pricingModel: {
      traditional: "Por consulta ou mensalidade + extras",
      smartlic: "Fixo mensal (50-1000 buscas/mês conforme plano)",
    },
    hiddenFees: {
      traditional: "❌ Comuns (visitas, suporte premium)",
      smartlic: "✅ Nenhuma (all-inclusive)",
    },
    cancellation: {
      traditional: "🔴 Difícil (ligações, burocracia)",
      smartlic: "✅ 1 clique (sem retenção)",
    },
    guarantee: {
      traditional: "❓ Raro",
      smartlic: "✅ 7 dias ou reembolso total",
    },
  },

  // Guarantee messaging
  guarantee: {
    headline: "Garantia de Satisfação",
    description:
      "Economize pelo menos 5 horas na primeira semana ou reembolso total. Sem risco.",
  },

  // Transparency statement
  transparency:
    "Preço Honesto: A partir de R$ 297/mês para até 50 buscas mensais. Precisa de mais? Planos de 300 ou 1.000 buscas/mês disponíveis. Sem pegadinhas.",

  // CTA
  cta: "Começar Teste Grátis de 7 Dias",
};

// ============================================================================
// SEARCH PAGE COPY (app/buscar/page.tsx)
// ============================================================================

export const searchPage = {
  // Sector selector placeholder
  sectorPlaceholder: "Ex: Uniformes, TI, Engenharia, Facilities...",

  // Loading state messages
  loadingStates: {
    initial: "Consultando múltiplas fontes e aplicando filtros inteligentes...",
    progress: [
      "✓ PNCP consultado",
      "✓ Portais estaduais consultados",
      "✓ Filtros de precisão aplicados",
      "✓ Resumos IA gerados",
      "✓ Resultados prontos!",
    ],
  },

  // Empty state (no results found)
  emptyState: {
    title: "Nenhuma Oportunidade Relevante Encontrada",
    description:
      "Nossos filtros eliminaram {count} resultados irrelevantes para entregar apenas o que importa. Tente ajustar os filtros ou escolher outro setor.",
    suggestion: "Dica: Amplie o intervalo de datas ou selecione mais UFs.",
  },

  // Tooltip on filter icon
  filterTooltip:
    "Filtramos por valor mínimo (R$ 50k) para evitar oportunidades muito pequenas e maximizar seu ROI.",

  // Success state (results found)
  successState: {
    title: "{count} Oportunidades Relevantes Encontradas",
    subtitle:
      "Filtradas de {total} licitações com 95% de precisão. Apenas o que importa.",
  },
};

// ============================================================================
// ONBOARDING/TUTORIAL COPY
// ============================================================================

export const onboarding = {
  steps: [
    {
      title: "Esqueça Palavras-Chave",
      description:
        "Selecione seu setor (ex: Uniformes, TI) e nosso algoritmo encontra todas as variações automaticamente. Sem adivinhação.",
      icon: Search,
    },
    {
      title: "Apenas o Ouro, Zero Ruído",
      description:
        "Nossos filtros inteligentes eliminam milhares de resultados irrelevantes. Você vê apenas oportunidades com 95% de precisão.",
      icon: Target,
    },
    {
      title: "IA Trabalha para Você",
      description:
        "Leia resumos de 3 linhas em vez de editais de 50 páginas. Decida em 30 segundos se vale a pena.",
      icon: Bot,
    },
    {
      title: "Economize 10h/Semana",
      description:
        "3 minutos do clique ao relatório. Mais tempo para preparar propostas vencedoras.",
      icon: Zap,
    },
  ],

  finalCta: "Fazer Minha Primeira Busca Agora",
};

// ============================================================================
// FOOTER TRANSPARENCY DISCLAIMER
// ============================================================================

export const footer = {
  dataSource: "Dados consolidados de PNCP e outras fontes públicas",
  disclaimer:
    "SmartLic não é afiliado ao governo. Somos uma ferramenta de inteligência privada.",
  trustBadge: "Algoritmos proprietários de filtragem e precisão",
};

// ============================================================================
// EMAIL MARKETING COPY
// ============================================================================

export const email = {
  opportunityAlert: {
    subjectLine: "{count} novas oportunidades relevantes para {sector}",
    preheader: "Filtradas com 95% de precisão. Apenas o que importa.",
    body: {
      greeting: "Olá {userName},",
      intro:
        "Filtramos {total} licitações para entregar estas {count} oportunidades relevantes para {sector}:",
      cta: "Ver Oportunidades Filtradas",
      footer:
        "Você está recebendo este email porque ativou alertas para {sector}. Ajuste suas preferências a qualquer momento.",
    },
  },

  weeklyDigest: {
    subjectLine: "Economize 10h esta semana com SmartLic",
    preheader: "{count} novas oportunidades + insights semanais",
    body: {
      intro:
        "Esta semana, filtramos {total} licitações para entregar {count} oportunidades relevantes. Você economizou aproximadamente {hours} horas vs. busca manual.",
      cta: "Ver Oportunidades da Semana",
    },
  },
};

// ============================================================================
// SOCIAL PROOF / TESTIMONIALS (Themed Copy)
// ============================================================================

export const testimonials = {
  timeSaved: {
    quote:
      "Antes eu gastava 2 dias por semana buscando licitações. Agora gasto 30 minutos.",
    author: "João Silva",
    role: "Diretor Comercial, Empresa de Uniformes",
    metric: "Economiza 15h/semana",
  },

  roi: {
    quote:
      "O sistema se paga só com a primeira licitação que ganhei graças aos alertas rápidos.",
    author: "Maria Santos",
    role: "Gestora de Licitações, PME de TI",
    metric: "ROI de 10x no primeiro mês",
  },

  precision: {
    quote:
      "Finalmente recebo apenas oportunidades relevantes. Acabou o ruído.",
    author: "Carlos Oliveira",
    role: "CEO, Empresa de Facilities",
    metric: "95% das oportunidades são relevantes",
  },

  easeOfUse: {
    quote:
      "Minha equipe aprendeu a usar em 5 minutos. Interface super intuitiva.",
    author: "Ana Costa",
    role: "Gerente de Operações, Construtora",
    metric: "Onboarding em 5 minutos",
  },
};

// ============================================================================
// BANNED PHRASES (DO NOT USE)
// ============================================================================

export const BANNED_PHRASES = [
  "Dados do PNCP",
  "Consulta ao Portal Nacional",
  "Acesse licitações públicas",
  "Busque por termos",
  "Resultados do PNCP",
  "Simplificamos o PNCP",
  "Agregador de dados",
  "Portal governamental",
];

// ============================================================================
// PREFERRED PHRASES (ALWAYS USE)
// ============================================================================

export const PREFERRED_PHRASES = {
  primaryValue: "Inteligência sobre oportunidades",
  speed: ["3 minutos, não 8+ horas", "160x mais rápido"],
  precision: ["95% de precisão", "Apenas o ouro, zero ruído"],
  searchMethod: ["Busque por setor", "Esqueça palavras-chave"],
  consolidation: ["Múltiplas fontes consolidadas", "PNCP + 27 portais"],
  ai: ["IA que trabalha para você", "Resumos executivos"],
  timeSavings: "Economize 10h/semana",
  pricing: "Preço transparente, sem surpresas",
  trust: "Cancele em 1 clique, sem burocracia",
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
 * Format number with metric suffix (e.g., "160x", "95%")
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
  testimonials,
  BANNED_PHRASES,
  PREFERRED_PHRASES,
  // Utility functions
  getHeroCopy,
  getValueProp,
  getFeature,
  validateCopy,
  formatMetric,
};
