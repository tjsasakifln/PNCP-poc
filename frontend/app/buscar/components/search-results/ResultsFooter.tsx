"use client";

import { useState } from "react";
import Link from "next/link";
import type { BuscaResult } from "../../../types";
import { TrialUpsellCTA } from "../../../../components/billing/TrialUpsellCTA";

interface ResultsFooterProps {
  result: BuscaResult;
  rawCount: number;
  searchMode: "setor" | "termos";
  sectorName: string;
  ufsSelecionadas: Set<string>;
  termosArray: string[];
  // Download
  onDownload: () => void;
  downloadLoading: boolean;
  downloadError: string | null;
  downloadCompleted: boolean;
  // Auth
  planInfo: {
    plan_id: string;
    subscription_status?: string;
    capabilities: { allow_excel: boolean; max_requests_per_month: number };
  } | null;
  session: { access_token: string } | null;
  isTrialExpired?: boolean;
  paywallApplied?: boolean;
  totalBeforePaywall?: number | null;
  onShowUpgradeModal: (plan?: string, source?: string) => void;
}

/**
 * TD-007: Footer section — export CTAs, stats, source badges, timestamps, upsell CTAs.
 */
export function ResultsFooter({
  result, rawCount, searchMode, sectorName, ufsSelecionadas, termosArray,
  onDownload, downloadLoading, downloadError, downloadCompleted,
  planInfo, session, isTrialExpired, paywallApplied, totalBeforePaywall,
  onShowUpgradeModal,
}: ResultsFooterProps) {
  const [showSourceBadges, setShowSourceBadges] = useState(false);

  return (
    <>
      {/* Export CTAs */}
      {paywallApplied && totalBeforePaywall ? (
        <div className="relative">
          <button onClick={onDownload} disabled={downloadLoading} className="w-full bg-surface-0 border-2 border-blue-500 text-blue-700 dark:text-blue-300 py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-all duration-200 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed" data-testid="excel-paywall-button" title={`Assine o SmartLic Pro para exportar todos os ${totalBeforePaywall} resultados`}>
            {downloadLoading ? (<><svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-label="Carregando" role="img"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>Preparando preview...</>) : (<><svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>Baixar Preview ({result.licitacoes.length} resultados)</>)}
          </button>
        </div>
      ) : isTrialExpired ? (
        <Link href="/planos" className="w-full bg-surface-0 border-2 border-amber-500 text-amber-700 dark:text-amber-300 py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold hover:bg-amber-50 dark:hover:bg-amber-900/10 transition-all duration-200 flex items-center justify-center gap-3" data-testid="excel-trial-expired-button"><svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>Ative seu plano para exportar</Link>
      ) : !planInfo?.capabilities.allow_excel ? (
        <Link href="/planos" className="w-full bg-surface-0 border-2 border-brand-navy text-brand-navy py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold hover:bg-brand-blue-subtle transition-all duration-200 flex items-center justify-center gap-3" aria-label="Assine um plano para exportar resultados em Excel e Google Sheets"><svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>Assine para exportar resultados e acessar funcionalidades premium</Link>
      ) : null}

      {/* Alert creation */}
      {session?.access_token && result && (
        <a href={`/alertas?from_search=1&setor=${encodeURIComponent(searchMode === "setor" ? (result as BuscaResult & { setor_id?: string }).setor_id || "" : "")}&ufs=${encodeURIComponent(Array.from(ufsSelecionadas).join(","))}&keywords=${encodeURIComponent(searchMode === "termos" ? termosArray.join(",") : "")}`} className="w-full bg-surface-0 border-2 border-brand-navy text-brand-navy py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold hover:bg-brand-blue-subtle transition-all duration-200 flex items-center justify-center gap-3"><svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" /></svg>Criar alerta a partir desta análise</a>
      )}

      {/* Download Error */}
      {downloadError && (
        <div className="p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-card" role="alert"><p className="text-sm sm:text-base font-medium text-error">{downloadError}</p></div>
      )}

      {/* Stats + Source badges + Timestamp */}
      <div className="text-xs sm:text-sm text-ink-muted text-center space-y-1">
        {rawCount > 0 && (
          <p>
            {result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'oportunidade selecionada' : 'oportunidades selecionadas'} de {rawCount.toLocaleString("pt-BR")} analisadas
            {searchMode === "setor" && sectorName !== "Licitações" ? ` para o setor ${sectorName.toLowerCase()}` : ''}
            {result.sources_used && result.sources_used.length > 1 && (
              <span className="ml-1 cursor-help border-b border-dotted border-ink-faint" title={result.source_stats?.filter((s: { status: string }) => s.status === "success" || s.status === "partial").map((s: { source_code: string; record_count: number }) => `${s.source_code}: ${s.record_count} registros`).join('\n') || ''}>(dados de multiplas fontes)</span>
            )}
          </p>
        )}
        {result.is_partial && !result.cached && result.sources_used && result.sources_used.length > 0 && (
          <p className="text-amber-600 dark:text-amber-400">Análise concluída | Fonte temporariamente indisponível (dados podem estar incompletos)</p>
        )}
        {result.source_stats && result.source_stats.length > 1 && (
          <div className="space-y-1">
            <button onClick={() => setShowSourceBadges(!showSourceBadges)} className="text-ink-faint hover:text-ink-secondary transition-colors text-xs underline-offset-2 hover:underline" aria-expanded={showSourceBadges}>{showSourceBadges ? 'Ocultar fontes' : 'Mostrar fontes'}</button>
            {showSourceBadges && (
              <div className="flex items-center justify-center gap-2 animate-fade-in">
                {result.source_stats.filter((s: { status: string }) => s.status === "success" || s.status === "partial").map((s: { source_code: string; record_count: number; status: string }) => (
                  <span key={s.source_code} className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${s.source_code === 'PNCP' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'}`}>
                    {s.source_code}: {s.record_count}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
        {result.ultima_atualizacao && (
          <p className="text-ink-faint">
            <svg className="w-3.5 h-3.5 inline mr-1 -mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            Atualizado em {new Date(result.ultima_atualizacao).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })}
          </p>
        )}
      </div>

      {/* Post-search/download CTAs */}
      {result.resumo.total_oportunidades >= 10 && <TrialUpsellCTA variant="post-search" planId={planInfo?.plan_id} subscriptionStatus={planInfo?.subscription_status} contextData={{ opportunities: result.resumo.total_oportunidades }} />}
      {downloadCompleted && <TrialUpsellCTA variant="post-download" planId={planInfo?.plan_id} subscriptionStatus={planInfo?.subscription_status} contextData={{ exportLimit: planInfo?.capabilities.max_requests_per_month ?? 1000 }} />}

      <p className="text-center text-sm text-ink-muted py-2" data-testid="return-invitation">Novas oportunidades são publicadas diariamente. Volte amanhã para conferir.</p>
    </>
  );
}
