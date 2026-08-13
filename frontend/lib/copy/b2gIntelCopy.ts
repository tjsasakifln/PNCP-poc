/**
 * REPO-COMMS #1289: B2G Intelligence Positioning Copy
 *
 * Migração de "monitoramento de licitações com IA" para "vantagem competitiva".
 * Tom: terminal de inteligência. Sem IA, algoritmo, plataforma, monitoramento.
 *
 * Design validation: 3 opções apresentadas via AskUserQuestion (2026-05-31):
 *   1. Bloomberg Terminal (dark, monospace, dados densos)
 *   2. Palantir Gotham (dark, mapas, redes)
 *   3. Linear/Supabase (light, minimal, moderna)
 * Opção escolhida: #1 Bloomberg Terminal — melhor alinhamento com
 * "terminal de inteligência" e diferenciação de SaaS genérico.
 */

// ============================================================================
// TypeScript interfaces for copy objects (IDE autocomplete + type safety)
// ============================================================================

export interface B2GHeroCopy {
  headline: string;
  subheadlines: string[];
  cta: {
    primary: string;
    primaryHref: string;
    secondary: string;
    secondaryHref: string;
  };
  trustLine: string;
}

export interface AntecipeColumn {
  title: string;
  description: string;
  metric: string;
  metricLabel: string;
}

export interface AntecipeDecidaExecuteCopy {
  sectionId: string;
  headline: string;
  columns: AntecipeColumn[];
}

export interface TerminalComparisonCopy {
  sectionId: string;
  kicker: string;
  headline: string;
  before: { title: string; items: string[] };
  after: { title: string; items: string[] };
}

export interface SocialProofMetric {
  value: string;
  label: string;
  detail: string;
}

export interface SocialProofCopy {
  sectionId: string;
  headline: string;
  metrics: SocialProofMetric[];
}

export interface PersonaGroup {
  title: string;
  description: string;
}

export interface PersonasCopy {
  sectionId: string;
  headline: string;
  groups: PersonaGroup[];
}

export interface PricingB2GCopy {
  sectionId: string;
  headline: string;
  subheadline: string;
  note: string;
}

export interface MarketSocialQuote {
  text: string;
  author: string;
  role: string;
}

export interface MarketSocialCopy {
  sectionId: string;
  headline: string;
  quotes: MarketSocialQuote[];
}

// ============================================================================
// HERO — Terminal de Inteligência B2G
// ============================================================================

export const b2gHero: B2GHeroCopy = {
  headline: "Inteligência pública de licitações da CONFENGE.",

  subheadlines: [
    "Consulte o fato. Veja a fonte. Decida se pede diagnóstico.",
    "Empresa, contrato, licitação, órgão e município no mesmo grafo.",
    "O SmartLic publica o dado. A CONFENGE opera a decisão.",
  ],

  cta: {
    primary: "Explorar dados públicos",
    primaryHref: "/licitacoes",
    secondary: "Pedir diagnóstico CONFENGE",
    secondaryHref: "/consultoria-b2g",
  },

  trustLine: "Sem login para consultar. Sem trial. Sem plano.",
};

// ============================================================================
// SEÇÃO 2 — Antecipe, Decida, Execute (3 colunas)
// ============================================================================

export const antecipeDecidaExecute: AntecipeDecidaExecuteCopy = {
  sectionId: "o-que-faz",
  headline: "O que o SmartLic realmente faz",
  columns: [
    {
      title: "Antecipe",
      description:
        "Saiba quais contratos vão vencer e quais órgãos vão comprar. Dados oficiais, processamento proprietário — você vê o movimento antes do edital sair.",
      metric: "2M+",
      metricLabel: "contratos analisados",
    },
    {
      title: "Decida",
      description:
        "Veja onde seu concorrente está ganhando e onde ele está caindo. Decida participar com evidência, não com intuição.",
      metric: "500+",
      metricLabel: "órgãos monitorados",
    },
    {
      title: "Execute",
      description:
        "Gerencie todo seu pipeline B2G em um só lugar. Do edital à proposta, com visibilidade completa de cada etapa.",
      metric: "20",
      metricLabel: "setores classificados",
    },
  ],
};

// ============================================================================
// SEÇÃO 3 — Terminal Comparison (antes/depois)
// ============================================================================

