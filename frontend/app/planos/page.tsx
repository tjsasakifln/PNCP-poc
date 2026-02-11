"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";
import { PlanToggle, BillingPeriod } from "../../components/subscriptions/PlanToggle";
import {
  calculateROI,
  DEFAULT_VALUES,
  formatCurrency,
  getROIMessage,
  type ROIInputs,
} from '@/lib/copy/roi';

interface Plan {
  id: string;
  name: string;
  description: string;
  max_searches: number | null;
  price_brl: number;
  duration_days: number | null;
}

interface UserProfile {
  plan_id?: string;
  plan_name?: string;
  is_admin?: boolean;
}

// Plan hierarchy for upgrade/downgrade logic (lower index = lower tier)
const PLAN_HIERARCHY = [
  "free",
  "free_trial",
  "pack_5",
  "pack_10",
  "pack_20",
  "consultor_agil",
  "monthly",
  "maquina",
  "annual",
  "sala_guerra",
  "master",
];

// Plans that should be hidden from public listing (only truly internal plans)
const HIDDEN_PLANS = ["free", "master"];

// Free tier plan IDs
const FREE_TIER_IDS = ["free", "free_trial"];

// Plan capabilities for feature display (matches backend quota.py PLAN_CAPABILITIES)
interface PlanFeatures {
  maxHistoryDays: number;
  allowExcel: boolean;
  maxRequestsPerMonth: number;
  maxRequestsPerMin: number;
  aiLevel: string;  // Display text for AI summary level
}

const PLAN_FEATURES: Record<string, PlanFeatures> = {
  free_trial: {
    maxHistoryDays: 7,
    allowExcel: false,
    maxRequestsPerMonth: 3,
    maxRequestsPerMin: 2,
    aiLevel: "Basico",
  },
  consultor_agil: {
    maxHistoryDays: 30,
    allowExcel: false,
    maxRequestsPerMonth: 50,
    maxRequestsPerMin: 10,
    aiLevel: "Basico",
  },
  maquina: {
    maxHistoryDays: 365,
    allowExcel: true,
    maxRequestsPerMonth: 300,
    maxRequestsPerMin: 30,
    aiLevel: "Detalhado",
  },
  sala_guerra: {
    maxHistoryDays: 1825,  // 5 years
    allowExcel: true,
    maxRequestsPerMonth: 1000,
    maxRequestsPerMin: 60,
    aiLevel: "Prioritário",
  },
};

/**
 * Format history days as human-readable string.
 */
function formatHistoryDays(days: number): string {
  if (days <= 7) return `${days} dias`;
  if (days <= 30) return "30 dias";
  if (days <= 365) return "1 ano";
  return "5 anos";
}

/**
 * Check if user is on a free tier plan.
 * Free users should see all plans for initial subscription.
 */
function isFreeUser(userProfile?: UserProfile | null): boolean {
  if (!userProfile) return true; // Not logged in = treat as free
  if (!userProfile.plan_id) return true;
  return FREE_TIER_IDS.includes(userProfile.plan_id);
}

/**
 * Get plan relation (upgrade, downgrade, or current) based on hierarchy.
 */
function getPlanRelation(
  currentPlanId: string,
  targetPlanId: string
): "current" | "upgrade" | "downgrade" {
  const currentIndex = PLAN_HIERARCHY.indexOf(currentPlanId);
  const targetIndex = PLAN_HIERARCHY.indexOf(targetPlanId);

  // If plan not found in hierarchy, treat as neutral
  if (currentIndex === -1 || targetIndex === -1) return "upgrade";

  if (targetIndex === currentIndex) return "current";
  if (targetIndex > currentIndex) return "upgrade";
  return "downgrade";
}

/**
 * Check if user has privileged access (admin, master, owner).
 * Privileged users should see a different view on the pricing page.
 *
 * Checks multiple sources to ensure no privileged user sees upgrade prompts:
 * - isAdmin flag from AuthContext (profiles.is_admin = true)
 * - plan_id for master-level plans (master, sala_guerra)
 * - plan_name containing admin/master keywords
 *
 * @param isAdmin - Boolean from AuthContext indicating admin status
 * @param userProfile - User profile data from /me endpoint (optional)
 * @returns true if user has any privileged access level
 */
