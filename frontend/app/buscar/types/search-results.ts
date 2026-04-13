/**
 * TD-005 AC10-AC14: Grouped prop interfaces for SearchResults component.
 *
 * The 55+ flat props are organized into 7 semantic groups to improve
 * readability, reduce cognitive load, and enable incremental refactoring.
 */

import type { BuscaResult } from "../../types";
import type {
  SearchProgressEvent,
  RefreshAvailableInfo,
  SourceStatus,
  PartialProgress,
  FilterSummary,
  UfStatus,
} from "../../../hooks/useSearchSSE";
import type { SearchError } from "../hooks/useSearch";
import type { OrdenacaoOption } from "../../components/OrdenacaoSelect";
import type { StatusLicitacao } from "../components/StatusFilter";

// ---------------------------------------------------------------------------
// Group 1: SearchResultsData — results, counts, metadata
// ---------------------------------------------------------------------------
export interface SearchResultsData {
  result: BuscaResult | null;
  rawCount: number;
  filterSummary?: FilterSummary | null;
  pendingReviewCount?: number;
  pendingReviewUpdate?: {
    reclassifiedCount: number;
    acceptedCount: number;
    rejectedCount: number;
  } | null;
  /** CRIT-059 AC5: Zero-match background classification progress */
  zeroMatchProgress?: {
    candidates: number;
    willClassify: number;
    classified: number;
    approved: number;
    status: 'started' | 'classifying' | 'ready' | 'error';
  } | null;
}

// ---------------------------------------------------------------------------
// Group 2: SearchLoadingState — all loading / progress related
// ---------------------------------------------------------------------------
export interface SearchLoadingState {
  loading: boolean;
  loadingStep: number;
  estimatedTime: number;
  stateCount: number;
  statesProcessed: number;
  sseEvent: SearchProgressEvent | null;
  useRealProgress: boolean;
  sseAvailable: boolean;
  sseDisconnected?: boolean;
  isReconnecting?: boolean;
  isDegraded?: boolean;
  degradedDetail?: SearchProgressEvent["detail"] | null;
  skeletonTimeoutReached?: boolean;
  // UF progress
  ufStatuses?: Map<string, UfStatus>;
  /** UX-436: Snapshot of ufStatuses captured at timeout moment (before SSE clears). */
  ufStatusesSnapshot?: Map<string, UfStatus>;
  ufTotalFound?: number;
  ufAllComplete?: boolean;
  // Progressive results
  sourceStatuses?: Map<string, SourceStatus>;
  partialProgress?: PartialProgress | null;
}

// ---------------------------------------------------------------------------
// Group 3: SearchResultsFilters — current filter context
// ---------------------------------------------------------------------------
export interface SearchResultsFilters {
  ufsSelecionadas: Set<string>;
  sectorName: string;
  searchMode: "setor" | "termos";
  termosArray: string[];
  ordenacao: OrdenacaoOption;
  status?: StatusLicitacao;
}

// ---------------------------------------------------------------------------
// Group 4: SearchResultsActions — all callbacks
// ---------------------------------------------------------------------------
export interface SearchResultsActions {
  onCancel: () => void;
  onStageChange: (stage: number) => void;
  onOrdenacaoChange: (ord: OrdenacaoOption) => void;
  onDownload: () => void;
  onSearch: () => void;
  onRegenerateExcel?: () => void;
  onShowUpgradeModal: (plan?: string, source?: string) => void;
  onTrackEvent: (name: string, data: Record<string, any>) => void;
  onViewPartial?: () => void;
  onDismissPartial?: () => void;
  onRetryForceFresh?: () => void;
  onLoadLastSearch?: () => void;
  onRefreshResults?: () => void;
  onRetryNow?: () => void;
  onCancelRetry?: () => void;
  onAdjustPeriod?: () => void;
  onAddNeighborStates?: () => void;
  onViewNearbyResults?: () => void;
  onGeneratePdf?: (options: { clientName: string; maxItems: number }) => void;
  onStartResultsTour?: () => void;
  /** UX-436: Retry search with a reduced set of UFs */
  onRetryWithUfs?: (ufs: string[]) => void;
}

// ---------------------------------------------------------------------------
// Group 5: SearchDisplayState — display / error state
// ---------------------------------------------------------------------------
export interface SearchDisplayState {
  error: SearchError | null;
  quotaError: string | null;
  downloadLoading: boolean;
  downloadError: string | null;
  excelFailCount?: number;
  searchElapsedSeconds?: number;
  partialDismissed?: boolean;
  liveFetchInProgress?: boolean;
  refreshAvailable?: RefreshAvailableInfo | null;
  hasLastSearch?: boolean;
  retryCountdown?: number | null;
  retryMessage?: string | null;
  retryExhausted?: boolean;
  nearbyResultsCount?: number;
  pdfLoading?: boolean;
}

// ---------------------------------------------------------------------------
// Group 6: SearchAuthState — plan, session, trial
// ---------------------------------------------------------------------------
export interface SearchAuthState {
  planInfo: {
    plan_id: string;
    plan_name: string;
    quota_used: number;
    quota_reset_date: string;
    trial_expires_at?: string | null;
    subscription_status?: string;
    capabilities: {
      max_history_days: number;
      max_requests_per_month: number;
      allow_excel: boolean;
    };
  } | null;
  session: { access_token: string } | null;
  isTrialExpired?: boolean;
  trialPhase?: "full_access" | "limited_access" | "not_trial";
  paywallApplied?: boolean;
  totalBeforePaywall?: number | null;
  isProfileComplete?: boolean;
}

// ---------------------------------------------------------------------------
// Group 7: SearchFeedbackState — feedback / search IDs
// ---------------------------------------------------------------------------
export interface SearchFeedbackState {
  searchId?: string;
  setorId?: string;
  isResultsTourCompleted?: () => boolean;
}

// ---------------------------------------------------------------------------
// Combined grouped interface — all groups as named properties
// ---------------------------------------------------------------------------
export interface SearchResultsGroupedProps {
  data: SearchResultsData;
  loadingState: SearchLoadingState;
  filters: SearchResultsFilters;
  actions: SearchResultsActions;
  display: SearchDisplayState;
  auth: SearchAuthState;
  feedback: SearchFeedbackState;
}

// ---------------------------------------------------------------------------
// Backward-compatible flat interface — identical to the original 55-prop
// interface so both call-sites work during migration.
// ---------------------------------------------------------------------------
export type SearchResultsProps = SearchResultsData &
  SearchLoadingState &
  SearchResultsFilters &
  SearchResultsActions &
  SearchDisplayState &
  SearchAuthState &
  SearchFeedbackState;
