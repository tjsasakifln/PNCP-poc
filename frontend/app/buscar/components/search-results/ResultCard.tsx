"use client";

import Link from "next/link";
import type { BuscaResult } from "../../../types";
import { LlmSourceBadge } from "../LlmSourceBadge";
import { formatCurrencyBR } from "../../../../lib/format-currency";
import ViabilityBadge, { type ViabilityFactors } from "@/components/ViabilityBadge";

interface ResultCardProps {
  result: BuscaResult;
  trialPhase?: "full_access" | "limited_access" | "not_trial";
  isProfileComplete?: boolean;
  bannerDismissed: boolean;
  onDismissBanner: () => void;
}

/**
 * TD-007 AC1: ResultCard — Summary card for search results.
 * Displays executive summary, recommendations, highlights, value totals,
 * urgency alerts, and sector insights.
 */
export function ResultCard({
  result,
  trialPhase,
  isProfileComplete = true,
  bannerDismissed,
  onDismissBanner,
}: ResultCardProps) {
  return (
    <div className="p-4 sm:p-6 bg-brand-blue-subtle border border-accent rounded-card relative">
      {/* CRIT-005 AC16: LLM source badge near the summary */}
      <div className="flex items-center gap-2 mb-3">
        <LlmSourceBadge llmSource={result.llm_source} />
      </div>

      {/* STORY-320 AC9: Truncate AI summary in limited_access */}
      <p className="text-base sm:text-lg leading-relaxed text-ink">
        {trialPhase === "limited_access"
          ? result.resumo.resumo_executivo.split('. ').slice(0, 2).join('. ') + '...'
          : result.resumo.resumo_executivo}
      </p>

      {/* STORY-441: Inline CTA after truncated summary */}
      {trialPhase === "limited_access" && (
        <p className="mt-1 text-sm text-blue-700 dark:text-blue-400">
          <Link
            href="/planos"
            className="underline underline-offset-2 hover:text-blue-900 dark:hover:text-blue-300 font-medium"
            data-testid="summary-unlock-cta"
          >
            Desbloqueie o resumo completo + recomendação de participação →
          </Link>
        </p>
      )}

      {/* STORY-320 AC9: Paywall overlay on summary */}
      {trialPhase === "limited_access" && (
        <div className="mt-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-700/40 rounded-lg flex items-center justify-between">
          <span className="text-sm text-blue-800 dark:text-blue-200">
            Ver análise completa com SmartLic Pro
          </span>
          <Link
            href="/planos"
            className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline"
            data-testid="summary-paywall-cta"
          >
            Assinar
          </Link>
        </div>
      )}

      <div className="flex flex-col sm:flex-row flex-wrap gap-4 sm:gap-8 mt-4 sm:mt-6">
        <div>
          <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-brand-navy dark:text-brand-blue">
            {result.resumo.total_oportunidades}
          </span>
          <span className="text-sm sm:text-base text-ink-secondary block mt-1">{result.resumo.total_oportunidades === 1 ? 'licitação' : 'licitações'}</span>
        </div>
        <div>
          <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-brand-navy dark:text-brand-blue">
            {result.resumo.valor_total > 0 ? formatCurrencyBR(result.resumo.valor_total) : "Valor não divulgado"}
          </span>
          <span className="text-sm sm:text-base text-ink-secondary block mt-1">{result.resumo.valor_total > 0 ? "valor total" : "valor não disponível nas fontes"}</span>
        </div>
      </div>

      {/* AC11: Insight Setorial Banner */}
      {result.resumo.insight_setorial && (
        <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-brand-blue-subtle/50 border border-accent/30 rounded-card">
          <p className="text-sm sm:text-base text-ink-secondary leading-relaxed">
            <span className="font-semibold text-brand-navy dark:text-brand-blue">Contexto do setor: </span>
            {result.resumo.insight_setorial}
          </p>
        </div>
      )}

      {/* AC12: Multiple Urgency Alerts */}
      {result.resumo.alertas_urgencia && result.resumo.alertas_urgencia.length > 0 ? (
        <div className="mt-4 sm:mt-6 space-y-2" role="alert">
          {result.resumo.alertas_urgencia.map((alerta, i) => (
            <div key={i} className="p-3 sm:p-4 bg-warning-subtle border border-warning/20 rounded-card">
              <p className="text-sm sm:text-base font-medium text-warning">{alerta}</p>
            </div>
          ))}
        </div>
      ) : result.resumo.alerta_urgencia ? (
        <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-warning-subtle border border-warning/20 rounded-card" role="alert">
          <p className="text-sm sm:text-base font-medium text-warning">
            <span aria-hidden="true">Atenção: </span>
            {result.resumo.alerta_urgencia}
          </p>
        </div>
      ) : null}

      {/* AC10 + UX-350 AC5-AC8: Recommendation Cards with strategic context */}
      {result.resumo.recomendacoes && result.resumo.recomendacoes.length > 0 && (
        <div className="mt-4 sm:mt-6">
          <h4 className="text-base sm:text-lg font-semibold font-display text-ink mb-3 sm:mb-4">Recomendações Estratégicas:</h4>

          {/* AC6/AC16: Incomplete profile banner with CTA */}
          {!isProfileComplete && !bannerDismissed && (
            <div className="mb-3 p-3 bg-amber-50 dark:bg-amber-900/15 border border-amber-200 dark:border-amber-700/40 rounded-card flex items-center gap-3" data-testid="profile-incomplete-banner">
              <svg className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-amber-800 dark:text-amber-200 flex-1">
                Complete seu perfil para recomendações mais precisas.{' '}
                <Link href="/conta" className="font-semibold underline underline-offset-2 hover:text-amber-900 dark:hover:text-amber-100">
                  Completar perfil →
                </Link>
              </p>
              <button
                type="button"
                onClick={onDismissBanner}
                className="ml-auto flex-shrink-0 text-amber-600 dark:text-amber-400 hover:text-amber-900 dark:hover:text-amber-100 transition-colors"
                aria-label="Fechar aviso"
                data-testid="profile-banner-dismiss"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}

          {/* AC8: AI transparency label */}
          <p className="text-xs text-ink-muted mb-3" data-testid="ai-transparency-label">
            Análise gerada por IA com base no seu perfil e no edital
          </p>

          <div className="space-y-3">
            {result.resumo.recomendacoes.map((rec, i) => {
              const matchedBid = result.licitacoes.find(l =>
                rec.oportunidade && (
                  l.orgao && rec.oportunidade.includes(l.orgao) ||
                  l.objeto && rec.oportunidade.includes(l.objeto.substring(0, 40))
                )
              );
              return (
                <div
                  key={i}
                  className="p-3 sm:p-4 bg-surface border border-border rounded-card animate-fade-in-up"
                  style={{ animationDelay: `${i * 80}ms` }}
                >
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    {/* STORY-440: ViabilityBadge per recommendation */}
                    {matchedBid?.viability_level && (
                      <span data-tour={i === 0 ? "viability-badge" : undefined}>
                        <ViabilityBadge
                          level={matchedBid.viability_level}
                          score={matchedBid.viability_score ?? undefined}
                          factors={(matchedBid.viability_factors as ViabilityFactors | null | undefined) ?? undefined}
                          valueSource={matchedBid._value_source ?? undefined}
                        />
                      </span>
                    )}
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                      rec.urgencia === "alta"
                        ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                        : rec.urgencia === "media"
                        ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300"
                        : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                    }`}>
                      {rec.urgencia === "alta" ? "Urgente" : rec.urgencia === "media" ? "Atenção" : "Normal"}
                    </span>
                    <span className="text-sm font-semibold text-brand-navy dark:text-brand-blue">
                      {rec.valor > 0 ? `R$ ${rec.valor.toLocaleString("pt-BR")}` : "Valor não divulgado"}
                    </span>
                  </div>
                  <p className="text-sm sm:text-base font-medium text-ink mb-1">{rec.oportunidade}</p>
                  <p className="text-sm text-brand-navy dark:text-brand-blue font-medium mb-1">{rec.acao_sugerida}</p>
                  <p className="text-xs sm:text-sm text-ink-secondary">{rec.justificativa}</p>
                  {matchedBid?.link && (
                    <a
                      href={matchedBid.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-brand-navy dark:text-brand-blue hover:underline"
                      data-testid="rec-edital-link"
                    >
                      Ver edital na fonte oficial
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {result.resumo.destaques && result.resumo.destaques.length > 0 && (
        <div className="mt-4 sm:mt-6">
          <h4 className="text-base sm:text-lg font-semibold font-display text-ink mb-2 sm:mb-3">Destaques:</h4>
          <ul className="list-disc list-inside text-sm sm:text-base space-y-2 text-ink-secondary">
            {result.resumo.destaques.map((d, i) => (
              <li key={i} className="animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>{d}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
