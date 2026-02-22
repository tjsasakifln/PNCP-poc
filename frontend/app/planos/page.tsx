"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import LandingNavbar from "../components/landing/LandingNavbar";
import Link from "next/link";
import { useAnalytics } from "../../hooks/useAnalytics";
import { getUserFriendlyError } from "../../lib/error-messages";
import { PlanToggle, BillingPeriod } from "../../components/subscriptions/PlanToggle";
import { formatCurrency } from '@/lib/copy/roi';
import { usePlan } from "../../hooks/usePlan";
import { toast } from "sonner";

interface UserProfile {
  plan_id?: string;
  plan_name?: string;
  is_admin?: boolean;
}

// GTM-002: Single plan pricing by billing period
const PRICING: Record<BillingPeriod, { monthly: number; total: number; period: string; discount?: number }> = {
  monthly: { monthly: 1999, total: 1999, period: "mês" },
  semiannual: { monthly: 1799, total: 10794, period: "semestre", discount: 10 },
  annual: { monthly: 1599, total: 19188, period: "ano", discount: 20 },
};

// GTM-002: Features list — ALL enabled (no comparison needed)
const FEATURES = [
  { text: "1.000 análises por mês", detail: "Avalie oportunidades em todos os 27 estados" },
  { text: "Exportação Excel completa", detail: "Relatórios detalhados para sua equipe" },
  { text: "Pipeline de acompanhamento", detail: "Gerencie oportunidades do início ao fim" },
  { text: "Resumos executivos com IA avançada", detail: "Análise estratégica de cada oportunidade" },
  { text: "5 anos de histórico", detail: "Acesso a oportunidades desde 2021" },
  { text: "15 setores e 27 estados", detail: "Cobertura nacional integrada de fontes oficiais" },
  { text: "Filtragem com 1.000+ regras", detail: "Precisão setorial para seu mercado" },
];

// FAQ items
const FAQ_ITEMS = [
  {
    question: "Posso cancelar a qualquer momento?",
    answer: "Sim. Sem contrato de fidelidade, mesmo no acesso anual. Cancele quando quiser e mantenha o acesso até o fim do período já pago.",
  },
  {
    question: "Existe contrato de fidelidade?",
    answer: "Não. O SmartLic Pro funciona como acesso recorrente. Você escolhe o nível de compromisso e pode alterar ou cancelar livremente.",
  },
  {
    question: "O que acontece se eu cancelar?",
    answer: "Você mantém acesso completo até o fim do período atual. Depois, sua conta volta ao modo de avaliação com 3 análises.",
  },
  {
    question: "Como funciona a cobrança semestral e anual?",
    answer: "No acesso semestral, o valor é cobrado a cada 6 meses com 10% de economia. No anual, a cada 12 meses com 20% de economia. Stripe processa tudo com segurança.",
  },
];

type UserStatus = "subscriber" | "privileged" | "trial" | "trial_expired" | "anonymous";

