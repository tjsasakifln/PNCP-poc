"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import Link from "next/link";
import { Rocket, Zap, Trophy, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import { useAnalytics } from "../../../hooks/useAnalytics";

const PLAN_DETAILS: Record<string, { name: string; icon: React.ReactNode; message: string }> = {
  smartlic_pro: {
    name: "SmartLic Pro",
    icon: <Trophy className="w-5 h-5 inline-block" />,
    message: "Você agora tem 1.000 análises/mês, exportação Excel completa e histórico de 5 anos.",
  },
  consultor_agil: {
    name: "SmartLic Pro",
    icon: <Trophy className="w-5 h-5 inline-block" />,
    message: "Você agora tem 1.000 análises/mês, exportação Excel completa e histórico de 5 anos.",
  },
  maquina: {
    name: "SmartLic Pro",
    icon: <Trophy className="w-5 h-5 inline-block" />,
    message: "Você agora tem 1.000 análises/mês, exportação Excel completa e histórico de 5 anos.",
  },
  sala_guerra: {
    name: "SmartLic Pro",
    icon: <Trophy className="w-5 h-5 inline-block" />,
    message: "Você agora tem 1.000 análises/mês, exportação Excel completa e histórico de 5 anos.",
  },
};

const POLL_INTERVAL_MS = 5000;
const MAX_POLL_DURATION_MS = 120000; // 2 minutes

type ActivationStatus = "polling" | "active" | "timeout";

function ObrigadoContent() {
  const searchParams = useSearchParams();
  const { session } = useAuth();
  const { trackEvent } = useAnalytics();
  const [planId, setPlanId] = useState<string | null>(null);
  const [activationStatus, setActivationStatus] = useState<ActivationStatus>("polling");

  useEffect(() => {
    const plan = searchParams.get("plan");
    if (plan) setPlanId(plan);
  }, [searchParams]);

  useEffect(() => {
    if (planId) {
      trackEvent("checkout_completed", { plan_id: planId });
    }
  }, [planId]); // eslint-disable-line react-hooks/exhaustive-deps

  // GTM-FIX-016: Poll for subscription activation
  useEffect(() => {
    if (!session?.access_token || activationStatus === "active") return;

    const startTime = Date.now();
    const interval = setInterval(async () => {
      // Timeout after 2 minutes
      if (Date.now() - startTime > MAX_POLL_DURATION_MS) {
        setActivationStatus("timeout");
        clearInterval(interval);
        return;
      }

      try {
        const response = await fetch("/api/subscription-status", {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          if (data.status === "active") {
            setActivationStatus("active");
            clearInterval(interval);
          }
        }
      } catch {
        // Silently retry on next interval
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [session?.access_token, activationStatus]);

  const details = planId ? PLAN_DETAILS[planId] : null;

  return (
    <div className="min-h-screen bg-[var(--canvas)] flex items-center justify-center px-4">
      <div className="max-w-lg w-full text-center">
        <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-8 shadow-lg">
          {/* Status Icon */}
          <div className="w-16 h-16 mx-auto mb-6 rounded-full flex items-center justify-center"
               style={{ backgroundColor: activationStatus === "timeout" ? "var(--warning-subtle, #FEF3C7)" : "rgba(var(--success-rgb, 34,197,94), 0.1)" }}>
            {activationStatus === "polling" ? (
              <Loader2 className="w-8 h-8 text-[var(--brand-blue)] animate-spin" />
            ) : activationStatus === "timeout" ? (
              <AlertCircle className="w-8 h-8 text-[var(--warning, #F59E0B)]" />
            ) : (
              <CheckCircle className="w-8 h-8 text-[var(--success)]" />
            )}
          </div>

          {activationStatus === "polling" ? (
            <>
              <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">
                Ativando sua conta...
              </h1>
              <p className="text-[var(--ink-secondary)] mb-4">
                Estamos confirmando seu pagamento. Isso leva apenas alguns segundos.
              </p>
              <div className="flex items-center justify-center gap-2 text-sm text-[var(--ink-muted)]">
                <Loader2 className="w-4 h-4 animate-spin" />
                Verificando ativação...
              </div>
            </>
          ) : activationStatus === "timeout" ? (
            <>
              <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">
                Ativação em andamento
              </h1>
              <p className="text-[var(--ink-secondary)] mb-4">
                Seu pagamento foi recebido, mas a ativação está demorando mais que o esperado.
                Não se preocupe — seu acesso será liberado em breve.
              </p>
              <div className="p-4 bg-[var(--surface-1)] rounded-input text-left mb-4">
                <p className="text-sm text-[var(--ink-secondary)]">
                  Se o problema persistir, entre em contato:
                </p>
                <p className="text-sm font-medium text-[var(--ink)] mt-1">
                  suporte@smartlic.tech
                </p>
              </div>
            </>
          ) : (
            <>
              <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">
                Assinatura confirmada!
              </h1>
              {details ? (
                <>
                  <p className="text-lg text-[var(--ink-secondary)] mb-4">
                    Bem-vindo ao <strong>{details.name}</strong> {details.icon}
                  </p>
                  <p className="text-sm text-[var(--ink-muted)] mb-6">{details.message}</p>
                </>
              ) : (
                <p className="text-[var(--ink-secondary)] mb-6">
                  Seu acesso está ativo. Obrigado pela confiança!
                </p>
              )}
            </>
          )}

          <div className="space-y-3 mt-6">
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
