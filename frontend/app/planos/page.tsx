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
import TestimonialSection, { TESTIMONIALS } from "../../components/TestimonialSection";

interface UserProfile {
  plan_id?: string;
  plan_name?: string;
  is_admin?: boolean;
}

// STORY-277: Repricing — R$397/mês (market-aligned). STORY-319: 14-day trial
const PRICING: Record<BillingPeriod, { monthly: number; total: number; period: string; discount?: number }> = {
  monthly: { monthly: 397, total: 397, period: "mês" },
  semiannual: { monthly: 357, total: 2142, period: "semestre", discount: 10 },
  annual: { monthly: 297, total: 3564, period: "ano", discount: 25 },
};

// GTM-002: Features list — ALL enabled (no comparison needed)
const FEATURES = [
  { text: "1.000 análises por mês", detail: "Avalie oportunidades em todos os 27 estados" },
  { text: "Exportação Excel completa", detail: "Relatórios detalhados para sua equipe" },
  { text: "Pipeline de acompanhamento", detail: "Gerencie oportunidades do início ao fim" },
  { text: "Resumos executivos com IA avançada", detail: "Análise estratégica de cada oportunidade" },
  { text: "Histórico completo", detail: "Acesso a oportunidades publicadas nos portais oficiais" },
  { text: "15 setores e 27 estados", detail: "Cobertura nacional integrada de fontes oficiais" },
  { text: "Filtragem com 1.000+ regras", detail: "Precisão setorial para seu mercado" },
];

const CONSULTORIA_PRICING: Record<BillingPeriod, { monthly: number; total: number; period: string; discount?: number }> = {
  monthly: { monthly: 997, total: 997, period: "mês" },
  semiannual: { monthly: 897, total: 5382, period: "semestre", discount: 10 },
  annual: { monthly: 797, total: 9564, period: "ano", discount: 20 },
};

const CONSULTORIA_FEATURES = [
  { text: "Até 5 usuários", detail: "Sua equipe inteira em uma só conta" },
  { text: "5.000 análises por mês", detail: "Capacidade compartilhada entre membros" },
  { text: "Dashboard consolidado", detail: "Veja buscas e resultados de toda a equipe" },
  { text: "Logo da consultoria nos relatórios", detail: "Branding profissional em Excel/PDF" },
  { text: "Todas as funcionalidades Pro", detail: "Excel, pipeline, IA, 15 setores, 27 estados" },
  { text: "Suporte prioritário", detail: "Atendimento dedicado para sua consultoria" },
];

