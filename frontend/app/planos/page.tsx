"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { usePlans } from "../../hooks/usePlans";
import { useAuth } from "../components/AuthProvider";
import LandingNavbar from "../components/landing/LandingNavbar";
import Link from "next/link";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useClarity } from "../../hooks/useClarity";
import { getUserFriendlyError } from "../../lib/error-messages";
import { PlanToggle, BillingPeriod } from "../../components/subscriptions/PlanToggle";
import { formatCurrency, ROI_DISCLAIMER } from '@/lib/copy/roi';
import { usePlan } from "../../hooks/usePlan";
import { toast } from "sonner";
import { MessageCircle, Mail } from "lucide-react";
import TestimonialSection, { TESTIMONIALS } from "../../components/TestimonialSection";
import { CaseStudyCard } from "../../components/CaseStudyCard";
import { safeSetItem, safeGetItem } from "../../lib/storage";

import { PlanStatusBanners } from "./components/PlanStatusBanners";
import { PlanProCard } from "./components/PlanProCard";
import { PlanConsultoriaCard } from "./components/PlanConsultoriaCard";
import { PlanFAQ } from "./components/PlanFAQ";
import { ProductSchema } from "./components/ProductSchema";
import { buttonVariants } from "../../components/ui/button";
import { trackViewItem, trackBeginCheckout } from "../components/GoogleAnalytics";
import { PRO_PRICING, CONSULTORIA_PRICING } from "@/lib/plan-pricing";
import type { components } from "../api-types.generated";

// STORY-2.1 (EPIC-TD-2026Q2): Profile shape is a subset of the backend
// UserProfileResponse schema. Fields we don't consume here stay optional so
// callers can pass the full response unchanged.
type UserProfile = Partial<components["schemas"]["UserProfileResponse"]>;

// STORY-360 AC2 + STORY-SEO-004: pricing source of truth lives in `lib/plan-pricing.ts`
// (consumed here and by ProductSchema.tsx to keep JSON-LD in sync with UI).
const PRICING_FALLBACK = PRO_PRICING;

// Coupon → discount % mapping. Day 16 trial-expired email sends TRIAL_COMEBACK_20.
// Keep in sync with Stripe coupon configuration (Stripe is source of truth for actual billing).
const COUPON_DISCOUNTS: Record<string, number> = {
  TRIAL_COMEBACK_20: 20,
};

// GTM-002: Features list
const FEATURES = [
  { text: "1.000 análises por mês", detail: "Avalie oportunidades em todos os 27 estados" },
  { text: "Exportação Excel completa", detail: "Relatórios detalhados para sua equipe" },
  { text: "Pipeline de acompanhamento", detail: "Gerencie oportunidades do início ao fim" },
  { text: "Resumos executivos com IA avançada", detail: "Análise estratégica de cada oportunidade" },
  { text: "Histórico completo", detail: "Acesso a oportunidades publicadas nos portais oficiais" },
  { text: "15 setores e 27 estados", detail: "Cobertura nacional integrada de fontes oficiais" },
  { text: "Filtragem com 1.000+ regras", detail: "Precisão setorial para seu mercado" },
];

const CONSULTORIA_PRICING_FALLBACK = CONSULTORIA_PRICING;

const CONSULTORIA_FEATURES = [
  { text: "Até 5 usuários", detail: "Sua equipe inteira em uma só conta" },
  { text: "5.000 análises por mês", detail: "Capacidade compartilhada entre membros" },
  { text: "Dashboard consolidado", detail: "Veja análises e resultados de toda a equipe" },
  { text: "Logo da consultoria nos relatórios", detail: "Branding profissional em Excel/PDF" },
  { text: "Todas as funcionalidades Pro", detail: "Excel, pipeline, IA, 15 setores, 27 estados" },
  { text: "Suporte prioritário", detail: "Atendimento dedicado para sua consultoria" },
];