export const terminalComparison: TerminalComparisonCopy = {
  sectionId: "terminal",
  kicker: "Não é um alerta de edital. É um terminal de inteligência.",
  headline: "De planilha, Trello e WhatsApp para um sistema operacional B2G",
  before: {
    title: "Antes",
    items: [
      "Planilha compartilhada no WhatsApp",
      "Edital lido por 3 pessoas diferentes",
      "Pipeline em post-it ou Trello improvisado",
      "Decisão baseada em feeling do sócio",
      "Oportunidade descoberta 5 dias depois da publicação",
    ],
  },
  after: {
    title: "Com SmartLic",
    items: [
      "Dados oficiais processados automaticamente",
      "Classificação setorial com precisão validada",
      "Pipeline B2G estruturado com estágios e alertas",
      "Decisão baseada em 4 fatores de viabilidade",
      "Oportunidades detectadas em tempo real, 27 UFs",
    ],
  },
};

// ============================================================================
// SEÇÃO 4 — Prova Social (métricas do datalake)
// ============================================================================

export const socialProof: SocialProofCopy = {
  sectionId: "numeros",
  headline: "Números que sustentam sua vantagem",
  metrics: [
    { value: "2M+", label: "Contratos analisados", detail: "Base histórica de contratações públicas" },
    { value: "500+", label: "Órgãos monitorados", detail: "Cobertura federal, estadual e municipal" },
    { value: "20", label: "Setores classificados", detail: "Classificação setorial proprietária" },
    { value: "27", label: "UFs cobertas", detail: "Cobertura nacional de fontes oficiais" },
  ],
};

// ============================================================================
// SEÇÃO 5 — Personas
// ============================================================================

export const personas: PersonasCopy = {
  sectionId: "para-quem",
  headline: "Para quem é o SmartLic",
  groups: [
    {
      title: "Integradoras e empresas de TI",
      description:
        "Antecipe contratos de transformação digital, infraestrutura e software antes da publicação do edital. Saiba quais órgãos estão expandindo orçamento de TI.",
    },
    {
      title: "Distribuidores e fornecedores recorrentes",
      description:
        "Veja padrões de compra de cada órgão. Saiba quando seu produto será demandado e em qual quantidade — antes da licitação abrir.",
    },
    {
      title: "Consultorias B2G",
      description:
        "Entregue inteligência para seus clientes com dados que nenhum assessor tem. Diferencie seu serviço com evidência, não com PDF.",
    },
    {
      title: "Operadores profissionais de licitação",
      description:
        "Substitua busca manual por terminal de inteligência. Pipeline estruturado, classificação automática, decisão baseada em dados.",
    },
  ],
};

// ============================================================================
// SEÇÃO 6 — Pricing (placeholder até REPO-TIER-COMMAND)
// ============================================================================

export const pricingB2G: PricingB2GCopy = {
  sectionId: "planos",
  headline: "Comece com o plano que cabe no seu momento",
  subheadline: "Todos os planos incluem acesso completo. Sem limite de busca. Sem surpresa.",
  note: "Novo tier SmartLic Command em breve — para operadores que precisam de war room e inteligência concorrencial.",
};

// ============================================================================
// SEÇÃO 7 — Social Proof / Depoimentos
// ============================================================================

export const marketSocial: MarketSocialCopy = {
  sectionId: "mercado",
  headline: "O que o mercado diz",
  quotes: [
    {
      text: "Finalmente alguém entendeu que B2G não é sobre buscar edital — é sobre decidir onde competir.",
      author: "Sócio de consultoria B2G",
      role: "São Paulo, SP",
    },
    {
      text: "A antecipação de contrato mudou nossa operação. Chegamos antes do edital, preparamos proposta com calma.",
      author: "Diretor Comercial de integradora de TI",
      role: "Belo Horizonte, MG",
    },
  ],
};

// ============================================================================
// BANNED WORDS (REPO-COMMS #1289 — adicional ao BANNED_PHRASES existente)
// ============================================================================

export const REPO_COMMS_BANNED_WORDS = [
  "IA",
  "inteligência artificial",
  "machine learning",
  "algoritmo",
  "plataforma",
  "monitoramento",
  "alerta",
  "match",
  "buscar",
  "encontrar",
  "dados abertos",
  // NO-JARGON-004: Technical jargon — sync with BANNED_PHRASES
  "datalake",
  "data lake",
  "GPT-4",
  "GPT-3.5",
  "GPT",
  "LLM",
  "large language model",
  "cache expirado",
  "em cache",
  "quota",
];

// ============================================================================
// PREFERRED WORDS (REPO-COMMS #1289)
// ============================================================================

export const REPO_COMMS_PREFERRED_WORDS = {
  nouns: [
    "inteligência comercial",
    "vantagem competitiva",
    "antecipação",
    "território",
    "comando",
    "predição",
    "mapa",
    "oportunidade",
    "estratégia",
    "receita pública",
  ],
  verbs: ["antecipar", "decidir", "executar", "posicionar", "detectar", "classificar"],
};
