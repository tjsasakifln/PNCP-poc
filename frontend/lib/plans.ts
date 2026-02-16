/**
 * Plan configuration for consistent naming across the frontend.
 *
 * This file centralizes all plan-related mappings to ensure consistency
 * between the backend plan_id values and user-facing display names.
 *
 * Backend Plan IDs (from quota.py PLAN_NAMES):
 * - free_trial: "FREE Trial"
 * - consultor_agil: "Consultor Agil"
 * - maquina: "Maquina"
 * - sala_guerra: "Sala de Guerra"
 */

export interface PlanConfig {
  id: string;
  displayName: string;
  displayNamePt: string;  // Portuguese marketing name
  price: string | null;
  badge: {
    bg: string;
    icon: string;
  };
  tier: number;  // For sorting/comparison
}

/**
 * Complete plan configuration mapping.
 * plan_id -> configuration object
 */
export const PLAN_CONFIGS: Record<string, PlanConfig> = {
  free_trial: {
    id: "free_trial",
    displayName: "FREE Trial",
    displayNamePt: "Gratuito",
    price: null,
    badge: {
      bg: "bg-gray-500",
      icon: "sparkles",
    },
    tier: 0,
  },
  consultor_agil: {
    id: "consultor_agil",
    displayName: "Consultor Agil",
    displayNamePt: "Consultor Agil",
    price: "R$ 297/mes",
    badge: {
      bg: "bg-blue-500",
      icon: "briefcase",
    },
    tier: 1,
  },
  maquina: {
    id: "maquina",
    displayName: "Maquina",
    displayNamePt: "Maquina",
    price: "R$ 597/mes",
    badge: {
      bg: "bg-green-500",
      icon: "cog",
    },
    tier: 2,
  },
  sala_guerra: {
    id: "sala_guerra",
    displayName: "Sala de Guerra",
    displayNamePt: "Sala de Guerra",
    price: "R$ 1.497/mes",
    badge: {
      bg: "bg-yellow-500",
      icon: "crown",
    },
    tier: 3,
  },
  smartlic_pro: {
    id: "smartlic_pro",
    displayName: "SmartLic Pro",
    displayNamePt: "SmartLic Pro",
    price: "R$ 1.999/mês",
    badge: {
      bg: "bg-brand-navy",
      icon: "star",
    },
    tier: 4,
  },
};

/**
 * Legacy plan ID mapping for backwards compatibility.
 * Maps old plan IDs to new ones.
 */
const LEGACY_PLAN_MAPPING: Record<string, string> = {
  free: "free_trial",
  legacy: "free_trial",
  pack_5: "consultor_agil",
  pack_10: "consultor_agil",
  pack_20: "maquina",
  monthly: "maquina",
  annual: "sala_guerra",
  master: "sala_guerra",
};

/**
 * Normalize a plan_id, handling legacy values.
 * @param planId - The plan ID from backend (may be legacy)
 * @returns Normalized plan ID (one of: free_trial, consultor_agil, maquina, sala_guerra)
 */
export function normalizePlanId(planId: string | null | undefined): string {
  if (!planId) return "free_trial";

  // Check if it's a legacy plan ID
  const normalized = LEGACY_PLAN_MAPPING[planId];
  if (normalized) return normalized;

  // Check if it's already a valid plan ID
  if (PLAN_CONFIGS[planId]) return planId;

  // Default to free_trial for unknown plans
  return "free_trial";
}

/**
 * Get the user-facing display name for a plan.
 * Uses Portuguese marketing names.
 *
 * @param planId - The plan ID (will be normalized if legacy)
 * @param backendName - Optional name from backend (fallback)
 * @returns User-friendly plan name in Portuguese
 */
export function getPlanDisplayName(planId: string | null | undefined, backendName?: string): string {
  const normalizedId = normalizePlanId(planId);
  const config = PLAN_CONFIGS[normalizedId];

  if (config) {
    return config.displayNamePt;
  }

  // Fallback to backend name if provided
  if (backendName) {
    // Clean up common backend names
    if (backendName.toLowerCase() === "free trial" || backendName === "FREE Trial") {
      return "Gratuito";
    }
    return backendName;
  }

  return "Gratuito";
}

/**
 * Get the plan configuration object.
 * @param planId - The plan ID (will be normalized if legacy)
 * @returns Plan configuration or default free_trial config
 */
export function getPlanConfig(planId: string | null | undefined): PlanConfig {
  const normalizedId = normalizePlanId(planId);
  return PLAN_CONFIGS[normalizedId] || PLAN_CONFIGS.free_trial;
}

/**
 * Check if plan A is higher tier than plan B.
 */
export function isHigherTier(planA: string, planB: string): boolean {
  const configA = getPlanConfig(planA);
  const configB = getPlanConfig(planB);
  return configA.tier > configB.tier;
}

/**
 * Get upgrade suggestion based on current plan.
 */
export function getUpgradeSuggestion(currentPlanId: string): string | null {
  const config = getPlanConfig(currentPlanId);

  switch (config.id) {
    case "free_trial":
      return "smartlic_pro";
    case "consultor_agil":
      return "smartlic_pro";
    case "maquina":
      return "smartlic_pro";
    case "sala_guerra":
      return "smartlic_pro";
    default:
      return null;
  }
}
