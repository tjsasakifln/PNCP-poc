/**
 * SmartLic ROI Calculator Logic
 *
 * Calculate time savings and ROI to justify SmartLic pricing vs. manual search cost
 * Used on pricing page to demonstrate value proposition (STORY-173)
 *
 * @agent @ux-design-expert (Uma)
 * @date 2026-02-08
 */

// ============================================================================
// CONSTANTS & DEFAULTS
// ============================================================================

export const DEFAULT_VALUES = {
  // Manual search time (hours per week)
  hoursPerWeek: 10,

  // User's hourly cost (R$ per hour)
  costPerHour: 100,

  // Time saved per search (hours)
  timeSavedPerSearch: 8.5, // Manual (8.5h) vs SmartLic (0.05h = 3 min)

  // SmartLic time per search (hours)
  smartlicTimePerSearch: 0.05, // 3 minutes = 0.05 hours
};

// ============================================================================
// ROI CALCULATION INTERFACES
// ============================================================================

export interface ROIInputs {
  hoursPerWeek: number;
  costPerHour: number;
  planPrice: number; // Monthly price in BRL (from backend plan data)
}

export interface ROIOutputs {
  // Manual search costs
  manualSearchCostPerWeek: number;
  manualSearchCostPerMonth: number;
  manualSearchCostPerYear: number;

  // SmartLic costs
  smartlicPlanCost: number;
  smartlicCostPerYear: number;

  // Savings
  monthlySavings: number;
  yearlySavings: number;

  // ROI metrics
  roi: number; // ROI multiple (e.g., 12.5x)
  roiPercentage: number; // ROI percentage (e.g., 1250%)
  paybackPeriodDays: number; // Days to recoup investment

  // Time metrics
  hoursSavedPerWeek: number;
  hoursSavedPerMonth: number;
  hoursSavedPerYear: number;

  // Formatted strings (for display)
  formatted: {
    manualSearchCostPerMonth: string;
    smartlicPlanCost: string;
    monthlySavings: string;
    roi: string;
    roiPercentage: string;
    paybackPeriodDays: string;
    hoursSavedPerMonth: string;
  };
}

// ============================================================================
// CORE ROI CALCULATION FUNCTION
// ============================================================================

export function calculateROI(inputs: ROIInputs): ROIOutputs {
  const { hoursPerWeek, costPerHour, planPrice } = inputs;

  // Manual search costs
  const manualSearchCostPerWeek = hoursPerWeek * costPerHour;
  const manualSearchCostPerMonth = manualSearchCostPerWeek * 4; // 4 weeks/month
  const manualSearchCostPerYear = manualSearchCostPerMonth * 12;

  // SmartLic costs
  const smartlicPlanCost = planPrice;
  const smartlicCostPerYear = smartlicPlanCost * 12;

  // Savings
  const monthlySavings = manualSearchCostPerMonth - smartlicPlanCost;
  const yearlySavings = manualSearchCostPerYear - smartlicCostPerYear;

  // ROI calculation
  const roi = monthlySavings / smartlicPlanCost; // e.g., 3703 / 297 = 12.5x
  const roiPercentage = roi * 100;

  // Payback period (days to recoup SmartLic investment)
  const dailySavings = monthlySavings / 30;
  const paybackPeriodDays = smartlicPlanCost / dailySavings;

  // Time saved
  const hoursSavedPerWeek = hoursPerWeek - (hoursPerWeek * DEFAULT_VALUES.smartlicTimePerSearch) / DEFAULT_VALUES.timeSavedPerSearch;
  const hoursSavedPerMonth = hoursSavedPerWeek * 4;
  const hoursSavedPerYear = hoursSavedPerMonth * 12;

  return {
    manualSearchCostPerWeek,
    manualSearchCostPerMonth,
    manualSearchCostPerYear,
    smartlicPlanCost,
    smartlicCostPerYear,
    monthlySavings,
    yearlySavings,
    roi,
    roiPercentage,
    paybackPeriodDays,
    hoursSavedPerWeek,
    hoursSavedPerMonth,
    hoursSavedPerYear,
    formatted: {
      manualSearchCostPerMonth: formatCurrency(manualSearchCostPerMonth),
      smartlicPlanCost: formatCurrency(smartlicPlanCost),
      monthlySavings: formatCurrency(monthlySavings),
      roi: formatROI(roi),
      roiPercentage: formatPercentage(roiPercentage),
      paybackPeriodDays: formatDays(paybackPeriodDays),
      hoursSavedPerMonth: formatHours(hoursSavedPerMonth),
    },
  };
}

