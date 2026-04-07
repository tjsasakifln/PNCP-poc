"use client";

import Link from "next/link";
import { safeGetItem } from "../../../lib/storage";

interface OnboardingEmptyStateProps {
  onAdjustFilters: () => void;
}

export function OnboardingEmptyState({ onAdjustFilters }: OnboardingEmptyStateProps) {
  // Zero-churn P1 §6.1: Check if user skipped onboarding
  const hasCompletedOnboarding = safeGetItem("smartlic-onboarding-completed") === "true";

  return (
    <div className="mb-4 p-6 rounded-lg bg-[var(--surface-1)] border border-[var(--border)] text-center">
      {!hasCompletedOnboarding && (
        <div className="mb-4 p-3 rounded-lg bg-[var(--brand-blue)]/5 border border-[var(--brand-blue)]/20">
          <p className="text-sm text-[var(--brand-blue)] font-medium mb-2">
            Configure seu perfil para melhores resultados
          </p>
          <p className="text-xs text-[var(--ink-secondary)] mb-3">
            O onboarding ajuda a IA a encontrar oportunidades mais relevantes para seu setor.
          </p>
          <Link
            href="/onboarding"
            className="inline-flex px-4 py-2 rounded-lg bg-[var(--brand-blue)] text-white text-sm font-medium hover:bg-[var(--brand-blue-hover)] transition-colors"
          >
            Configurar perfil
          </Link>
        </div>
      )}

      <svg className="w-12 h-12 mx-auto mb-3 text-[var(--ink-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <h3 className="text-lg font-semibold text-[var(--ink)] mb-2">
        Sua análise foi concluída
      </h3>
      <p className="text-sm text-[var(--ink-secondary)] mb-4 max-w-md mx-auto">
        Não encontramos oportunidades compatíveis no período selecionado. Isso acontece em análises mais específicas — e pode mudar nos próximos dias.
      </p>
      <div className="space-y-2 text-sm text-[var(--ink-secondary)] mb-4">
        <p>Para ampliar resultados, tente:</p>
        <ul className="list-disc list-inside text-left max-w-sm mx-auto space-y-1">
          <li>Incluir estados vizinhos</li>
          <li>Ampliar a faixa de valor estimado</li>
          <li>Estender o período para 15 ou 30 dias</li>
        </ul>
      </div>
      <div className="mt-3 mb-4 text-center">
        <Link href="/ajuda#como-buscar" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
          Precisa de ajuda?
        </Link>
      </div>
      <button
        onClick={onAdjustFilters}
        className="px-4 py-2 rounded-lg bg-[var(--brand-blue)] text-white text-sm font-medium hover:bg-[var(--brand-blue-hover)] transition-colors"
      >
        Refinar análise
      </button>
    </div>
  );
}
