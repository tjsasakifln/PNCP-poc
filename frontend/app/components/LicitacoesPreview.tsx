"use client";

import { useState, useCallback, type ReactNode } from "react";
import Link from "next/link";
import type { LicitacaoItem, BidAnalysisItem } from "../types";
import ViabilityBadge from "../../components/ViabilityBadge";
import FeedbackButtons from "../../components/FeedbackButtons";
import CompatibilityBadge from "../../components/CompatibilityBadge";
import ActionLabel from "../../components/ActionLabel";
import DeepAnalysisModal from "../../components/DeepAnalysisModal";
import { AddToPipelineButton } from "./AddToPipelineButton";
import { formatCurrencyBR } from "../../lib/format-currency";
import { ShareAnalysisButton } from "../../components/ShareAnalysisButton";

interface LicitacoesPreviewProps {
  /** List of bid items to display */
  licitacoes: LicitacaoItem[];
  /** Number of items to show fully (rest will be blurred) */
  previewCount?: number;
  /** Whether Excel export is available for user's plan */
  excelAvailable: boolean;
  /** Callback when user clicks upgrade CTA */
  onUpgradeClick?: () => void;
  /** Active search terms for highlighting in bid descriptions */
  searchTerms?: string[];
  /** D-05: Search ID for feedback association */
  searchId?: string;
  /** D-05: Sector ID for feedback context */
  setorId?: string;
  /** D-05: Access token for authenticated feedback */
  accessToken?: string | null;
  /** STORY-259: Per-bid analysis from batch LLM call */
  bidAnalysis?: BidAnalysisItem[];
  /** STORY-259: Status of bid analysis batch job */
  bidAnalysisStatus?: "ready" | "processing" | null;
}

/**
 * LicitacoesPreview - Displays bid items with FREE tier blur effect.
 *
 * Shows first N items fully with links, rest are blurred without links
 * to encourage upgrade to paid plans.
 */