function isPrivilegedUser(isAdmin: boolean, userProfile?: UserProfile | null): boolean {
  // Check explicit admin flag from AuthContext
  if (isAdmin) return true;

  // Check profile-based privileges
  if (userProfile) {
    // Check is_admin from profile (redundant but explicit)
    if (userProfile.is_admin === true) return true;

    // Check plan_id for master-level plans
    const privilegedPlanIds = ["master", "sala_guerra"];
    if (userProfile.plan_id && privilegedPlanIds.includes(userProfile.plan_id)) {
      return true;
    }

    // Check plan_name for master-level indicators (case-insensitive)
    const privilegedPlanNames = ["master", "sala de guerra", "admin", "owner"];
    if (userProfile.plan_name) {
      const planNameLower = userProfile.plan_name.toLowerCase();
      if (privilegedPlanNames.some((name) => planNameLower.includes(name))) {
        return true;
      }
    }
  }

  return false;
}

export default function PlanosPage() {
  const { session, user, isAdmin, loading: authLoading } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("monthly");
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);

  // ROI Calculator State
  const [hoursPerWeek, setHoursPerWeek] = useState(DEFAULT_VALUES.hoursPerWeek);
  const [costPerHour, setCostPerHour] = useState(DEFAULT_VALUES.costPerHour);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);

  // Get selected plan object and price
  const selectedPlan = plans.find((p) => p.id === selectedPlanId) || plans.find((p) => p.id === 'maquina') || plans[0];
  const selectedPlanPrice = billingPeriod === 'annual'
    ? selectedPlan?.price_brl * 9.6
    : selectedPlan?.price_brl || 149;

  const [roiResult, setRoiResult] = useState(
    calculateROI({
      hoursPerWeek: DEFAULT_VALUES.hoursPerWeek,
      costPerHour: DEFAULT_VALUES.costPerHour,
      planPrice: 149, // Default to consultor_agil price
    })
  );

  // Initialize selected plan when plans load
  useEffect(() => {
    if (plans.length > 0 && !selectedPlanId) {
      // Default to "maquina" (most popular) if available
      const defaultPlan = plans.find((p) => p.id === 'maquina') || plans[0];
      setSelectedPlanId(defaultPlan.id);
    }
  }, [plans, selectedPlanId]);

  // Calculate ROI on input change
  useEffect(() => {
    if (!selectedPlan) return;
    const inputs: ROIInputs = {
      hoursPerWeek,
      costPerHour,
      planPrice: selectedPlanPrice,
    };
    setRoiResult(calculateROI(inputs));
  }, [hoursPerWeek, costPerHour, selectedPlan, selectedPlanPrice]);

  const roiMessage = getROIMessage({
    hoursPerWeek,
    costPerHour,
    planPrice: selectedPlanPrice,
  });

  // Check URL params for success/cancelled
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("success")) setStatusMsg("Pagamento realizado com sucesso! Seu plano está ativo.");
    if (params.get("cancelled")) setStatusMsg("Pagamento cancelado.");
  }, []);

  // Fetch user profile to check privileges (master plan, etc.)
  useEffect(() => {
    const fetchUserProfile = async () => {
      if (!session?.access_token) {
        setUserProfile(null);
        setProfileLoading(false);
        return;
      }

      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
        const res = await fetch(`${backendUrl}/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setUserProfile(data);
        }
      } catch {
        // Ignore errors - will just show pricing page
      } finally {
        setProfileLoading(false);
      }
    };

    fetchUserProfile();
  }, [session?.access_token]);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
      const res = await fetch(`${backendUrl}/plans`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      // Hide free, master, and sala_guerra from public listing
      setPlans(data.plans.filter((p: Plan) => !HIDDEN_PLANS.includes(p.id)));
    } catch {
      setPlans([]);
    } finally {
      setLoading(false);
    }
  };

  // Determine if user is privileged (admin, master, owner)
  const userIsPrivileged = isPrivilegedUser(isAdmin, userProfile);

  // Determine if user is on a free plan (no paid subscription)
  const userIsFree = isFreeUser(userProfile);

  // Current plan ID for upgrade/downgrade comparison
  const currentPlanId = userProfile?.plan_id || "free";

  // Get current plan name for display
  const getCurrentPlanName = () => {
    if (!userProfile?.plan_name) return "";
    return userProfile.plan_name;
  };

  // Get button text and style based on plan relation
  const getButtonConfig = (planId: string) => {
    if (userIsFree) {
      return { text: "Assinar", variant: "primary" as const };
    }

    const relation = getPlanRelation(currentPlanId, planId);
    switch (relation) {
      case "current":
        return { text: "Seu plano atual", variant: "current" as const };
      case "upgrade":
        return { text: "Fazer upgrade", variant: "primary" as const };
      case "downgrade":
        return { text: "Fazer downgrade", variant: "secondary" as const };
      default:
        return { text: "Assinar", variant: "primary" as const };
    }
  };

  // Get display role for privileged users
  const getPrivilegedRole = (): { title: string; description: string; showAdminLink: boolean } => {
    if (isAdmin || userProfile?.is_admin) {
      return {
        title: "Você é administrador do sistema",
        description: "Como administrador, você possui acesso completo a todas as funcionalidades do sistema, sem restrições de plano ou créditos.",
        showAdminLink: true,
      };
    }
    if (userProfile?.plan_id === "sala_guerra" || userProfile?.plan_name?.toLowerCase().includes("sala de guerra")) {
      return {
        title: "Você possui o plano Sala de Guerra",
        description: "Com o plano Sala de Guerra, você possui acesso completo a todas as funcionalidades do sistema, sem restrições de créditos.",
        showAdminLink: false,
      };
    }
    if (userProfile?.plan_id === "master" || userProfile?.plan_name?.toLowerCase().includes("master")) {
      return {
        title: "Você possui acesso Master",
        description: "Com acesso Master, você possui acesso completo a todas as funcionalidades do sistema, sem restrições de plano ou créditos.",
        showAdminLink: false,
      };
    }
    // Fallback for any other privileged user
    return {
      title: "Você possui acesso privilegiado",
      description: "Você possui acesso completo a todas as funcionalidades do sistema, sem restrições de plano ou créditos.",
      showAdminLink: false,
    };
  };

  // Admin/Master users see a different view
  if (!authLoading && !profileLoading && userIsPrivileged) {
    const roleInfo = getPrivilegedRole();
    return (
      <div className="min-h-screen bg-[var(--canvas)] py-12 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--brand-blue)]/10 flex items-center justify-center">
              <svg
              role="img"
              aria-label="Ícone" className="w-8 h-8 text-[var(--brand-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-3">
              {roleInfo.title}
            </h1>
            <p className="text-[var(--ink-secondary)] mb-6">
              {roleInfo.description}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {roleInfo.showAdminLink && (
                <Link
                  href="/admin"
                  className="px-6 py-3 bg-[var(--brand-navy)] text-white rounded-button font-semibold
                             hover:bg-[var(--brand-blue)] transition-colors"
                >
                  Gerenciar usuários
                </Link>
              )}
              <Link
                href="/buscar"
                className="px-6 py-3 border border-[var(--border)] text-[var(--ink)] rounded-button font-semibold
                           hover:bg-[var(--surface-1)] transition-colors"
              >
                Voltar para buscas
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const handleCheckout = async (planId: string) => {
    if (!session) {
      window.location.href = "/login";
      return;
    }
    setCheckoutLoading(planId);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
      const res = await fetch(`${backendUrl}/checkout?plan_id=${planId}&billing_period=${billingPeriod}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao iniciar pagamento");
      }
      const data = await res.json();
      window.location.href = data.checkout_url;
    } catch (err) {
      alert(err instanceof Error ? err.message : "Erro ao iniciar pagamento");
    } finally {
      setCheckoutLoading(null);
    }
  };

  const formatPrice = (val: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val);

  const isPopular = (id: string) => id === "maquina";

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-12 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-display font-bold text-[var(--ink)] mb-3">
            {userIsFree ? "Escolha seu plano" : "Gerenciar sua assinatura"}
          </h1>
          <p className="text-[var(--ink-secondary)] max-w-lg mx-auto">
            {userIsFree
              ? "Comece gratis com 3 buscas. Escolha um plano para acesso completo ao monitoramento de licitacoes."
              : `Voce esta no plano ${getCurrentPlanName()}. Veja as opcoes de upgrade ou downgrade abaixo.`}
          </p>

          {/* Billing Period Toggle - Monthly/Annual */}
          <div className="mt-6">
            <PlanToggle value={billingPeriod} onChange={setBillingPeriod} />
          </div>
        </div>

        {statusMsg && (
          <div className="mb-8 p-4 bg-[var(--success-subtle)] text-[var(--success)] rounded-card text-center">
            {statusMsg}
          </div>
        )}

        {/* Current Plan Banner for paying users */}
        {!userIsFree && !loading && userProfile && (
          <div className="mb-8 p-4 bg-[var(--brand-blue)]/10 border border-[var(--brand-blue)]/30 rounded-card">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <span className="text-sm text-[var(--ink-secondary)]">Seu plano atual:</span>
                <span className="ml-2 font-semibold text-[var(--ink)]">{getCurrentPlanName()}</span>
              </div>
              <Link
                href="/conta"
                className="text-sm text-[var(--brand-blue)] hover:underline"
              >
                Ver detalhes da conta
              </Link>
            </div>
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-72 bg-[var(--surface-1)] rounded-card animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {plans.map((plan) => {
              const buttonConfig = getButtonConfig(plan.id);
              const isCurrent = !userIsFree && getPlanRelation(currentPlanId, plan.id) === "current";
              const isDowngrade = !userIsFree && getPlanRelation(currentPlanId, plan.id) === "downgrade";

              return (
                <div
                  key={plan.id}
                  className={`relative p-6 bg-[var(--surface-0)] border rounded-card
                    ${isCurrent
                      ? "border-[var(--success)] ring-2 ring-[var(--success)]/20"
                      : isPopular(plan.id)
                        ? "border-[var(--brand-blue)] shadow-lg"
                        : "border-[var(--border)]"
                    }`}
                >
                  {/* Current Plan Badge */}
                  {isCurrent && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5
                                    bg-[var(--success)] text-white text-xs font-semibold rounded-full">
                      Seu plano atual
                    </div>
                  )}

                  {/* Popular Badge - only show if not current */}
                  {isPopular(plan.id) && !isCurrent && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5
                                    bg-[var(--brand-blue)] text-white text-xs font-semibold rounded-full">
                      Mais popular
                    </div>
                  )}

                  <h3 className="text-lg font-semibold text-[var(--ink)] mb-1">{plan.name}</h3>
                  <p className="text-sm text-[var(--ink-secondary)] mb-4">{plan.description}</p>

                  <div className="mb-6">
                    <span className="text-3xl font-data font-bold text-[var(--ink)]">
                      {billingPeriod === "annual"
                        ? formatPrice(plan.price_brl * 9.6)
                        : formatPrice(plan.price_brl)}
                    </span>
                    <span className="text-sm text-[var(--ink-muted)]">
                      {billingPeriod === "annual" ? "/ano" : "/mês"}
                    </span>
                    {billingPeriod === "annual" && (
                      <div className="mt-1">
                        <span className="text-sm text-[var(--ink-secondary)]">
                          Equivalente a {formatPrice((plan.price_brl * 9.6) / 12)}/mês
                        </span>
                      </div>
                    )}
                  </div>

                  <ul className="space-y-2 mb-6 text-sm text-[var(--ink-secondary)]">
                    {/* Dynamic features based on plan capabilities */}
                    {(() => {
                      const features = PLAN_FEATURES[plan.id] || PLAN_FEATURES.consultor_agil;
                      return (
                        <>
                          {/* Searches per month */}
                          <li className="flex items-center gap-2">
                            <span className="text-[var(--success)]">&#10003;</span>
                            {`${features.maxRequestsPerMonth} buscas/mês`}
                          </li>
                          {/* History period */}
                          <li className="flex items-center gap-2">
                            <span className="text-[var(--success)]">&#10003;</span>
                            Histórico de {formatHistoryDays(features.maxHistoryDays)}
                          </li>
                          {/* Excel export - show as available or blocked */}
                          <li className="flex items-center gap-2">
                            {features.allowExcel ? (
                              <>
                                <span className="text-[var(--success)]">&#10003;</span>
                                <span>Download Excel</span>
                              </>
                            ) : (
                              <>
                                <span className="text-[var(--ink-muted)]">&#10007;</span>
                                <span className="text-[var(--ink-muted)] line-through">Download Excel</span>
                              </>
                            )}
                          </li>
                          {/* AI summary level */}
                          <li className="flex items-center gap-2">
                            <span className="text-[var(--success)]">&#10003;</span>
                            IA {features.aiLevel}
                          </li>
                          {/* Processing priority */}
                          <li className="flex items-center gap-2">
                            <span className="text-[var(--success)]">&#10003;</span>
                            {plan.id === "sala_guerra"
                              ? "Processamento prioritário"
                              : plan.id === "maquina"
                                ? "Processamento rápido"
                                : "Processamento padrão"}
                          </li>
                        </>
                      );
                    })()}
                  </ul>

                  <button
                    onClick={() => !isCurrent && handleCheckout(plan.id)}
                    disabled={checkoutLoading === plan.id || isCurrent}
                    className={`w-full py-3 rounded-button font-semibold transition-colors
                      disabled:cursor-not-allowed
                      ${isCurrent
                        ? "bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/30"
                        : buttonConfig.variant === "primary" || (isPopular(plan.id) && !isDowngrade)
                          ? "bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] disabled:opacity-50"
                          : isDowngrade
                            ? "border border-[var(--warning)] text-[var(--warning)] hover:bg-[var(--warning)]/10"
                            : "border border-[var(--border)] text-[var(--ink)] hover:bg-[var(--surface-1)] disabled:opacity-50"
                      }`}
                  >
                    {checkoutLoading === plan.id ? "Redirecionando..." : buttonConfig.text}
                  </button>

                  {/* Downgrade warning */}
                  {isDowngrade && (
                    <p className="mt-2 text-xs text-[var(--warning)] text-center">
                      Voce perdera recursos do seu plano atual
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ROI Calculator Section */}
        <div className="mt-16 max-w-4xl mx-auto">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-8">
            <h2 className="text-3xl font-bold text-[var(--ink)] mb-2 text-center">
              Calcule sua Economia
            </h2>
            <p className="text-center text-[var(--ink-secondary)] mb-8">
              Calcule quanto você economiza com o SmartLic vs. busca manual
            </p>

            {/* Calculator Inputs */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {/* Hours per Week Input */}
              <div>
                <label
                  htmlFor="hours-per-week"
                  className="block text-sm font-medium text-[var(--ink)] mb-2"
                >
                  Horas gastas por semana em buscas manuais
                </label>
                <input
                  id="hours-per-week"
                  type="number"
                  min="1"
                  max="168"
                  value={hoursPerWeek}
                  onChange={(e) => setHoursPerWeek(Number(e.target.value))}
                  className="w-full px-4 py-3 bg-[var(--surface-0)] border border-[var(--border)] rounded-button text-[var(--ink)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue)]"
                />
              </div>

              {/* Cost per Hour Input */}
              <div>
                <label
                  htmlFor="cost-per-hour"
                  className="block text-sm font-medium text-[var(--ink)] mb-2"
                >
                  Custo/hora do seu tempo (R$)
                </label>
                <input
                  id="cost-per-hour"
                  type="number"
                  min="1"
                  max="10000"
                  value={costPerHour}
                  onChange={(e) => setCostPerHour(Number(e.target.value))}
                  className="w-full px-4 py-3 bg-[var(--surface-0)] border border-[var(--border)] rounded-button text-[var(--ink)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue)]"
                />
              </div>
            </div>

            {/* Plan Selector - Dynamic from real plans */}
            <div className="mb-8">
              <label className="block text-sm font-medium text-[var(--ink)] mb-3">
                Selecione o plano SmartLic
              </label>
              <div className="grid md:grid-cols-3 gap-4">
                {plans
                  .filter((p) => ['consultor_agil', 'maquina', 'sala_guerra'].includes(p.id))
                  .map((plan) => {
                    const features = PLAN_FEATURES[plan.id] || PLAN_FEATURES.consultor_agil;
                    const isSelected = selectedPlanId === plan.id;
                    const planPrice = billingPeriod === 'annual'
                      ? plan.price_brl * 9.6
                      : plan.price_brl;

                    return (
                      <button
                        key={plan.id}
                        onClick={() => setSelectedPlanId(plan.id)}
                        className={`px-6 py-4 rounded-card border-2 transition-all ${
                          isSelected
                            ? 'border-[var(--brand-blue)] bg-[var(--brand-blue)]/10 text-[var(--brand-blue)]'
                            : 'border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] hover:border-[var(--brand-blue)]/50'
                        }`}
                      >
                        <div className="font-semibold mb-1">
                          {plan.name}
                          {plan.id === 'maquina' && (
                            <span className="ml-2 text-xs bg-[var(--brand-blue)] text-white px-2 py-0.5 rounded-full">
                              Popular
                            </span>
                          )}
                        </div>
                        <div className="text-2xl font-bold mb-1">
                          {formatPrice(planPrice)}
                        </div>
                        <div className="text-xs text-[var(--ink-secondary)]">
                          {billingPeriod === 'annual' ? '/ano' : '/mês'}
                        </div>
                        <div className="text-xs text-[var(--ink-muted)] mt-1">
                          até {features.maxRequestsPerMonth} buscas/mês
                        </div>
                      </button>
                    );
                  })}
              </div>
              {billingPeriod === 'annual' && (
                <p className="text-xs text-[var(--ink-muted)] text-center mt-2">
                  Preços com 20% de desconto (12 meses pelo preço de 9.6)
                </p>
              )}
            </div>

            {/* Divider */}
            <div className="border-t border-[var(--border)] my-8"></div>

            {/* ROI Results */}
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div className="bg-[var(--error)]/10 border border-[var(--error)]/30 rounded-card p-6">
                <p className="text-sm text-[var(--ink-secondary)] mb-1">
                  💸 Custo Mensal da Busca Manual
                </p>
                <p className="text-3xl font-bold text-[var(--error)]">
                  {roiResult.formatted.manualSearchCostPerMonth}
                </p>
                <p className="text-xs text-[var(--ink-muted)] mt-2">
                  {hoursPerWeek}h/semana × {formatCurrency(costPerHour)}/h × 4 semanas
                </p>
              </div>

              <div className="bg-[var(--success)]/10 border border-[var(--success)]/30 rounded-card p-6">
                <p className="text-sm text-[var(--ink-secondary)] mb-1">
                  💸 Plano SmartLic ({selectedPlan?.name || 'Consultor Ágil'})
                </p>
                <p className="text-3xl font-bold text-[var(--success)]">
                  {roiResult.formatted.smartlicPlanCost}
                </p>
                <p className="text-xs text-[var(--ink-muted)] mt-2">
                  {billingPeriod === 'annual'
                    ? `${formatPrice(selectedPlanPrice / 12)}/mês (pago anualmente)`
                    : 'Fixo mensal, sem taxas ocultas'}
                </p>
              </div>
            </div>

            <div className="bg-[var(--brand-blue)]/10 border border-[var(--brand-blue)]/30 rounded-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-[var(--ink-secondary)] mb-1">
                    ✅ Economia {billingPeriod === 'annual' ? 'Anual' : 'Mensal'}
                  </p>
                  <p className="text-4xl font-bold text-[var(--brand-blue)]">
                    {roiResult.formatted.monthlySavings}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-[var(--ink-secondary)] mb-1">📊 ROI</p>
                  <p className="text-4xl font-bold text-[var(--brand-blue)]">
                    {roiResult.formatted.roi}
                  </p>
                </div>
              </div>
              <div className="border-t border-[var(--brand-blue)]/20 pt-4">
                <p className="font-semibold text-[var(--ink)] mb-2">{roiMessage.headline}</p>
                <p className="text-sm text-[var(--ink-secondary)]">{roiMessage.explanation}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center">
          <Link href="/buscar" className="text-sm text-[var(--ink-muted)] hover:underline">
            Voltar para buscas
          </Link>
        </div>
      </div>
    </div>
  );
}
