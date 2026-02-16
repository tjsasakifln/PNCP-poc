"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import Link from "next/link";
import { Rocket, Zap, Trophy, CheckCircle } from "lucide-react";
import { useAnalytics } from "../../../hooks/useAnalytics";

const PLAN_DETAILS: Record<string, { name: string; icon: React.ReactNode; message: string }> = {
  smartlic_pro: {
    name: "SmartLic Pro",
    icon: <Trophy className="w-5 h-5 inline-block" />,
    message: "Você agora tem 1.000 análises/mês, exportação Excel completa e histórico de 5 anos.",
  },
  // Legacy plans (existing subscribers)
  consultor_agil: {
    name: "Consultor Ágil",
    icon: <Rocket className="w-5 h-5 inline-block" />,
    message: "Você agora tem 50 análises/mês e histórico de 30 dias.",
  },
  maquina: {
    name: "Máquina",
    icon: <Zap className="w-5 h-5 inline-block" />,
    message: "Você agora tem 300 análises/mês, exportação Excel e histórico de 1 ano.",
  },
  sala_guerra: {
    name: "Sala de Guerra",
    icon: <Trophy className="w-5 h-5 inline-block" />,
    message: "Você agora tem 1.000 análises/mês, processamento prioritário e histórico de 5 anos.",
  },
};

function ObrigadoContent() {
  const searchParams = useSearchParams();
  const { session } = useAuth();
  const { trackEvent } = useAnalytics();
  const [planId, setPlanId] = useState<string | null>(null);

  useEffect(() => {
    const plan = searchParams.get("plan");
    if (plan) setPlanId(plan);
  }, [searchParams]);

  useEffect(() => {
    if (planId) {
      trackEvent("checkout_completed", { plan_id: planId });
    }
  }, [planId]); // eslint-disable-line react-hooks/exhaustive-deps

  const details = planId ? PLAN_DETAILS[planId] : null;

  return (
    <div className="min-h-screen bg-[var(--canvas)] flex items-center justify-center px-4">
      <div className="max-w-lg w-full text-center">
        <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-8 shadow-lg">
          {/* Success Icon */}
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--success)]/10 flex items-center justify-center">
            <CheckCircle className="w-8 h-8 text-[var(--success)]" />
          </div>

          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">
            Assinatura confirmada!
          </h1>

          {details ? (
            <>
              <p className="text-lg text-[var(--ink-secondary)] mb-4">
                Bem-vindo ao plano <strong>{details.name}</strong> {details.icon}
              </p>
              <p className="text-sm text-[var(--ink-muted)] mb-6">{details.message}</p>
            </>
          ) : (
            <p className="text-[var(--ink-secondary)] mb-6">
              Seu plano está ativo. Obrigado pela confiança!
            </p>
          )}

          <div className="space-y-3">
            <Link
              href="/buscar"
              className="block w-full py-3 bg-[var(--brand-navy)] text-white rounded-button font-semibold hover:bg-[var(--brand-blue)] transition-colors"
            >
              Começar a buscar
            </Link>
            <Link
              href="/conta"
              className="block w-full py-3 border border-[var(--border)] text-[var(--ink)] rounded-button font-semibold hover:bg-[var(--surface-1)] transition-colors"
            >
              Ver minha conta
            </Link>
          </div>

          {session?.user?.email && (
            <p className="mt-6 text-xs text-[var(--ink-muted)]">
              Um recibo será enviado para {session.user.email}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ObrigadoPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[var(--canvas)] flex items-center justify-center">
        <div className="animate-pulse text-[var(--ink-muted)]">Carregando...</div>
      </div>
    }>
      <ObrigadoContent />
    </Suspense>
  );
}