export function LicitacoesPreview({
  licitacoes,
  previewCount = 5,
  excelAvailable,
  onUpgradeClick,
  searchTerms = [],
  searchId,
  setorId,
  accessToken,
  bidAnalysis,
  bidAnalysisStatus,
}: LicitacoesPreviewProps) {
  /** STORY-259: Index bid analysis by bid_id for O(1) lookup */
  const bidAnalysisMap = bidAnalysis
    ? new Map(bidAnalysis.map((a) => [a.bid_id, a]))
    : null;
  /** AC5.4: Relevance badge based on score */
  const getRelevanceBadge = (score?: number | null) => {
    if (score == null) return null;
    if (score >= 0.7) {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
          Muito relevante
        </span>
      );
    }
    if (score >= 0.4) {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
          Relevante
        </span>
      );
    }
    return null;
  };

  /** AC5.5: Highlight matched terms in text using React elements (no innerHTML) */
  const highlightTerms = (text: string, terms: string[]): ReactNode => {
    if (!terms || terms.length === 0) return text;
    // Build a regex that matches any of the search terms (case-insensitive, accent-insensitive not needed here since matching is on displayed text)
    const escaped = terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    const pattern = new RegExp(`(${escaped.join("|")})`, "gi");
    const parts = text.split(pattern);
    if (parts.length === 1) return text;
    return parts.map((part, i) =>
      pattern.test(part) ? (
        <mark key={i} className="bg-yellow-200 dark:bg-yellow-800/50 text-inherit rounded-sm px-0.5">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  // UX-352 AC1: Removed "Fonte Oficial" badge — all sources are official, badge was redundant
  const getSourceBadge = (_source?: string) => null;

  /** C-02 AC5-AC7, AC11: Confidence badge with 3 visual levels + tooltip + accessibility */
  const getConfidenceBadge = (confidence?: "high" | "medium" | "low" | null) => {
    if (!confidence) return null;

    const config: Record<string, {
      label: string;
      tooltip: string;
      ariaLabel: string;
      bg: string;
      icon: React.ReactNode;
    }> = {
      high: {
        label: "Alta relevância",
        tooltip: "Alta densidade de termos relevantes para o setor selecionado",
        ariaLabel: "Relevância alta deste resultado para o seu perfil",
        bg: "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
        icon: (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        ),
      },
      medium: {
        label: "Relevância média",
        tooltip: "Relevância confirmada por avaliação de inteligência artificial",
        ariaLabel: "Relevância média deste resultado para o seu perfil",
        bg: "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
        icon: (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        ),
      },
      low: {
        label: "Avaliado por IA",
        tooltip: "Resultado com relevância possível, verificado por IA. Recomendamos revisar manualmente",
        ariaLabel: "Relevância baixa — verificado por IA, recomendamos revisar",
        bg: "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400",
        icon: (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      },
    };

    const c = config[confidence];
    if (!c) return null;

    return (
      <span
        className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${c.bg}`}
        title={c.tooltip}
        aria-label={c.ariaLabel}
        tabIndex={0}
        role="img"
      >
        {c.icon}
        {c.label}
      </span>
    );
  };

  /** GTM-FIX-028 AC12 + UX-352 AC2: Badge based on relevance_source
   *  AC2: Removed "Palavra-chave" badge (internal jargon). Only LLM badge remains. */
  const getRelevanceSourceBadge = (source?: string | null) => {
    if (!source) return null;
    // UX-352 AC2: "keyword" badge removed — was internal jargon meaningless to users
    // All LLM variants get the same blue "Validado por IA" badge
    if (source.startsWith("llm")) {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
          Validado por IA
        </span>
      );
    }
    return null;
  };

  if (!licitacoes || licitacoes.length === 0) {
    return null;
  }

  const visibleItems = licitacoes.slice(0, previewCount);
  const blurredItems = licitacoes.slice(previewCount);

  /** UX-401 AC4+AC5: Unified currency formatting with null/0 handling */
  const formatCurrency = (value: number | null | undefined): string => {
    if (value === null || value === undefined || value === 0) {
      return "Valor não informado";
    }
    return formatCurrencyBR(value);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-";
    const [year, month, day] = dateStr.split("-");
    return `${day}/${month}/${year}`;
  };

  /** AC2 + AC9: Get urgency color classes based on urgencia level */
  const getUrgenciaBadge = (item: LicitacaoItem) => {
    if (!item.data_encerramento) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 text-xs font-medium">
          Prazo não informado
        </span>
      );
    }
    const dias = item.dias_restantes;
    const urgencia = item.urgencia;

    let colorClasses = "bg-surface-2 text-ink-secondary"; // default gray
    let label = `Prazo final: ${formatDate(item.data_encerramento)}`;

    if (urgencia === "encerrada" || (dias != null && dias < 0)) {
      // GTM-FIX-042 AC1: expired bids show "Encerrada" in gray
      colorClasses = "bg-gray-100 dark:bg-gray-800 text-gray-500 line-through";
      label = `Encerrada: ${formatDate(item.data_encerramento)}`;
    } else if (dias === 0) {
      // GTM-FIX-042 AC1: last day
      colorClasses = "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300";
      label = `Último dia: ${formatDate(item.data_encerramento)}`;
    } else if (dias === 1) {
      // GTM-FIX-042 AC1: tomorrow
      colorClasses = "bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300";
      label = `Amanhã: ${formatDate(item.data_encerramento)}`;
    } else if (urgencia === "critica" || (dias != null && dias < 8)) {
      // UX-348 AC11: red (<8 days)
      colorClasses = "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300";
      label = `Urgente: ${formatDate(item.data_encerramento)} (${dias}d)`;
    } else if (urgencia === "alta" || (dias != null && dias <= 15)) {
      // UX-348 AC11: yellow (8-15 days)
      colorClasses = "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300";
      label = `Atenção: ${formatDate(item.data_encerramento)} (${dias}d)`;
    } else {
      // UX-348 AC11: green (>15 days)
      colorClasses = "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300";
      label = `Prazo final: ${formatDate(item.data_encerramento)}${dias != null ? ` (${dias}d)` : ''}`;
    }

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClasses}`}>
        {label}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-ink flex items-center gap-2">
        <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5 text-brand-navy" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        Oportunidades Encontradas
      </h3>

      {/* UX-352 AC7-AC8: Visible items — essential info visible, details expandable */}
      <div className="space-y-3">
        {visibleItems.map((item, index) => (
          <BidCard
            key={item.pncp_id || index}
            item={item}
            index={index}
            highlightTerms={highlightTerms}
            searchTerms={searchTerms}
            formatCurrency={formatCurrency}
            formatDate={formatDate}
            getRelevanceBadge={getRelevanceBadge}
            getRelevanceSourceBadge={getRelevanceSourceBadge}
            getConfidenceBadge={getConfidenceBadge}
            getSourceBadge={getSourceBadge}
            getUrgenciaBadge={getUrgenciaBadge}
            searchId={searchId}
            setorId={setorId}
            accessToken={accessToken}
            idPrefix="bid"
            bidAnalysis={bidAnalysisMap?.get(item.pncp_id || "") ?? null}
            bidAnalysisStatus={bidAnalysisStatus}
          />
        ))}
      </div>

      {/* Blurred items (FREE tier) */}
      {blurredItems.length > 0 && !excelAvailable && (
        <div className="relative">
          {/* Blur overlay with gradient */}
          <div className="absolute inset-0 z-10 bg-gradient-to-b from-transparent via-[var(--canvas)]/70 to-[var(--canvas)] pointer-events-none" />

          {/* Blurred content */}
          <div className="space-y-3 blur-sm select-none" aria-hidden="true">
            {blurredItems.slice(0, 3).map((item, index) => (
              <div
                key={`blurred-${index}`}
                className="p-4 bg-surface-0 border border-strong rounded-card opacity-60"
              >
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-base font-medium text-ink line-clamp-2 mb-1">
                      {item.objeto.substring(0, 50)}...
                    </h4>
                    <p className="text-sm text-ink-secondary truncate">
                      {item.orgao.substring(0, 30)}...
                    </p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-2 text-ink-muted text-xs">
                        {item.uf}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <span className="text-lg font-bold font-data text-ink-muted">
                      R$ ***
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Upgrade CTA overlay */}
          <div className="absolute inset-0 z-20 flex items-center justify-center">
            <div className="bg-surface-0 border border-brand-navy shadow-lg rounded-card p-6 max-w-sm text-center mx-4">
              <div className="w-12 h-12 mx-auto mb-4 bg-brand-blue-subtle rounded-full flex items-center justify-center">
                <svg
              role="img"
              aria-label="Ícone" className="w-6 h-6 text-brand-navy" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-ink mb-2">
                +{blurredItems.length} {blurredItems.length === 1 ? 'oportunidade oculta' : 'oportunidades ocultas'}
              </h4>
              <p className="text-sm text-ink-secondary mb-4">
                Assine para ver todas as oportunidades com links diretos e exportar para Excel.
              </p>
              <Link
                href="/planos"
                className="block w-full py-2.5 bg-brand-navy text-white rounded-button font-semibold hover:bg-brand-blue-hover transition-colors text-center"
              >
                Ver Planos
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Show remaining count for paid users who have Excel */}
      {blurredItems.length > 0 && excelAvailable && (
        <div className="space-y-3">
          {blurredItems.map((item, index) => (
            <BidCard
              key={item.pncp_id || `extra-${index}`}
              item={item}
              index={index}
              highlightTerms={highlightTerms}
              searchTerms={searchTerms}
              formatCurrency={formatCurrency}
              formatDate={formatDate}
              getRelevanceBadge={getRelevanceBadge}
              getRelevanceSourceBadge={getRelevanceSourceBadge}
              getConfidenceBadge={getConfidenceBadge}
              getSourceBadge={getSourceBadge}
              getUrgenciaBadge={getUrgenciaBadge}
              searchId={searchId}
              setorId={setorId}
              accessToken={accessToken}
              idPrefix="extra"
              bidAnalysis={bidAnalysisMap?.get(item.pncp_id || "") ?? null}
              bidAnalysisStatus={bidAnalysisStatus}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* UX-352 AC7-AC8: BidCard — essential info visible, details expandable       */
/* -------------------------------------------------------------------------- */

interface BidCardProps {
  item: LicitacaoItem;
  index: number;
  highlightTerms: (text: string, terms: string[]) => ReactNode;
  searchTerms: string[];
  formatCurrency: (value: number | null | undefined) => string;
  formatDate: (dateStr: string | null) => string;
  getRelevanceBadge: (score?: number | null) => ReactNode;
  getRelevanceSourceBadge: (source?: string | null) => ReactNode;
  getConfidenceBadge: (confidence?: "high" | "medium" | "low" | null) => ReactNode;
  getSourceBadge: (source?: string) => ReactNode;
  getUrgenciaBadge: (item: LicitacaoItem) => ReactNode;
  searchId?: string;
  setorId?: string;
  accessToken?: string | null;
  idPrefix: string;
  /** STORY-259: Per-bid analysis data (null = not yet available) */
  bidAnalysis?: BidAnalysisItem | null;
  /** STORY-259: Global analysis batch status */
  bidAnalysisStatus?: "ready" | "processing" | null;
}

function BidCard({
  item,
  index,
  highlightTerms,
  searchTerms,
  formatCurrency,
  formatDate,
  getRelevanceBadge,
  getRelevanceSourceBadge,
  getConfidenceBadge,
  getSourceBadge,
  getUrgenciaBadge,
  searchId,
  setorId,
  accessToken,
  idPrefix,
  bidAnalysis,
  bidAnalysisStatus,
}: BidCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [deepModalOpen, setDeepModalOpen] = useState(false);
  // STORY-447: Per-bid PDF export state
  const [isPdfLoading, setIsPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  /** STORY-259: true while analysis batch is still running and no data for this bid yet */
  const isAnalysisLoading = bidAnalysisStatus === "processing" && !bidAnalysis;

  /** STORY-447: Download a 1-page executive PDF for this bid */
  async function handlePdfExport() {
    if (!accessToken) return;
    setIsPdfLoading(true);
    setPdfError(null);
    try {
      const res = await fetch("/api/export/pdf", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          objeto: item.objeto,
          orgao: item.orgao,
          uf: item.uf,
          municipio: item.municipio ?? null,
          valor: item.valor ?? null,
          data_encerramento: item.data_encerramento ?? null,
          modalidade: item.modalidade ?? null,
          link: item.link ?? null,
          numero_compra: item.numero_compra ?? null,
          pncp_id: item.pncp_id ?? null,
          viability_level: item.viability_level ?? null,
          viability_score: item.viability_score ?? null,
          viability_factors: item.viability_factors ?? null,
        }),
      });
      if (!res.ok) {
        setPdfError("Erro ao gerar PDF. Tente novamente.");
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const safeTitle = (item.objeto ?? "edital").slice(0, 40).replace(/[^\w\s-]/g, "").trim();
      const today = new Date().toISOString().slice(0, 10);
      a.href = url;
      a.download = `SmartLic_${safeTitle}_${today}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setPdfError("Erro ao gerar PDF. Tente novamente.");
    } finally {
      setIsPdfLoading(false);
    }
  }

  return (
    <>
      <div
        className="p-4 bg-surface-0 border border-strong rounded-card hover:border-brand-blue transition-colors"
        data-testid="bid-card"
        data-tour="result-card"
      >
        {/* AC7: Essential info always visible — title, value, UF, prazo, viability */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h4 className="text-base font-medium text-ink line-clamp-2 mb-1">
              {highlightTerms(item.objeto, item.matched_terms || searchTerms)}
            </h4>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span data-tour="viability-badge"><ViabilityBadge level={item.viability_level} score={item.viability_score} factors={item.viability_factors} valueSource={item._value_source} /></span>
              {getUrgenciaBadge(item)}
              <span className="inline-flex items-center px-2 py-0.5 rounded bg-brand-blue-subtle text-brand-navy text-xs font-medium">
                {item.uf}
                {item.municipio && ` - ${item.municipio}`}
              </span>
              {getConfidenceBadge(item.confidence)}

              {/* STORY-259: Bid intelligence badges — always-visible row */}
              {isAnalysisLoading && (
                <span
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                  data-testid="analysis-loading-badge"
                  aria-label="Analisando compatibilidade"
                >
                  <svg
                    className="w-3 h-3 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                    aria-hidden="true"
                  >
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Analisando...
                </span>
              )}
              {bidAnalysis && (
                <>
                  <CompatibilityBadge compatibilidade_pct={bidAnalysis.compatibilidade_pct} />
                  <ActionLabel acao_recomendada={bidAnalysis.acao_recomendada} />
                </>
              )}
            </div>
          </div>

          <div className="flex flex-col items-end gap-2 shrink-0">
            <span className="text-lg font-bold font-data text-brand-navy">
              {formatCurrency(item.valor)}
            </span>
            <span data-tour="pipeline-button">
              <AddToPipelineButton licitacao={item} />
            </span>
            {item.link && (
              <a
                href={item.link}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Ver edital completo (abre em nova janela)"
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-brand-navy text-white text-sm font-medium rounded-button hover:bg-brand-blue-hover transition-colors"
                data-testid="link-edital"
              >
                Ver edital
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            )}
            {/* STORY-447: Per-bid PDF export button */}
            {accessToken && (
              <button
                type="button"
                onClick={handlePdfExport}
                disabled={isPdfLoading}
                aria-label="Exportar edital como PDF"
                title="Exportar PDF executivo"
                data-testid="pdf-export-btn"
                className="inline-flex items-center gap-1 px-2.5 py-1.5 border border-border text-ink-secondary text-xs font-medium rounded-button hover:bg-surface-1 hover:text-ink transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isPdfLoading ? (
                  <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
                PDF
              </button>
            )}
            {pdfError && (
              <p className="text-xs text-red-600 dark:text-red-400" data-testid="pdf-error">{pdfError}</p>
            )}
            {/* SEO-PLAYBOOK P6: Share analysis button */}
            {item.viability_score != null && (
              <ShareAnalysisButton item={item} accessToken={accessToken} />
            )}
          </div>
        </div>

        {/* AC8: Expandable details section */}
        <div className="mt-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-ink-muted hover:text-ink-secondary transition-colors flex items-center gap-1"
            aria-expanded={expanded}
            data-testid="expand-details-btn"
          >
            <svg
              className={`w-3.5 h-3.5 transition-transform ${expanded ? 'rotate-90' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {expanded ? 'Ocultar detalhes' : 'Ver detalhes'}
          </button>

          {expanded && (
            <div className="mt-3 pt-3 border-t border-border space-y-2 animate-fade-in" data-testid="bid-details">
              <p className="text-sm text-ink-secondary">
                <span className="font-medium text-ink">Órgão:</span> {item.orgao}
              </p>
              {/* UX-418 AC2: CNPJ do órgão */}
              {item.cnpj_orgao && (
                <p className="text-sm text-ink-secondary">
                  <span className="font-medium text-ink">CNPJ:</span> {item.cnpj_orgao}
                </p>
              )}
              {/* UX-418 AC1: Número do processo */}
              {item.numero_compra && (
                <p className="text-sm text-ink-secondary">
                  <span className="font-medium text-ink">Processo:</span> {item.numero_compra}
                </p>
              )}
              {item.modalidade && (
                <p className="text-sm text-ink-secondary">
                  <span className="font-medium text-ink">Modalidade:</span> {item.modalidade}
                </p>
              )}
              {/* UX-418 AC4: Data de publicação */}
              {item.data_publicacao && (
                <p className="text-sm text-ink-secondary">
                  <span className="font-medium text-ink">Publicação:</span> {formatDate(item.data_publicacao)}
                </p>
              )}
              {item.data_abertura && (
                <p className="text-sm text-ink-secondary">
                  <span className="font-medium text-ink">Abertura de propostas:</span> {formatDate(item.data_abertura)}
                </p>
              )}
              {/* UX-418 AC3: Prazo de encerramento */}
              {item.data_encerramento && (
                <p className="text-sm text-ink-secondary">
                  <span className="font-medium text-ink">Encerramento:</span> {formatDate(item.data_encerramento)}
                  {item.dias_restantes != null && item.dias_restantes >= 0 && (
                    <span className="text-ink-muted ml-1">({item.dias_restantes}d restantes)</span>
                  )}
                </p>
              )}
              {/* UX-418 AC5: Valor estimado */}
              <p className="text-sm text-ink-secondary">
                <span className="font-medium text-ink">Valor estimado:</span> {formatCurrency(item.valor)}
              </p>
              {/* UX-418 AC7: Fonte do dado */}
              {item._source && (
                <p className="text-sm text-ink-muted text-xs">
                  Fonte: {item._source === 'pncp' ? 'PNCP' : item._source === 'pcp' ? 'Portal de Compras Públicas' : item._source === 'compras_gov' ? 'ComprasGov' : item._source}
                </p>
              )}
              <div className="flex flex-wrap gap-2 mt-1">
                {getRelevanceBadge(item.relevance_score)}
                {getRelevanceSourceBadge(item.relevance_source)}
                {getSourceBadge(item._source ?? undefined)}
              </div>

              {/* STORY-259: "Por que foi recomendado" section with justificativas */}
              {bidAnalysis && bidAnalysis.justificativas.length > 0 && (
                <div
                  className="mt-2 p-3 bg-surface-1 rounded-input space-y-1.5"
                  data-testid="bid-justificativas"
                >
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-muted mb-1">
                    Por que foi recomendado
                  </p>
                  <ul className="space-y-1">
                    {bidAnalysis.justificativas.map((j, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-1.5 text-xs text-ink-secondary"
                      >
                        <span className="mt-1 w-1.5 h-1.5 rounded-full bg-brand-navy flex-shrink-0" aria-hidden="true" />
                        {j}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* STORY-259: "Analisar em detalhe" button */}
              {(bidAnalysis || bidAnalysisStatus === "ready") && (
                <div className="pt-1">
                  <button
                    onClick={() => setDeepModalOpen(true)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-brand-navy dark:text-brand-blue border border-brand-navy/30 dark:border-brand-blue/30 rounded-button hover:bg-brand-blue-subtle transition-colors"
                    data-testid="deep-analysis-btn"
                    aria-label="Abrir análise detalhada do edital"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    Analisar em detalhe
                  </button>
                </div>
              )}

              {searchId && (
                <div className="pt-2">
                  <FeedbackButtons
                    searchId={searchId}
                    bidId={item.pncp_id || `${idPrefix}-${index}`}
                    setorId={setorId}
                    bidObjeto={item.objeto}
                    bidValor={item.valor ?? undefined}
                    bidUf={item.uf}
                    confidenceScore={typeof item.confidence === "string" ? (item.confidence === "high" ? 90 : item.confidence === "medium" ? 60 : 30) : undefined}
                    relevanceSource={item.relevance_source || undefined}
                    accessToken={accessToken}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* STORY-259: Deep analysis modal — rendered outside card to avoid clipping */}
      <DeepAnalysisModal
        isOpen={deepModalOpen}
        onClose={() => setDeepModalOpen(false)}
        bidId={item.pncp_id || `${idPrefix}-${index}`}
        searchId={searchId}
        bidData={{
          objeto: item.objeto,
          orgao: item.orgao,
          valor: item.valor ?? undefined,
          modalidade: item.modalidade ?? undefined,
          uf: item.uf,
        }}
        accessToken={accessToken}
      />
    </>
  );
}
