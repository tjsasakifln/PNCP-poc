/**
 * GTM-005: Real Analysis Examples Data
 *
 * 5 curated examples of real procurement opportunities
 * analyzed by SmartLic with actionable decisions.
 *
 * Structure: Procurement -> Analysis -> Decision
 */

// ============================================================================
// INTERFACES
// ============================================================================

export type DecisionType = 'go' | 'evaluate' | 'no_go';

export type CategoryId =
  | 'uniformes'
  | 'facilities'
  | 'epi'
  | 'elevadores'
  | 'saude';

export interface AnalysisExample {
  id: string;
  title: string;
  uf: string;
  value: number;
  category: CategoryId;
  analysis: {
    timeline: string;
    requirements: string;
    competitiveness: string;
    score: number;
  };
  decision: {
    recommendation: string;
    justification: string;
    type: DecisionType;
  };
}

// ============================================================================
// CATEGORY METADATA
// ============================================================================

export interface CategoryMeta {
  label: string;
  color: string;
  bgColor: string;
  darkColor: string;
  darkBgColor: string;
}

export const CATEGORY_META: Record<CategoryId, CategoryMeta> = {
  uniformes: {
    label: 'Uniformes',
    color: 'text-blue-700',
    bgColor: 'bg-blue-50',
    darkColor: 'dark:text-blue-300',
    darkBgColor: 'dark:bg-blue-900/30',
  },
  facilities: {
    label: 'Facilities',
    color: 'text-emerald-700',
    bgColor: 'bg-emerald-50',
    darkColor: 'dark:text-emerald-300',
    darkBgColor: 'dark:bg-emerald-900/30',
  },
  epi: {
    label: 'EPI',
    color: 'text-amber-700',
    bgColor: 'bg-amber-50',
    darkColor: 'dark:text-amber-300',
    darkBgColor: 'dark:bg-amber-900/30',
  },
  elevadores: {
    label: 'Elevadores',
    color: 'text-purple-700',
    bgColor: 'bg-purple-50',
    darkColor: 'dark:text-purple-300',
    darkBgColor: 'dark:bg-purple-900/30',
  },
  saude: {
    label: 'Saude',
    color: 'text-rose-700',
    bgColor: 'bg-rose-50',
    darkColor: 'dark:text-rose-300',
    darkBgColor: 'dark:bg-rose-900/30',
  },
};

// ============================================================================
// DECISION METADATA
// ============================================================================

export const DECISION_META: Record<
  DecisionType,
  { label: string; color: string; bgColor: string; darkColor: string; darkBgColor: string }
> = {
  go: {
    label: 'PARTICIPAR',
    color: 'text-emerald-700',
    bgColor: 'bg-emerald-50',
    darkColor: 'dark:text-emerald-300',
    darkBgColor: 'dark:bg-emerald-900/30',
  },
  evaluate: {
    label: 'AVALIAR COM CAUTELA',
    color: 'text-amber-700',
    bgColor: 'bg-amber-50',
    darkColor: 'dark:text-amber-300',
    darkBgColor: 'dark:bg-amber-900/30',
  },
  no_go: {
    label: 'NAO PARTICIPAR',
    color: 'text-red-700',
    bgColor: 'bg-red-50',
    darkColor: 'dark:text-red-300',
    darkBgColor: 'dark:bg-red-900/30',
  },
};

// ============================================================================
// CURATED EXAMPLES (5)
// ============================================================================