const FAQ_ITEMS = [
  { question: "Quais formas de pagamento são aceitas?", answer: "Aceitamos cartão de crédito e Boleto Bancário. O cartão é processado instantaneamente. O boleto pode levar até 1 dia útil para confirmação após o pagamento." },
  { question: "Posso cancelar a qualquer momento?", answer: "Sim. Sem contrato de fidelidade, mesmo no acesso anual. Cancele quando quiser e mantenha o acesso até o fim do período já pago." },
  { question: "Existe contrato de fidelidade?", answer: "Não. O SmartLic Pro funciona como acesso recorrente. Você escolhe o período de acesso e pode alterar ou cancelar livremente." },
  { question: "O que acontece se eu cancelar?", answer: "Você mantém acesso completo até o fim do período já pago. Após essa data, o acesso ao sistema é encerrado. O período de avaliação gratuita é exclusivo para os primeiros 14 dias após o cadastro inicial e não é reativado." },
  { question: "Como funciona a cobrança semestral e anual?", answer: `No acesso semestral, o valor é cobrado a cada 6 meses com ${PRICING_FALLBACK.semiannual.discount}% de economia. No anual, a cada 12 meses com ${PRICING_FALLBACK.annual.discount}% de economia. Stripe processa tudo com segurança.` },
];

type UserStatus = "subscriber" | "privileged" | "trial" | "trial_expired" | "anonymous";