export default function PlanosPage() {
  const { session, user, isAdmin, loading: authLoading } = useAuth();
  const { planInfo, loading: planLoading } = usePlan();
  const { trackEvent } = useAnalytics();
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [stripeRedirecting, setStripeRedirecting] = useState(false);
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("monthly");
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);

  // Check URL params
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("success")) setStatusMsg("Acesso ativado com sucesso! Bem-vindo ao SmartLic Pro.");
    if (params.get("cancelled")) setStatusMsg("Processo cancelado.");
    // Pre-select billing period from URL
    const billing = params.get("billing");
    if (billing === "semiannual" || billing === "annual") setBillingPeriod(billing);
  }, []);

  useEffect(() => {
    trackEvent("plan_page_viewed", { source: "url" });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch user profile
  useEffect(() => {
    const fetchUserProfile = async () => {
      if (!session?.access_token) {
        setUserProfile(null);
        setProfileLoading(false);
        return;
      }
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
        const res = await fetch(`${backendUrl}/v1/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (res.ok) setUserProfile(await res.json());
      } catch {
        // Ignore
      } finally {
        setProfileLoading(false);
      }
    };
    fetchUserProfile();
  }, [session?.access_token]);

  // UX-339: Derive user status for contextual banner
  const userStatus: UserStatus = useMemo(() => {
    if (!session || !user) return "anonymous";
    // Active subscriber
    if (planInfo?.plan_id === "smartlic_pro" && planInfo?.subscription_status === "active") return "subscriber";
    // Admin/master/privileged
    if (isAdmin || userProfile?.is_admin || userProfile?.plan_id === "master") return "privileged";
    // Trial expired
    if (planInfo?.plan_id === "free_trial" && planInfo?.subscription_status === "expired") return "trial_expired";
    // Trial active (default for logged-in users with free_trial)
    if (planInfo?.plan_id === "free_trial") return "trial";
    // Fallback: if we have a session but unknown plan, treat as trial
    return "trial";
  }, [session, user, planInfo, isAdmin, userProfile]);

  // UX-339: Calculate trial days remaining
  const trialDaysRemaining = useMemo(() => {
    if (!planInfo?.trial_expires_at) return null;
    const expiryDate = new Date(planInfo.trial_expires_at);
    const now = new Date();
    const diffTime = expiryDate.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
  }, [planInfo?.trial_expires_at]);

  const currentPricing = PRICING[billingPeriod];
  const isAlreadyPro = userStatus === "subscriber";
  const hasFullAccess = userStatus === "subscriber" || userStatus === "privileged";

  // UX-339: Billing portal redirect for active subscribers
  const handleManageSubscription = useCallback(async () => {
    if (!session?.access_token) return;
    setPortalLoading(true);
    try {
      const res = await fetch("/api/billing-portal", {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error("Erro ao abrir portal");
      const data = await res.json();
      window.location.href = data.url;
    } catch (err) {
      toast.error(getUserFriendlyError(err));
    } finally {
      setPortalLoading(false);
    }
  }, [session?.access_token]);

  const handleCheckout = async () => {
    if (!session) {
      window.location.href = "/login";
      return;
    }
    setCheckoutLoading(true);
    trackEvent("checkout_initiated", {
      plan_id: "smartlic_pro",
      billing_period: billingPeriod,
      source: "planos_page",
    });
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
      const res = await fetch(
        `${backendUrl}/v1/checkout?plan_id=smartlic_pro&billing_period=${billingPeriod}`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${session.access_token}` },
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao iniciar processo");
      }
      const data = await res.json();
      setStripeRedirecting(true);
      window.location.href = data.checkout_url;
    } catch (err) {
      trackEvent("checkout_failed", {
        plan_id: "smartlic_pro",
        billing_period: billingPeriod,
        error: err instanceof Error ? err.message : "unknown",
      });
      toast.error(getUserFriendlyError(err));
      setCheckoutLoading(false);
      setStripeRedirecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--canvas)]">
      <LandingNavbar />

      {/* Stripe redirect overlay */}
      {stripeRedirecting && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[var(--canvas)]/80 backdrop-blur-sm">
          <div className="backdrop-blur-xl bg-white/70 dark:bg-gray-900/60 border border-white/20 dark:border-white/10 rounded-card p-8 text-center shadow-glass max-w-sm mx-4">
            <div className="w-12 h-12 mx-auto mb-4 border-4 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
            <h2 className="text-lg font-semibold text-[var(--ink)] mb-2">
              Redirecionando para o checkout
            </h2>
            <p className="text-sm text-[var(--ink-secondary)]">
              Você será redirecionado para o Stripe para concluir de forma segura.
            </p>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto py-12 px-4">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-display font-bold text-[var(--ink)] mb-4">
            Escolha Seu Nível de Compromisso
          </h1>
          <p className="text-lg text-[var(--ink-secondary)] max-w-2xl mx-auto">
            O SmartLic é um só. Você decide com que frequência quer investir em inteligência competitiva.
          </p>
        </div>

        {statusMsg && (
          <div className="mb-8 p-4 bg-[var(--success-subtle)] backdrop-blur-sm text-[var(--success)] rounded-card text-center">
            {statusMsg}
          </div>
        )}

        {/* UX-339: Contextual status banner for logged-in users */}
        {userStatus === "subscriber" && (
          <div data-testid="status-banner-subscriber" className="mb-8 p-4 bg-emerald-50 dark:bg-emerald-950/30 backdrop-blur-sm border border-emerald-200 dark:border-emerald-800 rounded-card text-center">
            <p className="font-semibold text-emerald-800 dark:text-emerald-200">
              Você possui acesso completo ao SmartLic
            </p>
            <button
              onClick={handleManageSubscription}
              disabled={portalLoading}
              className="mt-1 text-sm text-emerald-600 dark:text-emerald-400 hover:underline disabled:opacity-50"
            >
              {portalLoading ? "Abrindo..." : "Gerenciar assinatura"}
            </button>
          </div>
        )}

        {userStatus === "privileged" && (
          <div data-testid="status-banner-privileged" className="mb-8 p-4 bg-emerald-50 dark:bg-emerald-950/30 backdrop-blur-sm border border-emerald-200 dark:border-emerald-800 rounded-card text-center">
            <p className="font-semibold text-emerald-800 dark:text-emerald-200">
              Você possui acesso completo ao SmartLic
            </p>
            <Link href="/buscar" className="mt-1 text-sm text-emerald-600 dark:text-emerald-400 hover:underline">
              Iniciar análise
            </Link>
          </div>
        )}

        {userStatus === "trial" && (
          <div data-testid="status-banner-trial" className="mb-8 p-4 bg-blue-50 dark:bg-blue-950/30 backdrop-blur-sm border border-blue-200 dark:border-blue-800 rounded-card text-center">
            <p className="font-semibold text-blue-800 dark:text-blue-200">
              Você está no período de avaliação{trialDaysRemaining !== null ? ` (${trialDaysRemaining} ${trialDaysRemaining === 1 ? "dia restante" : "dias restantes"})` : ""}
            </p>
            <p className="text-sm text-blue-600 dark:text-blue-400">
              Escolha seu compromisso para continuar após o trial
            </p>
          </div>
        )}

        {userStatus === "trial_expired" && (
          <div data-testid="status-banner-expired" className="mb-8 p-4 bg-amber-50 dark:bg-amber-950/30 backdrop-blur-sm border border-amber-200 dark:border-amber-800 rounded-card text-center">
            <p className="font-semibold text-amber-800 dark:text-amber-200">
              Seu período de avaliação encerrou
            </p>
            <p className="text-sm text-amber-600 dark:text-amber-400">
              Escolha um compromisso para voltar a ter acesso
            </p>
          </div>
        )}

        {/* Billing Period Toggle */}
        <div className="flex justify-center mb-8">
          <PlanToggle value={billingPeriod} onChange={setBillingPeriod} />
        </div>

        {/* Single Plan Card — Centered */}
        <div className="max-w-lg mx-auto">
          <div className="backdrop-blur-xl bg-white/50 dark:bg-gray-900/40 border-2 border-[var(--brand-blue)] rounded-card p-8 shadow-gem-amethyst">
            {/* Plan Name */}
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-[var(--ink)] mb-1">SmartLic Pro</h2>
              <p className="text-sm text-[var(--ink-secondary)]">
                Inteligência de decisão completa para licitações
              </p>
            </div>

            {/* Dynamic Price */}
            <div className="text-center mb-6">
              <div className="flex items-baseline justify-center gap-1">
                <span className="text-5xl font-bold text-[var(--brand-navy)]">
                  {formatCurrency(currentPricing.monthly)}
                </span>
                <span className="text-lg text-[var(--ink-muted)]">/mês</span>
              </div>

              {currentPricing.discount && (
                <div className="mt-2">
                  <span className="inline-block px-3 py-1 bg-[var(--success-subtle)] text-[var(--success)] text-sm font-semibold rounded-full">
                    Economize {currentPricing.discount}%
                  </span>
                  {billingPeriod === "semiannual" && (
                    <p className="text-xs text-[var(--ink-muted)] mt-1">
                      Cobrado {formatCurrency(currentPricing.total)} a cada 6 meses
                    </p>
                  )}
                  {billingPeriod === "annual" && (
                    <p className="text-xs text-[var(--ink-muted)] mt-1">
                      Cobrado {formatCurrency(currentPricing.total)} por ano
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Feature List — ALL enabled */}
            <ul className="space-y-3 mb-8">
              {FEATURES.map((feature) => (
                <li key={feature.text} className="flex items-start gap-3">
                  <span className="flex-shrink-0 mt-0.5 w-5 h-5 rounded-full bg-[var(--success)] text-white flex items-center justify-center text-xs font-bold">
                    &#10003;
                  </span>
                  <div>
                    <span className="text-sm font-medium text-[var(--ink)]">{feature.text}</span>
                    <span className="block text-xs text-[var(--ink-muted)]">{feature.detail}</span>
                  </div>
                </li>
              ))}
            </ul>

            {/* CTA Button */}
            <button
              onClick={hasFullAccess ? handleManageSubscription : handleCheckout}
              disabled={checkoutLoading || portalLoading}
              className="w-full py-4 rounded-button text-lg font-bold transition-all
                bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] hover:shadow-lg
                disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {checkoutLoading || portalLoading
                ? "Processando..."
                : userStatus === "subscriber"
                ? "Gerenciar assinatura"
                : userStatus === "privileged"
                ? "Acesso completo"
                : userStatus === "trial_expired"
                ? "Continuar com SmartLic"
                : userStatus === "trial"
                ? "Assinar agora"
                : "Começar Agora"}
            </button>

            <p className="mt-3 text-center text-xs text-[var(--ink-muted)]">
              Cancele quando quiser. Sem contrato de fidelidade. Pagamento seguro via Stripe.
            </p>
          </div>
        </div>

        {/* ROI Anchor Message */}
        <div className="mt-12 max-w-lg mx-auto">
          <div className="backdrop-blur-md bg-white/60 dark:bg-gray-900/50 border border-white/20 dark:border-white/10 rounded-card p-6 text-center shadow-glass">
            <p className="text-lg font-semibold text-[var(--ink)] mb-2">
              Uma única licitação ganha pode pagar um ano inteiro
            </p>
            <div className="flex items-center justify-center gap-8 text-sm text-[var(--ink-secondary)]">
              <div>
                <p className="text-2xl font-bold text-[var(--brand-navy)]">R$ 150.000</p>
                <p>Oportunidade média</p>
              </div>
              <div className="text-3xl text-[var(--ink-muted)]">vs</div>
              <div>
                <p className="text-2xl font-bold text-[var(--success)]">{formatCurrency(PRICING.annual.total)}</p>
                <p>SmartLic Pro anual</p>
              </div>
            </div>
            <p className="mt-3 text-sm font-semibold text-[var(--brand-blue)]">
              Exemplo ilustrativo com base em oportunidades típicas do setor
            </p>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-16 max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-[var(--ink)] mb-6 text-center">
            Perguntas Frequentes
          </h2>
          <div className="space-y-3">
            {FAQ_ITEMS.map((item, index) => (
              <div
                key={index}
                className="backdrop-blur-md bg-white/60 dark:bg-gray-900/50 border border-white/20 dark:border-white/10 rounded-card overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === index ? null : index)}
                  className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-[var(--surface-1)] transition-colors"
                >
                  <span className="font-medium text-[var(--ink)]">{item.question}</span>
                  <svg
                    className={`w-5 h-5 text-[var(--ink-muted)] transition-transform ${openFaq === index ? "rotate-180" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {openFaq === index && (
                  <div className="px-6 pb-4">
                    <p className="text-sm text-[var(--ink-secondary)]">{item.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-12 text-center">
          <Link
            href="/buscar"
            className="text-sm text-[var(--ink-muted)] hover:underline"
          >
            {hasFullAccess ? "Voltar para análises" : "Continuar com período de avaliação"}
          </Link>
        </div>
      </div>
    </div>
  );
}