// ============================================================================
// FORMATTING UTILITIES
// ============================================================================

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatROI(value: number): string {
  return `${value.toFixed(1)}x`;
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(0)}%`;
}

export function formatDays(value: number): string {
  if (value < 1) {
    return "< 1 dia";
  }
  return `${Math.ceil(value)} dias`;
}

export function formatHours(value: number): string {
  return `${Math.round(value)}h`;
}

// ============================================================================
// QUICK CALCULATION HELPERS
// ============================================================================

/**
 * Calculate monthly savings for default scenario (10h/week @ R$100/h, R$149/month plan)
 */
export function getDefaultROI(planPrice: number = 149): ROIOutputs {
  return calculateROI({
    hoursPerWeek: DEFAULT_VALUES.hoursPerWeek,
    costPerHour: DEFAULT_VALUES.costPerHour,
    planPrice,
  });
}

/**
 * Quick check if SmartLic provides positive ROI
 */
export function hasPositiveROI(inputs: ROIInputs): boolean {
  const result = calculateROI(inputs);
  return result.monthlySavings > 0;
}

/**
 * Get recommended plan ID based on hours per week
 */
export function getRecommendedPlanId(hoursPerWeek: number): string {
  // Rough estimate: 1h/week = ~4 searches/month
  const estimatedSearchesPerMonth = hoursPerWeek * 4;

  if (estimatedSearchesPerMonth <= 50) {
    return "consultor_agil"; // up to 50 searches
  } else if (estimatedSearchesPerMonth <= 300) {
    return "maquina"; // up to 300 searches
  } else {
    return "sala_guerra"; // up to 1000 searches
  }
}

// ============================================================================
// MESSAGING HELPERS
// ============================================================================

export interface ROIMessage {
  headline: string;
  tagline: string;
  explanation: string;
}

/**
 * Generate ROI messaging based on calculation
 */
export function getROIMessage(inputs: ROIInputs): ROIMessage {
  const result = calculateROI(inputs);

  if (result.roi >= 10) {
    return {
      headline: `ROI de ${result.formatted.roi}`,
      tagline: "Investimento se paga na primeira licitação ganha",
      explanation: `Economize ${result.formatted.monthlySavings}/mês vs. custo de busca manual (${result.formatted.manualSearchCostPerMonth}).`,
    };
  } else if (result.roi >= 5) {
    return {
      headline: `ROI de ${result.formatted.roi}`,
      tagline: "Economize milhares por ano",
      explanation: `Reduza custos de busca de ${result.formatted.manualSearchCostPerMonth} para ${result.formatted.smartlicPlanCost}/mês.`,
    };
  } else if (result.roi >= 2) {
    return {
      headline: `ROI de ${result.formatted.roi}`,
      tagline: "Investimento vale a pena",
      explanation: `Economize ${result.formatted.monthlySavings}/mês em tempo de busca manual.`,
    };
  } else {
    return {
      headline: "Economize Tempo, Não Apenas Dinheiro",
      tagline: "Mais tempo para preparar propostas vencedoras",
      explanation: `Reduza ${inputs.hoursPerWeek}h/semana de busca manual para apenas minutos com SmartLic.`,
    };
  }
}

/**
 * Generate time savings message
 */
export function getTimeSavingsMessage(hoursSavedPerMonth: number): string {
  if (hoursSavedPerMonth >= 40) {
    return `Economize ${Math.round(hoursSavedPerMonth)}h/mês (equivalente a 1 semana de trabalho)`;
  } else if (hoursSavedPerMonth >= 20) {
    return `Economize ${Math.round(hoursSavedPerMonth)}h/mês (meio período de trabalho)`;
  } else {
    return `Economize ${Math.round(hoursSavedPerMonth)}h/mês para focar em propostas`;
  }
}

/**
 * Generate payback message
 */
export function getPaybackMessage(paybackPeriodDays: number): string {
  if (paybackPeriodDays <= 7) {
    return "Investimento se paga na primeira semana";
  } else if (paybackPeriodDays <= 14) {
    return "Investimento se paga em 2 semanas";
  } else if (paybackPeriodDays <= 30) {
    return "Investimento se paga no primeiro mês";
  } else {
    return `Payback em ${Math.ceil(paybackPeriodDays)} dias`;
  }
}

// ============================================================================
// PRESET SCENARIOS (For Examples)
// ============================================================================

export const PRESET_SCENARIOS = {
  freelancer: {
    name: "Freelancer / Consultor",
    hoursPerWeek: 5,
    costPerHour: 150,
    planId: "consultor_agil" as const,
    description: "Busca ocasional para projetos específicos",
  },

  pme: {
    name: "Pequena/Média Empresa",
    hoursPerWeek: 10,
    costPerHour: 100,
    planId: "maquina" as const,
    description: "Busca regular semanal por oportunidades",
  },

  enterprise: {
    name: "Grande Empresa / Departamento Licitações",
    hoursPerWeek: 20,
    costPerHour: 80,
    planId: "sala_guerra" as const,
    description: "Busca diária por múltiplos setores",
  },
};

/**
 * Calculate ROI for a preset scenario
 */
export function getPresetScenarioROI(
  scenario: keyof typeof PRESET_SCENARIOS,
  planPrice: number
): ROIOutputs & { scenarioName: string; description: string } {
  const preset = PRESET_SCENARIOS[scenario];
  const roi = calculateROI({
    hoursPerWeek: preset.hoursPerWeek,
    costPerHour: preset.costPerHour,
    planPrice,
  });

  return {
    ...roi,
    scenarioName: preset.name,
    description: preset.description,
  };
}

// ============================================================================
// VALIDATION HELPERS
// ============================================================================

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

/**
 * Validate ROI calculator inputs
 */
export function validateInputs(inputs: Partial<ROIInputs>): ValidationResult {
  const errors: string[] = [];

  if (!inputs.hoursPerWeek || inputs.hoursPerWeek <= 0) {
    errors.push("Horas por semana deve ser maior que zero");
  }

  if (inputs.hoursPerWeek && inputs.hoursPerWeek > 168) {
    errors.push("Horas por semana não pode exceder 168 (horas totais na semana)");
  }

  if (!inputs.costPerHour || inputs.costPerHour <= 0) {
    errors.push("Custo por hora deve ser maior que zero");
  }

  if (inputs.costPerHour && inputs.costPerHour > 10000) {
    errors.push("Custo por hora parece muito alto. Verifique o valor.");
  }

  if (!inputs.planPrice || inputs.planPrice <= 0) {
    errors.push("Preço do plano deve ser maior que zero");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

// ============================================================================
// COMPARISON WITH COMPETITORS (Hypothetical)
// ============================================================================

export interface CompetitorCost {
  name: string;
  baseFee: number; // Monthly base fee
  perSearchFee: number; // Per-search fee
  estimatedTotalCost: number; // For typical usage (50 searches/month)
}

export const COMPETITOR_COSTS: CompetitorCost[] = [
  {
    name: "Plataforma A (Modelo Por Consulta)",
    baseFee: 99,
    perSearchFee: 10,
    estimatedTotalCost: 99 + 10 * 50, // R$ 599/month for 50 searches
  },
  {
    name: "Plataforma B (Mensalidade + Extras)",
    baseFee: 199,
    perSearchFee: 5,
    estimatedTotalCost: 199 + 5 * 50, // R$ 449/month for 50 searches
  },
  {
    name: "SmartLic (All-Inclusive)",
    baseFee: 149,
    perSearchFee: 0,
    estimatedTotalCost: 149, // R$ 149/month for up to 50 searches (consultor_agil)
  },
];

/**
 * Compare SmartLic cost with competitors for a given number of searches
 */
export function compareWithCompetitors(searchesPerMonth: number) {
  return COMPETITOR_COSTS.map((competitor) => ({
    ...competitor,
    totalCost:
      competitor.baseFee + competitor.perSearchFee * searchesPerMonth,
  })).sort((a, b) => a.totalCost - b.totalCost);
}

// ============================================================================
// EXPORT ALL
// ============================================================================

export default {
  DEFAULT_VALUES,
  PRESET_SCENARIOS,
  COMPETITOR_COSTS,
  calculateROI,
  getDefaultROI,
  hasPositiveROI,
  getRecommendedPlanId,
  getROIMessage,
  getTimeSavingsMessage,
  getPaybackMessage,
  getPresetScenarioROI,
  validateInputs,
  compareWithCompetitors,
  // Formatting utilities
  formatCurrency,
  formatROI,
  formatPercentage,
  formatDays,
  formatHours,
};
