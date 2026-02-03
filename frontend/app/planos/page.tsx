"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";

interface Plan {
  id: string;
  name: string;
  description: string;
  max_searches: number | null;
  price_brl: number;
  duration_days: number | null;
}

export default function PlanosPage() {
  const { session, user } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);

  // Check URL params for success/cancelled
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("success")) setStatusMsg("Pagamento realizado com sucesso! Seu plano esta ativo.");
    if (params.get("cancelled")) setStatusMsg("Pagamento cancelado.");
  }, []);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
      const res = await fetch(`${backendUrl}/plans`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      // Hide free and master from public listing
      setPlans(data.plans.filter((p: Plan) => p.id !== "free" && p.id !== "master"));
    } catch {
      setPlans([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckout = async (planId: string) => {
    if (!session) {
      window.location.href = "/login";
      return;
    }
    setCheckoutLoading(planId);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
      const res = await fetch(`${backendUrl}/checkout?plan_id=${planId}`, {
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

  const getPlanLabel = (plan: Plan) => {
    if (plan.duration_days === 30) return "/mes";
    if (plan.duration_days === 365) return "/ano";
    return "";
  };

  const isPopular = (id: string) => id === "monthly";

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-12 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-display font-bold text-[var(--ink)] mb-3">
            Escolha seu plano
          </h1>
          <p className="text-[var(--ink-secondary)] max-w-lg mx-auto">
            Comece gratis com 3 buscas. Escolha um plano para acesso completo
            ao monitoramento de licitacoes.
          </p>
        </div>

        {statusMsg && (
          <div className="mb-8 p-4 bg-[var(--success-subtle)] text-[var(--success)] rounded-card text-center">
            {statusMsg}
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
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={`relative p-6 bg-[var(--surface-0)] border rounded-card
                  ${isPopular(plan.id)
                    ? "border-[var(--brand-blue)] shadow-lg"
                    : "border-[var(--border)]"
                  }`}
              >
                {isPopular(plan.id) && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5
                                  bg-[var(--brand-blue)] text-white text-xs font-semibold rounded-full">
                    Mais popular
                  </div>
                )}

                <h3 className="text-lg font-semibold text-[var(--ink)] mb-1">{plan.name}</h3>
                <p className="text-sm text-[var(--ink-secondary)] mb-4">{plan.description}</p>

                <div className="mb-6">
                  <span className="text-3xl font-data font-bold text-[var(--ink)]">
                    {formatPrice(plan.price_brl)}
                  </span>
                  <span className="text-sm text-[var(--ink-muted)]">{getPlanLabel(plan)}</span>
                </div>

                <ul className="space-y-2 mb-6 text-sm text-[var(--ink-secondary)]">
                  <li className="flex items-center gap-2">
                    <span className="text-[var(--success)]">&#10003;</span>
                    {plan.max_searches ? `${plan.max_searches} buscas` : "Buscas ilimitadas"}
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-[var(--success)]">&#10003;</span>
                    Todos os setores
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-[var(--success)]">&#10003;</span>
                    Download Excel
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-[var(--success)]">&#10003;</span>
                    Resumo executivo IA
                  </li>
                  {!plan.max_searches && (
                    <li className="flex items-center gap-2">
                      <span className="text-[var(--success)]">&#10003;</span>
                      Historico completo
                    </li>
                  )}
                </ul>

                <button
                  onClick={() => handleCheckout(plan.id)}
                  disabled={checkoutLoading === plan.id}
                  className={`w-full py-3 rounded-button font-semibold transition-colors
                    disabled:opacity-50 disabled:cursor-not-allowed
                    ${isPopular(plan.id)
                      ? "bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)]"
                      : "border border-[var(--border)] text-[var(--ink)] hover:bg-[var(--surface-1)]"
                    }`}
                >
                  {checkoutLoading === plan.id ? "Redirecionando..." : "Assinar"}
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8 text-center">
          <Link href="/" className="text-sm text-[var(--ink-muted)] hover:underline">
            Voltar para buscas
          </Link>
        </div>
      </div>
    </div>
  );
}
