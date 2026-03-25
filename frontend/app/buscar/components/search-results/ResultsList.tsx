"use client";

import type { BuscaResult } from "../../../types";
import { LicitacoesPreview } from "../../../components/LicitacoesPreview";
import { ResultsPagination } from "./ResultsPagination";
import { TrialPaywall } from "../../../../components/billing/TrialPaywall";

interface ResultsListProps {
  result: BuscaResult;
  paginatedLicitacoes: BuscaResult["licitacoes"];
  totalLicitacoes: number;
  currentPage: number;
  pageSize: 10 | 20 | 50;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: 10 | 20 | 50) => void;
  // Display
  searchMode: "setor" | "termos";
  termosArray: string[];
  // Auth/plan
  planInfo: {
    capabilities: { allow_excel: boolean };
  } | null;
  session: { access_token: string } | null;
  onShowUpgradeModal: (plan?: string, source?: string) => void;
  // Feedback
  searchId?: string;
  setorId?: string;
  // Paywall
  paywallApplied?: boolean;
  totalBeforePaywall?: number | null;
}

/**
 * TD-007 AC2: ResultsList — list/grid of ResultCards with pagination and empty state.
 * Wraps LicitacoesPreview with top/bottom pagination and paywall overlay.
 */
export function ResultsList({
  result,
  paginatedLicitacoes,
  totalLicitacoes,
  currentPage,
  pageSize,
  onPageChange,
  onPageSizeChange,
  searchMode,
  termosArray,
  planInfo,
  session,
  onShowUpgradeModal,
  searchId,
  setorId,
  paywallApplied,
  totalBeforePaywall,
}: ResultsListProps) {
  return (
    <>
      {/* UX-352 AC6: Clear visual separator between summary and opportunities list */}
      {result.licitacoes && result.licitacoes.length > 0 && (
        <div className="border-t border-strong" />
      )}

      {/* STORY-333 AC3: Top Pagination */}
      <ResultsPagination
        totalItems={totalLicitacoes}
        currentPage={currentPage}
        pageSize={pageSize}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />

      {/* STORY-333 AC2: Licitacoes Preview — paginated client-side */}
      {paginatedLicitacoes.length > 0 && (
        <LicitacoesPreview
          licitacoes={paginatedLicitacoes}
          previewCount={pageSize}
          excelAvailable={planInfo?.capabilities.allow_excel ?? false}
          searchTerms={searchMode === "termos" ? termosArray : (result.termos_utilizados || [])}
          onUpgradeClick={() => {
            onShowUpgradeModal("smartlic_pro", "licitacoes_preview");
          }}
          searchId={searchId}
          setorId={setorId}
          accessToken={session?.access_token}
          bidAnalysis={result.bid_analysis}
          bidAnalysisStatus={result.bid_analysis_status}
        />
      )}

      {/* UX-421 AC4: Single pagination (top only) — removed duplicate bottom pagination */}

      {/* STORY-320 AC7: Blurred results preview + paywall overlay for limited_access */}
      {paywallApplied && totalBeforePaywall && totalBeforePaywall > result.licitacoes.length && (
        <div className="relative mt-4" data-testid="paywall-blurred-results">
          {/* Blurred placeholder cards */}
          <div className="space-y-3 blur-sm pointer-events-none select-none" aria-hidden="true">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 bg-surface border border-border rounded-card">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded-full font-medium">Preview</span>
                </div>
                <div className="h-4 bg-[var(--surface-1)] rounded w-3/4 mb-2" />
                <div className="h-3 bg-[var(--surface-1)] rounded w-1/2" />
              </div>
            ))}
          </div>
          {/* Paywall overlay */}
          <TrialPaywall
            additionalCount={totalBeforePaywall - result.licitacoes.length}
            context="search_results"
          />
        </div>
      )}
    </>
  );
}