export default function PlanosPage() {
  const { session, user, isAdmin, loading: authLoading } = useAuth();
  const { planInfo, loading: planLoading } = usePlan();
  const { trackEvent } = useAnalytics();
  const { clarityEvent, claritySet } = useClarity();
  const trackEventRef = useRef(trackEvent);
  trackEventRef.current = trackEvent;
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [stripeRedirecting, setStripeRedirecting] = useState(false);
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("annual");
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [partnerName, setPartnerName] = useState<string | null>(null);
  const [couponCode, setCouponCode] = useState<string | null>(null);

  // STORY-BIZ-002: scroll to consultoria card when landing with ?highlight=consultoria
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("highlight") !== "consultoria") return;
    // Defer until the card is mounted
    const timer = window.setTimeout(() => {
      const el = document.getElementById("plano-consultoria");
      if (el && typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        el.classList.add("ring-2", "ring-indigo-400", "ring-offset-2");
        window.setTimeout(() => {
          el.classList.remove("ring-2", "ring-indigo-400", "ring-offset-2");
        }, 3000);
      }
    }, 250);
    return () => window.clearTimeout(timer);
  }, []);

  // TD-008 AC4: SWR-based dynamic pricing with static fallback
  type PricingMap = Record<BillingPeriod, { monthly: number; total: number; period: string; discount?: number }>;
  const { plans: plansData } = usePlans();

  const { proPricing, consultoriaPricing } = useMemo(() => {
    let pro: PricingMap = PRICING_FALLBACK;
    let consultoria: PricingMap = CONSULTORIA_PRICING_FALLBACK;
    if (!plansData) return { proPricing: pro, consultoriaPricing: consultoria };

    for (const plan of plansData) {
      const bp = plan.billing_periods;
      if (!bp) continue;
      const buildPricing = (base: PricingMap): PricingMap => {
        const result = { ...base };
        if (bp.monthly) {
          const m = bp.monthly.price_cents / 100;
          result.monthly = { monthly: m, total: m, period: "mês" };
        }
        if (bp.semiannual) {
          const m = bp.semiannual.price_cents / 100;
          result.semiannual = { monthly: m, total: m * 6, period: "semestre", discount: bp.semiannual.discount_percent || undefined };
        }
        if (bp.annual) {
          const m = bp.annual.price_cents / 100;
          result.annual = { monthly: m, total: m * 12, period: "ano", discount: bp.annual.discount_percent || undefined };
        }
        return result;
      };
      if (plan.id === "smartlic_pro") pro = buildPricing(PRICING_FALLBACK);
      if (plan.id === "consultoria") consultoria = buildPricing(CONSULTORIA_PRICING_FALLBACK);
    }
    return { proPricing: pro, consultoriaPricing: consultoria };
  }, [plansData]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("success")) setStatusMsg("Acesso ativado com sucesso! Bem-vindo ao SmartLic Pro.");
    if (params.get("cancelled")) setStatusMsg("Processo cancelado.");
    const billing = params.get("billing");
    if (billing === "monthly" || billing === "semiannual" || billing === "annual") setBillingPeriod(billing);
    // Zero-churn P1 §3.2: Auto-apply coupon from URL (e.g., ?coupon=TRIAL_COMEBACK_20)
    const coupon = params.get("coupon");
    if (coupon) setCouponCode(coupon);

    const partnerSlug = params.get("partner") || safeGetItem("smartlic_partner");
    if (partnerSlug) {
      safeSetItem("smartlic_partner", partnerSlug);
      document.cookie = `smartlic_partner=${partnerSlug};path=/;max-age=${7 * 24 * 60 * 60}`;
      setPartnerName(partnerSlug.replace(/-/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()));
    }
  }, []);

  useEffect(() => {
    trackEventRef.current("plan_page_viewed", { source: "url" });
  }, []);

  // GA4 view_item — fire once per billing period change for each plan shown.
  useEffect(() => {
    const pro = proPricing[billingPeriod];
    const consult = consultoriaPricing[billingPeriod];
    trackViewItem({
      id: "smartlic_pro",
      name: "SmartLic Pro",
      price: pro.monthly,
      billing_period: billingPeriod,
      category: "subscription",
    });
    trackViewItem({
      id: "consultoria",
      name: "SmartLic Consultoria",
      price: consult.monthly,
      billing_period: billingPeriod,
      category: "subscription",
    });
  }, [billingPeriod, proPricing, consultoriaPricing]);

  useEffect(() => {
    const fetchUserProfile = async () => {
      if (!session?.access_token) { setUserProfile(null); setProfileLoading(false); return; }
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
        const res = await fetch(`${backendUrl}/v1/me`, { headers: { Authorization: `Bearer ${session.access_token}` } });
        if (res.ok) setUserProfile(await res.json());
      } catch { /* Ignore */ } finally { setProfileLoading(false); }
    };
    fetchUserProfile();
  }, [session?.access_token]);

  const userStatus: UserStatus = useMemo(() => {
    if (!session || !user) return "anonymous";
    if (planInfo?.plan_id === "smartlic_pro" && planInfo?.subscription_status === "active") return "subscriber";
    if (isAdmin || userProfile?.is_admin || userProfile?.plan_id === "master") return "privileged";
    if (planInfo?.plan_id === "free_trial" && planInfo?.subscription_status === "expired") return "trial_expired";
    if (planInfo?.plan_id === "free_trial") return "trial";
    return "trial";
  }, [session, user, planInfo, isAdmin, userProfile]);

  const trialDaysRemaining = useMemo(() => {
    if (!planInfo?.trial_expires_at) return null;
    const diffTime = new Date(planInfo.trial_expires_at).getTime() - Date.now();
    return Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
  }, [planInfo?.trial_expires_at]);

  const currentPricing = proPricing[billingPeriod];
  const hasFullAccess = userStatus === "subscriber" || userStatus === "privileged";
  const couponDiscountPercent = couponCode
    ? COUPON_DISCOUNTS[couponCode.toUpperCase()]
    : undefined;

  const handleManageSubscription = useCallback(async () => {
    if (!session?.access_token) return;
    // Privileged users (admin/master) have no Stripe subscription — redirect to buscar directly
    if (userStatus === "privileged") {
      window.location.href = "/buscar";
      return;
    }
    setPortalLoading(true);
    try {
      const res = await fetch("/api/billing-portal", { method: "POST", headers: { Authorization: `Bearer ${session.access_token}` } });
      if (!res.ok) throw new Error("Erro ao abrir portal");
      const data = await res.json();
      window.location.href = data.url;
    } catch (err) { toast.error(getUserFriendlyError(err)); } finally { setPortalLoading(false); }
  }, [session?.access_token, userStatus]);

  const handleCheckout = async () => {
    if (!session) { window.location.href = "/login"; return; }
    setCheckoutLoading(true);
    trackEvent("checkout_initiated", { plan_id: "smartlic_pro", billing_period: billingPeriod, source: "planos_page" });
    if (typeof window !== "undefined" && window.mixpanel) {
      window.mixpanel.track("plan_selected", {
        plan_id: "smartlic_pro",
        billing_period: billingPeriod,
        has_coupon: !!couponCode,
        coupon_id: couponCode ?? null,
        discount_percent: couponDiscountPercent ?? null,
      });
    }
    clarityEvent("checkout_initiated");
    claritySet("selected_plan", "smartlic_pro");
    claritySet("billing_period", billingPeriod);
    trackBeginCheckout({
      id: "smartlic_pro",
      name: "SmartLic Pro",
      price: proPricing[billingPeriod].total,
      billing_period: billingPeriod,
      category: "subscription",
    });
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
      const checkoutUrl = `${backendUrl}/v1/checkout?plan_id=smartlic_pro&billing_period=${billingPeriod}${couponCode ? `&coupon=${encodeURIComponent(couponCode)}` : ""}`;
      const res = await fetch(checkoutUrl, {
        method: "POST", headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || "Erro ao iniciar processo"); }
      const data = await res.json();
      setStripeRedirecting(true);
      window.location.href = data.checkout_url;
    } catch (err) {
      trackEvent("checkout_failed", { plan_id: "smartlic_pro", billing_period: billingPeriod, error: err instanceof Error ? err.message : "unknown" });
      toast.error(getUserFriendlyError(err));
      setCheckoutLoading(false);
      setStripeRedirecting(false);
    }
  };

  const handleConsultoriaCheckout = async () => {
    if (!session) { window.location.href = "/login"; return; }
    setCheckoutLoading(true);
    trackEvent("checkout_initiated", { plan_id: "consultoria", billing_period: billingPeriod, source: "planos_page" });
    if (typeof window !== "undefined" && window.mixpanel) {
      window.mixpanel.track("plan_selected", {
        plan_id: "consultoria",
        billing_period: billingPeriod,
        has_coupon: !!couponCode,
        coupon_id: couponCode ?? null,
        discount_percent: couponDiscountPercent ?? null,
      });
    }
    clarityEvent("checkout_initiated");
    claritySet("selected_plan", "consultoria");
    claritySet("billing_period", billingPeriod);
    trackBeginCheckout({
      id: "consultoria",
      name: "SmartLic Consultoria",
      price: consultoriaPricing[billingPeriod].total,
      billing_period: billingPeriod,
      category: "subscription",
    });
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
      const res = await fetch(`${backendUrl}/v1/checkout?plan_id=consultoria&billing_period=${billingPeriod}`, {
        method: "POST", headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || "Erro ao iniciar processo"); }
      const data = await res.json();
      setStripeRedirecting(true);
      window.location.href = data.checkout_url;
    } catch (err) {
      toast.error(getUserFriendlyError(err));
      setCheckoutLoading(false);
      setStripeRedirecting(false);
    }
  };

  const isConsultoriaLead = useMemo(() => {
    if (typeof window === "undefined") return false;
    const params = new URLSearchParams(window.location.search);
    return params.get("utm_source") === "consultoria" || params.get("utm_campaign") === "consultoria";
  }, []);

  return (
    <div className="min-h-screen bg-[var(--canvas)]">
      <ProductSchema />
      <LandingNavbar />

      {/* Stripe redirect overlay */}
      {stripeRedirecting && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[var(--canvas)]/80 backdrop-blur-sm">
          <div role="status" className="backdrop-blur-xl bg-white/70 dark:bg-gray-900/60 border border-white/20 dark:border-white/10 rounded-card p-8 text-center shadow-glass max-w-sm mx-4">
            <div className="w-12 h-12 mx-auto mb-4 border-4 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
            <h2 className="text-lg font-semibold text-[var(--ink)] mb-2">Redirecionando para o checkout</h2>
            <p className="text-sm text-[var(--ink-secondary)]">Você será redirecionado para o Stripe para concluir de forma segura.</p>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto py-12 px-4">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-display font-bold text-[var(--ink)] mb-4">Comece a Vencer Licitações</h1>
          <p className="text-lg text-[var(--ink-secondary)] max-w-2xl mx-auto mb-5">O SmartLic é um só. Você decide com que frequência quer investir em inteligência competitiva.</p>
          {/* SAB-014: Trial badge above the fold — "14 dias grátis • sem cartão" */}
          <div
            className="inline-flex items-center gap-2 rounded-full border border-[var(--brand-blue)]/30 bg-[var(--brand-blue)]/10 px-4 py-1.5 text-sm font-medium text-[var(--brand-blue)]"
            data-testid="trial-badge"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span><strong>14 dias grátis</strong> · Sem cartão de crédito</span>
          </div>
        </div>

        <PlanStatusBanners
          userStatus={userStatus}
          trialDaysRemaining={trialDaysRemaining}
          partnerName={partnerName}
          statusMsg={statusMsg}
          portalLoading={portalLoading}
          onManageSubscription={handleManageSubscription}
        />

        {couponDiscountPercent !== undefined && (
          <div
            className="mb-6 rounded-card border border-emerald-300 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-900/30 px-4 py-3 text-center text-sm font-medium text-emerald-800 dark:text-emerald-200"
            role="status"
            data-testid="coupon-banner"
          >
            <span className="font-bold">Desconto de {couponDiscountPercent}% aplicado</span>
            <span className="ml-2 text-xs text-emerald-700 dark:text-emerald-300">
              (cupom {couponCode?.toUpperCase()})
            </span>
          </div>
        )}

        {/* Billing Period Toggle */}
        <div className="flex justify-center mb-8">
          <PlanToggle value={billingPeriod} onChange={setBillingPeriod} discounts={{ semiannual: proPricing.semiannual.discount, annual: proPricing.annual.discount }} />
        </div>

        <PlanProCard
          currentPricing={currentPricing}
          billingPeriod={billingPeriod}
          features={FEATURES}
          userStatus={userStatus}
          hasFullAccess={hasFullAccess}
          checkoutLoading={checkoutLoading}
          portalLoading={portalLoading}
          planLoading={planLoading || authLoading}
          onCheckout={handleCheckout}
          onManageSubscription={handleManageSubscription}
          couponDiscountPercent={couponDiscountPercent}
        />

        {/* ROI Anchor Message */}
        <div className="mt-12 max-w-lg mx-auto">
          <div className="backdrop-blur-md bg-white/60 dark:bg-gray-900/50 border border-white/20 dark:border-white/10 rounded-card p-6 text-center shadow-glass">
            <p className="text-lg font-semibold text-[var(--ink)] mb-2">Uma única licitação ganha pode pagar um ano inteiro</p>
            <div className="flex items-center justify-center gap-8 text-sm text-[var(--ink-secondary)]">
              <div>
                <p className="text-2xl font-bold text-[var(--brand-navy)]">R$ 150.000</p>
                <p>Oportunidade média</p>
              </div>
              <div className="text-3xl text-[var(--ink-muted)]">vs</div>
              <div>
                <p className="text-2xl font-bold text-[var(--success)]">{formatCurrency(proPricing.annual.total)}</p>
                <p>SmartLic Pro anual</p>
              </div>
            </div>
            <p className="mt-3 text-sm font-semibold text-[var(--brand-blue)]">Exemplo ilustrativo com base em oportunidades típicas do setor</p>
            <p className="mt-2 text-xs text-[var(--ink-muted)]" data-testid="roi-disclaimer">{ROI_DISCLAIMER}</p>
          </div>
        </div>

        {/* Zero-churn P2 §3.2 + §9: Payment methods + security badges */}
        <div className="mt-8 mb-8 flex flex-wrap items-center justify-center gap-6 text-sm text-[var(--ink-secondary)]">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-brand-navy" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
            <span>Cartão e Boleto</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
            <span>Dados criptografados</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            <span>LGPD compliant</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
            <span>Fontes oficiais do governo</span>
          </div>
        </div>

        {/* STORY-BIZ-002: anchor for ?highlight=consultoria scroll-to. */}
        <div id="plano-consultoria" data-plan-key="consultoria">
          <PlanConsultoriaCard
            pricing={consultoriaPricing}
            billingPeriod={billingPeriod}
            features={CONSULTORIA_FEATURES}
            isConsultoriaLead={isConsultoriaLead}
            checkoutLoading={checkoutLoading}
            onCheckout={() => { if (!session) { window.location.href = "/login"; return; } handleConsultoriaCheckout(); }}
            couponDiscountPercent={couponDiscountPercent}
          />
        </div>

        {/* Testimonials */}
        <div className="mt-16" data-testid="pricing-testimonials">
          <TestimonialSection testimonials={TESTIMONIALS.slice(0, 3)} heading="Empresas que já usam SmartLic" className="!py-0 !bg-transparent" />
        </div>

        {/* STORY-372 AC2: Case studies section */}
        <div className="mt-16 mb-12">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-display font-bold text-[var(--ink)]">
              Resultados reais de usuários SmartLic
            </h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <CaseStudyCard
              sector="Limpeza e Conservação"
              location="Curitiba-PR"
              companySize="12 funcionários"
              problem="Monitorava editais manualmente no PNCP 2h por dia"
              result="Encontrou Pregão Eletrônico de R$87.000 (prefeitura vizinha) que não apareceu na busca manual"
              highlight={{
                value: "R$ 87.000",
                label: "em oportunidades encontradas",
                time: "em 6 minutos",
              }}
            />
            <CaseStudyCard
              sector="Insumos de Informática"
              location="Porto Alegre-RS"
              companySize="Distribuidora regional"
              problem="Perdia editais por descobrir tarde demais"
              result="Identificou 3 pregões em municípios do interior com prazo > 10 dias"
              highlight={{
                value: "R$ 245.000",
                label: "valor total dos 3 editais",
                time: "identificados no primeiro acesso",
              }}
            />
          </div>
          <p className="text-xs text-[var(--ink-secondary)] text-center mt-4 opacity-70">
            * Cases baseados em dados reais de uso durante período de avaliação. Valores e detalhes aproximados para preservar privacidade.
          </p>
        </div>

        <PlanFAQ items={FAQ_ITEMS} openIndex={openFaq} onToggle={(i) => setOpenFaq(openFaq === i ? null : i)} />

        {/* Contact row */}
        <div className="mt-16 max-w-2xl mx-auto" data-testid="contact-row">
          <div className="border-t border-gray-200 dark:border-gray-700" />
          <div className="py-8 text-center">
            <p className="text-lg font-semibold text-[var(--ink)] mb-4">Precisa de mais informações?</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8">
              <a href={`https://wa.me/${process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "5548988344559"}?text=${encodeURIComponent("Olá! Gostaria de saber mais sobre o SmartLic Pro.")}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-[var(--ink-secondary)] hover:text-[var(--brand-blue)] transition-colors" data-testid="whatsapp-link">
                <MessageCircle className="w-5 h-5" /><span className="font-medium">Fale conosco</span>
              </a>
              <a href="mailto:tiago.sasaki@confenge.com.br" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-[var(--ink-secondary)] hover:text-[var(--brand-blue)] transition-colors" data-testid="email-link">
                <Mail className="w-5 h-5" /><span className="font-medium">tiago.sasaki@confenge.com.br</span>
              </a>
            </div>
          </div>
          <div className="border-t border-gray-200 dark:border-gray-700" />
        </div>

        {/* Bottom CTA — uses shared buttonVariants for consistent styling (DEBT-006 AC4) */}
        <div className="mt-12 text-center">
          <Link
            href="/buscar"
            className={buttonVariants({ variant: "link", size: "sm", className: "text-[var(--ink-muted)]" })}
          >
            {hasFullAccess ? "Voltar para análises" : "Continuar com período de avaliação"}
          </Link>
        </div>
      </div>
    </div>
  );
}
