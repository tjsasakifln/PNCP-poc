"use client";

import { useState } from "react";
import { useUser } from "../../../contexts/UserContext";
import { getPlanDisplayName } from "../../../lib/plans";
import { CancelSubscriptionModal } from "../../../components/account/CancelSubscriptionModal";
import { AlertPreferences } from "./AlertPreferences";
import Link from "next/link";

/**
 * DEBT-011 FE-001: /conta/plano — Plan/subscription management + alerts.
 */

export default function PlanoPage() {
  const { user, session, authLoading, planInfo, planError, isFromCache, cachedAt, refresh } = useUser();
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancellingEndsAt, setCancellingEndsAt] = useState<string | null>(null);

  if (authLoading) {
    return <div className="flex items-center justify-center py-12"><p className="text-[var(--ink-secondary)]">Carregando...</p></div>;
  }
  if (!user || !session) {
    return <div className="text-center py-12"><p className="text-[var(--ink-secondary)] mb-4">Faça login para acessar sua conta</p><Link href="/login" className="text-[var(--brand-blue)] hover:underline">Ir para login</Link></div>;
  }

  return (
    <div className="space-y-6">
      {/* Plan Status */}
      <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card" data-testid="plan-section">
        <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Seu Acesso ao SmartLic</h2>

        {isFromCache && cachedAt && (
          <div className="mb-4 p-3 bg-[var(--warning-subtle)] rounded-input text-sm text-[var(--warning)] flex items-center gap-2" data-testid="plan-cache-notice">
            <svg aria-hidden="true" className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Verificado há {Math.max(1, Math.round((Date.now() - cachedAt) / 60000))} min
          </div>
        )}

        {planError && !planInfo && (
          <div className="text-center py-4" data-testid="plan-error">
            <p className="text-[var(--ink-secondary)] mb-3">Não foi possível verificar seu plano.</p>
            <button onClick={() => refresh()} className="px-4 py-2 rounded-button bg-[var(--brand-navy)] text-white text-sm font-medium hover:bg-[var(--brand-blue)] transition-colors">Tentar novamente</button>
          </div>
        )}

        {planInfo ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-[var(--ink-muted)]">Status:</span>
              {planInfo.plan_id === "free_trial" ? (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-400">Período de avaliação</span>
              ) : planInfo.subscription_status === "active" ? (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400">Ativo</span>
              ) : (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">Expirado</span>
              )}
            </div>

            {/* Trial info */}
            {planInfo.plan_id === "free_trial" && planInfo.trial_expires_at && (() => {
              const daysLeft = Math.max(0, Math.ceil((new Date(planInfo.trial_expires_at!).getTime() - Date.now()) / 86400000));
              const used = planInfo.quota_used ?? 0;
              const total = planInfo.capabilities.max_requests_per_month ?? 3;
              const usagePct = total > 0 ? Math.min(Math.round((used / total) * 100), 100) : 0;
              return (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm"><span className="text-[var(--ink-secondary)]">Dias restantes</span><span className="font-medium text-[var(--ink)]">{daysLeft} de 7</span></div>
                  <div className="flex items-center justify-between text-sm"><span className="text-[var(--ink-secondary)]">Análises usadas</span><span className="font-medium text-[var(--ink)]">{used} de {total}</span></div>
                  <div className="w-full h-2 bg-[var(--surface-1)] rounded-full overflow-hidden">{/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width and backgroundColor are computed from quota usage percentage */}<div className="h-full rounded-full transition-all duration-500" style={{ width: `${usagePct}%`, backgroundColor: usagePct > 80 ? "var(--error)" : "var(--brand-blue)" }} /></div>
                  <p className="text-xs text-[var(--ink-muted)] text-right">{usagePct}% utilizado</p>
                </div>
              );
            })()}

            {/* Subscriber info */}
            {planInfo.plan_id !== "free_trial" && planInfo.subscription_status === "active" && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm"><span className="text-[var(--ink-secondary)]">Acesso</span><span className="font-medium text-[var(--ink)]">{getPlanDisplayName(planInfo.plan_id, planInfo.plan_name)}</span></div>
                <div className="flex items-center justify-between text-sm"><span className="text-[var(--ink-secondary)]">Análises este mês</span><span className="font-medium text-[var(--ink)]">{planInfo.quota_used} de {planInfo.capabilities.max_requests_per_month === -1 ? "ilimitado" : planInfo.capabilities.max_requests_per_month}</span></div>
                {planInfo.subscription_end_date
                  ? <div className="flex items-center justify-between text-sm"><span className="text-[var(--ink-secondary)]">Próxima renovação</span><span className="font-medium text-[var(--ink)]">{new Date(planInfo.subscription_end_date).toLocaleDateString("pt-BR", { day: "2-digit", month: "long" })}</span></div>
                  : planInfo.quota_reset_date
                    ? <div className="flex items-center justify-between text-sm"><span className="text-[var(--ink-secondary)]">Próximo reset de cota</span><span className="font-medium text-[var(--ink)]">{new Date(planInfo.quota_reset_date).toLocaleDateString("pt-BR", { day: "2-digit", month: "long" })}</span></div>
                    : null
                }
              </div>
            )}

            {cancellingEndsAt && (
              <div className="flex items-center gap-3 p-3 bg-[var(--warning-subtle)] rounded-input">
                <svg aria-hidden="true" className="w-5 h-5 text-[var(--warning)] flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <div><p className="text-sm font-medium text-[var(--warning)]">Ativo ate {new Date(cancellingEndsAt).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })}</p></div>
              </div>
            )}

            <div className="pt-2 space-y-3">
              {planInfo.plan_id === "free_trial" ? (
                <Link href="/planos" className="w-full py-3 px-4 rounded-button bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] transition-colors flex items-center justify-center gap-2 font-medium" data-testid="plan-cta-primary">Assinar SmartLic Pro</Link>
              ) : planInfo.subscription_status === "active" && !cancellingEndsAt ? (
                <Link href="/planos" className="w-full py-3 px-4 rounded-button border border-[var(--brand-blue)] text-[var(--brand-blue)] bg-transparent hover:bg-[var(--brand-blue-subtle)] transition-colors flex items-center justify-center gap-2 font-medium text-sm" data-testid="plan-cta-primary">Gerenciar acesso</Link>
              ) : planInfo.subscription_status !== "active" ? (
                <Link href="/planos" className="w-full py-3 px-4 rounded-button bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] transition-colors flex items-center justify-center gap-2 font-medium" data-testid="plan-cta-primary">Reativar SmartLic Pro</Link>
              ) : null}

              {planInfo.subscription_status === "active" && !cancellingEndsAt && planInfo.plan_id !== "free_trial" && (
                <button onClick={() => setShowCancelModal(true)} className="w-full text-center text-xs text-[var(--ink-muted)] hover:text-[var(--error)] transition-colors py-2" data-testid="cancel-link">Cancelar acesso</button>
              )}
            </div>
          </div>
        ) : (
          <div className="animate-pulse space-y-3"><div className="h-4 w-32 bg-[var(--surface-1)] rounded" /><div className="h-4 w-48 bg-[var(--surface-1)] rounded" /><div className="h-10 w-full bg-[var(--surface-1)] rounded-button" /></div>
        )}
      </div>

      <AlertPreferences accessToken={session.access_token} />

      <CancelSubscriptionModal isOpen={showCancelModal} onClose={() => setShowCancelModal(false)} onCancelled={(endsAt) => { setShowCancelModal(false); setCancellingEndsAt(endsAt); }} accessToken={session.access_token} />
    </div>
  );
}
