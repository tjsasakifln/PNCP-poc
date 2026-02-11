"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import Link from "next/link";

const PLAN_DETAILS: Record<string, { name: string; emoji: string; message: string }> = {
  consultor_agil: {
    name: "Consultor Agil",
    emoji: "\u{1F680}",
    message: "Voce agora tem 50 buscas/mes e historico de 30 dias.",
  },
  maquina: {
    name: "Maquina",
    emoji: "\u{26A1}",
    message: "Voce agora tem 300 buscas/mes, download Excel e historico de 1 ano.",
  },
  sala_guerra: {
    name: "Sala de Guerra",
    emoji: "\u{1F3C6}",
    message: "Voce agora tem 1.000 buscas/mes, processamento prioritario e historico de 5 anos.",
  },
};

function ObrigadoContent() {
  const searchParams = useSearchParams();
  const { session } = useAuth();
  const [planId, setPlanId] = useState<string | null>(null);

  useEffect(() => {
    const plan = searchParams.get("plan");
    if (plan) setPlanId(plan);
  }, [searchParams]);

  const details = planId ? PLAN_DETAILS[planId] : null;

  return (
    <div className="min-h-screen bg-[var(--canvas)] flex items-center justify-center px-4">
      <div className="max-w-lg w-full text-center">
        <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-8 shadow-lg">
          {/* Success Icon */}
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--success)]/10 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-[var(--success)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>

          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">
            Assinatura confirmada!
          </h1>

          {details ? (
            <>
              <p className="text-lg text-[var(--ink-secondary)] mb-4">
                Bem-vindo ao plano <strong>{details.name}</strong> {details.emoji}
              </p>
              <p className="text-sm text-[var(--ink-muted)] mb-6">{details.message}</p>
            </>
          ) : (
            <p className="text-[var(--ink-secondary)] mb-6">
              Seu plano esta ativo. Obrigado pela confianca!
            </p>
          )}

          <div className="space-y-3">
            <Link
              href="/buscar"
              className="block w-full py-3 bg-[var(--brand-navy)] text-white rounded-button font-semibold hover:bg-[var(--brand-blue)] transition-colors"
            >
              Comecar a buscar
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
              Um recibo sera enviado para {session.user.email}
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
