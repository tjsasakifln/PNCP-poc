/**
 * STORY-298 AC1: Unified search phase type system.
 *
 * Discriminated union mapping every possible search scenario to a single phase.
 * The `deriveSearchPhase()` function is the single source of truth — it guarantees
 * that exactly ONE phase is active at any time (AC2: zero limbo states).
 */

import type { SearchError } from "../hooks/useSearch";
import type { SourceStatus, PartialProgress } from "../../../hooks/useSearchSSE";
import type { BuscaResult } from "../../types";

/** The 9 user-visible search phases (AC1 table) */
export type SearchPhase =
  | "idle"                 // No search active
  | "searching"            // Search in progress (progress bar + source status)
  | "partial_available"    // Loading but partial results ready to view
  | "completed"            // Results available
  | "empty_results"        // Search finished but zero results
  | "all_sources_failed"   // All sources failed, no data
  | "source_timeout"       // Some sources timed out, partial data shown
  | "offline"              // Backend unreachable, auto-retry active
  | "failed"               // Non-transient error (manual retry needed)
  | "quota_exceeded";      // Plan/quota limit reached

export interface SearchPhaseInput {
  loading: boolean;
  error: SearchError | null;
  quotaError: string | null;
  result: BuscaResult | null;
  retryCountdown: number | null;
  retryExhausted: boolean;
  sourceStatuses: Map<string, SourceStatus>;
  partialProgress: PartialProgress | null;
  ufTotalFound: number;
  searchElapsedSeconds: number;
}

/**
 * Single decision tree that maps hook state → SearchPhase.
 * Evaluation order matters: most specific checks first, catch-all last.
 * Guarantees exactly one phase is returned (AC2: zero limbo states).
 */
export function deriveSearchPhase(input: SearchPhaseInput): SearchPhase {
  const {
    loading,
    error,
    quotaError,
    result,
    retryCountdown,
    retryExhausted,
    partialProgress,
    ufTotalFound,
    searchElapsedSeconds,
  } = input;

  // 1. Quota exceeded — highest priority, blocks everything
  if (quotaError) return "quota_exceeded";

  // 2. Error states (not loading)
  if (error && !loading) {
    // Auto-retry active = backend offline/transient
    if (retryCountdown != null && retryCountdown > 0) return "offline";
    // Retry exhausted but still transient = offline
    if (retryExhausted) return "offline";
    // Non-transient or no retry = failed
    return "failed";
  }

  // 3. Loading states
  if (loading) {
    // Partial results available during loading (after 15s with UF data)
    if (searchElapsedSeconds >= 15 && ufTotalFound > 0) return "partial_available";
    // Progressive delivery has some results
    if (partialProgress && partialProgress.totalSoFar > 0) return "partial_available";
    return "searching";
  }

  // 4. Result states (not loading, no error)
  if (result) {
    // All sources failed — empty_failure or zero results + partial + no cache
    if (result.response_state === "empty_failure") return "all_sources_failed";
    if (
      result.response_state !== "degraded_expired" &&
      result.is_partial &&
      (result.total_raw || 0) === 0 &&
      result.resumo.total_oportunidades === 0 &&
      !result.cached
    ) {
      return "all_sources_failed";
    }

    // Zero results (legitimate — not source failure)
    if (result.resumo.total_oportunidades === 0) return "empty_results";

    // Source timeout — has results but some sources failed
    if (result.is_partial || (result.failed_ufs && result.failed_ufs.length > 0)) {
      return "source_timeout";
    }

    return "completed";
  }

  return "idle";
}

/** Human-readable labels for each phase (used in tests + telemetry) */
export const PHASE_LABELS: Record<SearchPhase, string> = {
  idle: "Aguardando busca",
  searching: "Buscando licitações",
  partial_available: "Resultados parciais disponíveis",
  completed: "Busca concluída",
  empty_results: "Nenhum resultado encontrado",
  all_sources_failed: "Fontes indisponíveis",
  source_timeout: "Busca parcial concluída",
  offline: "Serviço temporariamente indisponível",
  failed: "Erro na busca",
  quota_exceeded: "Limite de buscas atingido",
};

/** Action labels for each phase (AC1 table, "Ação" column) */
export const PHASE_ACTIONS: Record<SearchPhase, string> = {
  idle: "",
  searching: "Cancelar",
  partial_available: "Ver parciais",
  completed: "Download / Pipeline",
  empty_results: "Ajustar filtros",
  all_sources_failed: "Tentar novamente",
  source_timeout: "Ver resultado parcial",
  offline: "Tentando novamente...",
  failed: "Tentar novamente",
  quota_exceeded: "Ver planos",
};