// FAQ items — STORY-280 AC4: Updated to mention Boleto
const FAQ_ITEMS = [
  {
    question: "Quais formas de pagamento são aceitas?",
    answer: "Aceitamos cartão de crédito e Boleto Bancário. O cartão é processado instantaneamente. O boleto pode levar até 1 dia útil para confirmação após o pagamento.",
  },
  {
    question: "Posso cancelar a qualquer momento?",
    answer: "Sim. Sem contrato de fidelidade, mesmo no acesso anual. Cancele quando quiser e mantenha o acesso até o fim do período já pago.",
  },
  {
    question: "Existe contrato de fidelidade?",
    answer: "Não. O SmartLic Pro funciona como acesso recorrente. Você escolhe o período de acesso e pode alterar ou cancelar livremente.",
  },
  {
    question: "O que acontece se eu cancelar?",
    answer: "Você mantém acesso completo até o fim do período já pago. Após essa data, o acesso ao sistema é encerrado. O período de avaliação gratuita é exclusivo para os primeiros 14 dias após o cadastro inicial e não é reativado.",
  },
  {
    question: "Como funciona a cobrança semestral e anual?",
    answer: "No acesso semestral, o valor é cobrado a cada 6 meses com 10% de economia. No anual, a cada 12 meses com 25% de economia. Stripe processa tudo com segurança.",
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

  // STORY-323 AC17: Partner tracking state
  const [partnerName, setPartnerName] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("success")) setStatusMsg("Acesso ativado com sucesso! Bem-vindo ao SmartLic Pro.");
    if (params.get("cancelled")) setStatusMsg("Processo cancelado.");
    // Pre-select billing period from URL
    const billing = params.get("billing");
    if (billing === "semiannual" || billing === "annual") setBillingPeriod(billing);

    // STORY-323 AC17: Detect partner from URL or cookie/localStorage
    const partnerSlug = params.get("partner") || localStorage.getItem("smartlic_partner");
    if (partnerSlug) {
      localStorage.setItem("smartlic_partner", partnerSlug);
      document.cookie = `smartlic_partner=${partnerSlug};path=/;max-age=${7 * 24 * 60 * 60}`;
      setPartnerName(partnerSlug.replace(/-/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()));
    }
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

  const handleConsultoriaCheckout = async () => {
    if (!session) { window.location.href = "/login"; return; }
    setCheckoutLoading(true);
    trackEvent("checkout_initiated", { plan_id: "consultoria", billing_period: billingPeriod, source: "planos_page" });
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
      const res = await fetch(
        `${backendUrl}/v1/checkout?plan_id=consultoria&billing_period=${billingPeriod}`,
        { method: "POST", headers: { Authorization: `Bearer ${session.access_token}` } }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao iniciar processo");
      }
      const data = await res.json();
      setStripeRedirecting(true);
      window.location.href = data.checkout_url;
    } catch (err) {
      toast.error(getUserFriendlyError(err));
      setCheckoutLoading(false);
      setStripeRedirecting(false);
    }
  };

  // AC22: Detect consultoria UTM params for lead badge
  const isConsultoriaLead = useMemo(() => {
    if (typeof window === "undefined") return false;
    const params = new URLSearchParams(window.location.search);
    return params.get("utm_source") === "consultoria" || params.get("utm_campaign") === "consultoria";
  }, []);

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
            Comece a Vencer Licitações
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
          <div data-testid="status-banner-subscriber" className="mb-8 p-4 bg-emerald-50 dark:bg-emerald-950/50 backdrop-blur-sm border border-emerald-200 dark:border-emerald-800 rounded-card text-center">
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
          <div data-testid="status-banner-privileged" className="mb-8 p-4 bg-emerald-50 dark:bg-emerald-950/50 backdrop-blur-sm border border-emerald-200 dark:border-emerald-800 rounded-card text-center">
            <p className="font-semibold text-emerald-800 dark:text-emerald-200">
              Você possui acesso completo ao SmartLic
            </p>
            <Link href="/buscar" className="mt-1 text-sm text-emerald-600 dark:text-emerald-400 hover:underline">
              Iniciar análise
            </Link>
          </div>
        )}

        {userStatus === "trial" && (
          <div data-testid="status-banner-trial" className="mb-8 p-4 bg-blue-50 dark:bg-blue-950/50 backdrop-blur-sm border border-blue-200 dark:border-blue-800 rounded-card text-center">
            <p className="font-semibold text-blue-800 dark:text-blue-200">
              Você está no período de avaliação{trialDaysRemaining !== null ? ` (${trialDaysRemaining} ${trialDaysRemaining === 1 ? "dia restante" : "dias restantes"})` : ""}
            </p>
            <p className="text-sm text-blue-600 dark:text-blue-400">
              Assine para continuar após o período de avaliação
            </p>
          </div>
        )}

        {userStatus === "trial_expired" && (
          <div data-testid="status-banner-expired" className="mb-8 p-4 bg-amber-50 dark:bg-amber-950/50 backdrop-blur-sm border border-amber-200 dark:border-amber-800 rounded-card text-center">
            <p className="font-semibold text-amber-800 dark:text-amber-200">
              Seu período de avaliação encerrou
            </p>
            <p className="text-sm text-amber-600 dark:text-amber-400">
              Assine para voltar a ter acesso
            </p>
          </div>
        )}

        {/* STORY-323 AC17: Partner referral banner */}
        {partnerName && (
          <div data-testid="partner-discount-banner" className="mb-8 p-4 bg-emerald-50 dark:bg-emerald-950/50 backdrop-blur-sm border border-emerald-200 dark:border-emerald-800 rounded-card text-center">
            <p className="font-semibold text-emerald-800 dark:text-emerald-200">
              Indicado por <strong>{partnerName}</strong> — 25% de desconto aplicado no checkout
            </p>
            <p className="text-sm text-emerald-600 dark:text-emerald-400">
              O cupom exclusivo será aplicado automaticamente ao finalizar
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
                : "Começar a filtrar oportunidades"}
            </button>

            <p className="mt-3 text-center text-xs text-[var(--ink-muted)]">
              Cancele quando quiser. Sem contrato de fidelidade. Pagamento seguro via Stripe.
            </p>

            {/* STORY-273 AC6: Stripe/Security Badge */}
            <div className="mt-4 flex items-center justify-center gap-3 pt-4 border-t border-white/10" data-testid="stripe-security-badge">
              <svg className="h-5 w-auto text-[var(--ink-muted)]" viewBox="0 0 60 25" fill="currentColor" aria-label="Stripe" role="img">
                <path d="M5 10.1c0-.7.6-1 1.5-1 1.3 0 3 .4 4.3 1.1V6.3c-1.5-.6-2.9-.8-4.3-.8C3.2 5.5.8 7.4.8 10.3c0 4.5 6.2 3.8 6.2 5.7 0 .8-.7 1.1-1.7 1.1-1.5 0-3.4-.6-4.9-1.4v3.9c1.7.7 3.3 1 4.9 1 3.4 0 5.7-1.7 5.7-4.6-.1-4.9-6.3-4-6.3-5.9zm11.5-4.3L12.3 7v7.7c0 2.8 2.1 4 4.1 4 1.3 0 2.3-.3 2.8-.6V15c-.5.2-2.9.9-2.9-1.3V9h2.9V5.9h-2.9l.2-.1zm6.8 4.8l-.3-1.6h-3.6v13h4.1v-8.8c1-1.3 2.6-1 3.1-.9V5.9c-.6-.2-2.5-.5-3.3 1.7zm4.3-1.7h4.1v13h-4.1zm0-1.6l4.1-.9V2.6l-4.1.9v3.8zm10 .1c-1.5 0-2.5.7-3 1.2l-.2-1h-3.6v17.4l4.1-.9v-4.2c.6.4 1.4 1 2.8 1 2.8 0 5.4-2.3 5.4-7.2-.1-4.6-2.7-7-5.5-7zm-1 10.7c-.9 0-1.5-.3-1.9-.8v-6c.4-.5 1-.8 1.9-.8 1.5 0 2.5 1.7 2.5 3.8 0 2.2-1 3.8-2.5 3.8zm13.8-10.6c-2.4 0-4 2-4 4.3 0 2.8 1.8 4.3 4.3 4.3 1.2 0 2.2-.3 2.9-.7v-3c-.7.4-1.5.6-2.5.6-1 0-1.9-.3-2-1.5h5c0-.1.1-.8.1-1.2-.1-2.5-1.3-4.8-3.8-4.8zm-1.5 3.5c0-1.1.7-1.6 1.3-1.6.7 0 1.3.5 1.3 1.6h-2.6z" />
              </svg>
              <div className="flex items-center gap-1.5 text-xs text-[var(--ink-muted)]">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>Pagamento seguro</span>
              </div>
            </div>

            {/* STORY-280 AC4: Payment method icons */}
            <div className="mt-3 flex items-center justify-center gap-4 text-xs text-[var(--ink-muted)]" data-testid="payment-methods">
              {/* Card icon */}
              <div className="flex items-center gap-1.5">
                <svg className="w-5 h-3.5" viewBox="0 0 24 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                  <rect x="1" y="1" width="22" height="14" rx="2" />
                  <line x1="1" y1="6" x2="23" y2="6" />
                  <rect x="3" y="9" width="5" height="2" rx="0.5" fill="currentColor" stroke="none" />
                </svg>
                <span>Cartao</span>
              </div>
              {/* Boleto icon */}
              <div className="flex items-center gap-1.5">
                <svg className="w-5 h-3.5" viewBox="0 0 24 16" fill="currentColor" aria-hidden="true">
                  <rect x="1" y="1" width="1.5" height="14" />
                  <rect x="4" y="1" width="1" height="14" />
                  <rect x="6.5" y="1" width="2" height="14" />
                  <rect x="10" y="1" width="1" height="14" />
                  <rect x="12.5" y="1" width="1.5" height="14" />
                  <rect x="15.5" y="1" width="1" height="14" />
                  <rect x="18" y="1" width="2" height="14" />
                  <rect x="21.5" y="1" width="1.5" height="14" />
                </svg>
                <span>Boleto</span>
              </div>
            </div>
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

        {/* Consultoria Plan Card — AC21/AC22 */}
        <div className="mt-16 max-w-lg mx-auto">
          <div className="text-center mb-6">
            {isConsultoriaLead && (
              <span className="inline-block mb-4 px-3 py-1 bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-400 text-sm font-semibold rounded-full">
                Recomendado para consultorias
              </span>
            )}
            <h2 className="text-2xl font-bold text-[var(--ink)]">Para Consultorias e Assessorias</h2>
            <p className="text-sm text-[var(--ink-secondary)] mt-1">
              Gerencie sua equipe e consolide resultados em uma conta
            </p>
          </div>
          <div className="backdrop-blur-xl bg-white/50 dark:bg-gray-900/40 border-2 border-amber-500 rounded-card p-8 shadow-gem-amethyst">
            {/* Plan Name */}
            <div className="text-center mb-6">
              <div className="flex items-center justify-center gap-2 mb-1">
                <h3 className="text-2xl font-bold text-[var(--ink)]">SmartLic Consultoria</h3>
              </div>
            </div>
            {/* Dynamic Price */}
            <div className="text-center mb-6">
              <div className="flex items-baseline justify-center gap-1">
                <span className="text-5xl font-bold text-amber-700 dark:text-amber-400">
                  {formatCurrency(CONSULTORIA_PRICING[billingPeriod].monthly)}
                </span>
                <span className="text-lg text-[var(--ink-muted)]">/mês</span>
              </div>
              {CONSULTORIA_PRICING[billingPeriod].discount && (
                <div className="mt-2">
                  <span className="inline-block px-3 py-1 bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-400 text-sm font-semibold rounded-full">
                    Economize {CONSULTORIA_PRICING[billingPeriod].discount}%
                  </span>
                </div>
              )}
            </div>
            {/* Feature List */}
            <ul className="space-y-3 mb-8">
              {CONSULTORIA_FEATURES.map((feature) => (
                <li key={feature.text} className="flex items-start gap-3">
                  <span className="flex-shrink-0 mt-0.5 w-5 h-5 rounded-full bg-amber-500 text-white flex items-center justify-center text-xs font-bold">&#10003;</span>
                  <div>
                    <span className="text-sm font-medium text-[var(--ink)]">{feature.text}</span>
                    <span className="block text-xs text-[var(--ink-muted)]">{feature.detail}</span>
                  </div>
                </li>
              ))}
            </ul>
            {/* CTA */}
            <button
              onClick={() => {
                if (!session) { window.location.href = "/login"; return; }
                handleConsultoriaCheckout();
              }}
              disabled={checkoutLoading}
              className="w-full py-4 rounded-button text-lg font-bold transition-all bg-amber-600 text-white hover:bg-amber-700 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {checkoutLoading ? "Processando..." : "Falar com vendas"}
            </button>
            <p className="mt-3 text-center text-xs text-[var(--ink-muted)]">
              Ideal para consultorias com 3-5 colaboradores
            </p>
          </div>
        </div>

        {/* STORY-273 AC2: Testimonials on Pricing Page */}
        <div className="mt-16" data-testid="pricing-testimonials">
          <TestimonialSection
            testimonials={TESTIMONIALS.slice(0, 3)}
            heading="Empresas que já usam SmartLic"
            className="!py-0 !bg-transparent"
          />
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