export const ANALYSIS_EXAMPLES: AnalysisExample[] = [
  {
    id: 'ex-uniformes-sp',
    title: 'Fornecimento de Uniformes Escolares',
    uf: 'SP',
    value: 450_000,
    category: 'uniformes',
    analysis: {
      timeline: 'Encerramento em 15 dias — prazo viavel para preparacao',
      requirements: 'Amostras obrigatórias, certificação INMETRO têxtil',
      competitiveness: '3-5 concorrentes esperados, mercado fragmentado',
      score: 8.5,
    },
    decision: {
      recommendation: 'Participar',
      justification:
        'Alta adequação ao perfil. Valor expressivo, concorrência moderada e prazo confortável. Priorize a preparação das amostras.',
      type: 'go',
    },
  },
  {
    id: 'ex-facilities-rj',
    title: 'Servicos de Limpeza e Manutencao Predial',
    uf: 'RJ',
    value: 1_200_000,
    category: 'facilities',
    analysis: {
      timeline: 'Encerramento em 8 dias — prazo apertado',
      requirements:
        'Atestado de capacidade técnica, equipe mínima de 30 profissionais',
      competitiveness: '8-12 concorrentes, mercado saturado',
      score: 5.2,
    },
    decision: {
      recommendation: 'Avaliar com cautela',
      justification:
        'Valor atrativo mas concorrência intensa. Exige investimento significativo em equipe. Só participar se já possuir atestados compatíveis.',
      type: 'evaluate',
    },
  },
  {
    id: 'ex-epi-mg',
    title: 'Aquisicao de EPIs — Equipamentos de Protecao',
    uf: 'MG',
    value: 85_000,
    category: 'epi',
    analysis: {
      timeline: 'Encerramento em 22 dias — prazo confortavel',
      requirements: 'Certificação CA válida, registro no fornecedor',
      competitiveness: '5-8 concorrentes, mercado competitivo',
      score: 7.0,
    },
    decision: {
      recommendation: 'Participar',
      justification:
        'Boa oportunidade de entrada. Valor menor mas requisitos acessiveis e prazo confortavel para preparacao completa.',
      type: 'go',
    },
  },
  {
    id: 'ex-elevadores-sp',
    title: 'Manutencao Preventiva de Elevadores',
    uf: 'SP',
    value: 350_000,
    category: 'elevadores',
    analysis: {
      timeline: 'Encerramento em 5 dias — prazo muito curto',
      requirements:
        'Registro CREA, equipe técnica certificada, peças originais',
      competitiveness: '2-3 concorrentes, mercado especializado',
      score: 4.8,
    },
    decision: {
      recommendation: 'Nao participar',
      justification:
        'Prazo insuficiente para preparação adequada. Requisitos técnicos exigem certificações específicas. Risco elevado de desclassificação.',
      type: 'no_go',
    },
  },
  {
    id: 'ex-saude-ba',
    title: 'Uniformes para Profissionais de Saude',
    uf: 'BA',
    value: 280_000,
    category: 'saude',
    analysis: {
      timeline: 'Encerramento em 18 dias — prazo adequado',
      requirements: 'Tecido antimicrobiano certificado, normas ANVISA',
      competitiveness: '4-6 concorrentes, nicho especializado',
      score: 8.8,
    },
    decision: {
      recommendation: 'Participar com prioridade',
      justification:
        'Excelente adequação. Nicho especializado com menor concorrência. Diferencial técnico em tecido antimicrobiano pode ser decisivo.',
      type: 'go',
    },
  },
];

// ============================================================================
// SECTION COPY
// ============================================================================

export const SECTION_COPY = {
  title: 'SmartLic em Ação',
  subtitle:
    'Veja como analisamos oportunidades reais e sugerimos decisões objetivas',
  flow: ['Licitação Real', 'Análise SmartLic', 'Decisão Sugerida'],
};

// ============================================================================
// UTILITY
// ============================================================================

export function formatCurrency(value: number): string {
  if (value >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toFixed(1)}M`;
  }
  return `R$ ${(value / 1_000).toFixed(0)}K`;
}

export function getScoreColor(score: number): {
  text: string;
  bg: string;
  bar: string;
} {
  if (score >= 7.5) {
    return {
      text: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-900/30',
      bar: 'bg-emerald-500',
    };
  }
  if (score >= 5.0) {
    return {
      text: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-900/30',
      bar: 'bg-amber-500',
    };
  }
  return {
    text: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-900/30',
    bar: 'bg-red-500',
  };
}
