"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../components/AuthProvider";
import LandingNavbar from "../components/landing/LandingNavbar";
import Link from "next/link";
import { useAnalytics } from "../../hooks/useAnalytics";
import { getUserFriendlyError } from "../../lib/error-messages";
import { PlanToggle, BillingPeriod } from "../../components/subscriptions/PlanToggle";
import { formatCurrency } from '@/lib/copy/roi';
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
  { text: "Inteligência de decisão completa", detail: "IA com 10.000 tokens de análise estratégica" },
  { text: "5 anos de histórico", detail: "Acesso ao maior acervo de oportunidades" },
  { text: "Cobertura nacional", detail: "Todos os estados e setores monitorados" },
  { text: "Processamento prioritário", detail: "Resultados em segundos, não minutos" },
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

/**
 * Check if user is privileged (admin, master, owner).
 */
function isPrivilegedUser(isAdmin: boolean, userProfile?: UserProfile | null): boolean {
  if (isAdmin) return true;
  if (userProfile?.is_admin) return true;
  if (userProfile?.plan_id && ["master"].includes(userProfile.plan_id)) return true;
  return false;
}

export default function PlanosPage() {
  const { session, user, isAdmin, loading: authLoading } = useAuth();
  const { trackEvent } = useAnalytics();
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [stripeRedirecting, setStripeRedirecting] = useState(false);
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("monthly");
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

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

  const currentPricing = PRICING[billingPeriod];
  const userIsPrivileged = isPrivilegedUser(isAdmin, userProfile);
  const isAlreadyPro = userProfile?.plan_id === "smartlic_pro";

  // Privileged users see a different view
  if (!authLoading && !profileLoading && userIsPrivileged) {
    return (
      <div className="min-h-screen bg-[var(--canvas)] py-12 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--brand-blue)]/10 flex items-center justify-center">
              <svg role="img" aria-label="Ícone" className="w-8 h-8 text-[var(--brand-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-3">
              Você possui acesso completo
            </h1>
            <p className="text-[var(--ink-secondary)] mb-6">
              Todas as funcionalidades do SmartLic estão disponíveis para você, sem restrições.
            </p>
            <Link
              href="/buscar"
              className="inline-block px-6 py-3 border border-[var(--border)] text-[var(--ink)] rounded-button font-semibold hover:bg-[var(--surface-1)] transition-colors"
            >
              Iniciar análise
            </Link>
          </div>
        </div>
      </div>
    );
  }

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
          <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-8 text-center shadow-xl max-w-sm mx-4">
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
          <div className="mb-8 p-4 bg-[var(--success-subtle)] text-[var(--success)] rounded-card text-center">
            {statusMsg}
          </div>
        )}

        {/* Already Pro Banner */}
        {isAlreadyPro && (
          <div className="mb-8 p-4 bg-[var(--brand-blue)]/10 border border-[var(--brand-blue)]/30 rounded-card text-center">
            <p className="font-semibold text-[var(--ink)]">Você já possui o SmartLic Pro ativo.</p>
            <Link href="/conta" className="text-sm text-[var(--brand-blue)] hover:underline">
              Gerenciar acesso
            </Link>
          </div>
        )}

        {/* Billing Period Toggle */}
        <div className="flex justify-center mb-8">
          <PlanToggle value={billingPeriod} onChange={setBillingPeriod} />
        </div>

        {/* Single Plan Card — Centered */}
        <div className="max-w-lg mx-auto">
          <div className="bg-[var(--surface-0)] border-2 border-[var(--brand-blue)] rounded-card p-8 shadow-xl">
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
              onClick={handleCheckout}
              disabled={checkoutLoading || isAlreadyPro}
              className="w-full py-4 rounded-button text-lg font-bold transition-all
                bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] hover:shadow-lg
                disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {checkoutLoading ? "Processando..." : isAlreadyPro ? "Acesso já ativo" : "Começar Agora"}
            </button>

            <p className="mt-3 text-center text-xs text-[var(--ink-muted)]">
              Cancele quando quiser. Sem contrato de fidelidade. Pagamento seguro via Stripe.
            </p>
          </div>
        </div>

        {/* ROI Anchor Message */}
        <div className="mt-12 max-w-lg mx-auto">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-6 text-center">
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
              ROI de 7.8x em uma única oportunidade ganha
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
                className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card overflow-hidden"
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
            Continuar com período de avaliação
          </Link>
        </div>
      </div>
    </div>
  );
}
