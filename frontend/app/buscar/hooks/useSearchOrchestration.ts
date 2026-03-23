"use client";

import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAnalytics } from "../../../hooks/useAnalytics";
import { useOnboarding } from "../../../hooks/useOnboarding";
import { useShepherdTour } from "../../../hooks/useShepherdTour";
import { useKeyboardShortcuts, type KeyboardShortcut } from "../../../hooks/useKeyboardShortcuts";
import { usePlan } from "../../../hooks/usePlan";
import { useTrialPhase } from "../../../hooks/useTrialPhase";
import { useAuth } from "../../components/AuthProvider";
import { useSearchFilters } from "./useSearchFilters";
import { useSearch } from "./useSearch";
import { useNavigationGuard } from "../../../hooks/useNavigationGuard";
import { useBackendStatusContext } from "../../components/BackendStatusIndicator";
import { useBroadcastChannel } from "../../../hooks/useBroadcastChannel";

import { dateDiffInDays } from "../../../lib/utils/dateDiffInDays";
import { toast } from "sonner";
import { checkHasLastSearch, getLastSearch } from "../../../lib/lastSearchCache";
import type { BuscaResult } from "../../types";
import { safeSetItem, safeGetItem, safeRemoveItem } from "../../../lib/storage";

import { SEARCH_TOUR_STEPS, RESULTS_TOUR_STEPS, type TrialValue } from "../constants/tour-steps";
import type { SearchResultsProps } from "../types/search-results";

export function useSearchOrchestration() {
  const { session, loading: authLoading } = useAuth();
  const { planInfo } = usePlan();
  const { phase: trialPhase } = useTrialPhase();
  const { trackEvent } = useAnalytics();
  // Ref for trackEvent — it is not memoized in useAnalytics, so effects that
  // should run only once access it via this ref instead of adding it to deps.
  const trackEventRef = useRef(trackEvent);
  trackEventRef.current = trackEvent;
  const router = useRouter();

  // TD-H02: Auth guard — redirect unauthenticated users to landing page,
  // matching the behavior of (protected)/layout.tsx for consistency.
  useEffect(() => {
    if (!authLoading && !session) {
      router.replace("/");
    }
  }, [authLoading, session, router]);

  // ── Trial / Plan State ──────────────────────────────────────────────
  const [showTrialConversion, setShowTrialConversion] = useState(false);
  const [trialValue, setTrialValue] = useState<TrialValue | null>(null);
  const [trialValueLoading, setTrialValueLoading] = useState(false);

  const trialDaysRemaining = useMemo(() => {
    if (!planInfo?.trial_expires_at) return null;
    const expiryDate = new Date(planInfo.trial_expires_at);
    const now = new Date();
    const diffTime = expiryDate.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
  }, [planInfo?.trial_expires_at]);

  const isTrialExpired = useMemo(() => {
    return planInfo?.plan_id === "free_trial" && planInfo?.subscription_status === "expired";
  }, [planInfo?.plan_id, planInfo?.subscription_status]);

  const isGracePeriod = useMemo(() => {
    return planInfo?.dunning_phase === "grace_period";
  }, [planInfo?.dunning_phase]);

  const graceDaysRemaining = useMemo(() => {
    if (!isGracePeriod || planInfo?.days_since_failure == null) return 0;
    return Math.max(0, 21 - planInfo.days_since_failure);
  }, [isGracePeriod, planInfo?.days_since_failure]);

  const [showPaymentRecovery, setShowPaymentRecovery] = useState(false);

  useEffect(() => {
    setShowPaymentRecovery(isGracePeriod);
  }, [isGracePeriod]);

  const fetchTrialValue = useCallback(async () => {
    if (!session?.access_token) return;
    setTrialValueLoading(true);
    try {
      const res = await fetch("/api/analytics?endpoint=trial-value", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setTrialValue(data);
      }
    } catch (err) {
      if (process.env.NODE_ENV !== "production") console.error("[GTM-010] Failed to fetch trial value:", err);
    } finally {
      setTrialValueLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (isTrialExpired) {
      setShowTrialConversion(true);
      fetchTrialValue();
    }
  }, [isTrialExpired, fetchTrialValue]);

  // ── Backend Status ──────────────────────────────────────────────────
  const backendStatus = useBackendStatusContext();
  const queuedSearchRef = useRef<(() => void) | null>(null);

  // ── Auto-Search / Onboarding ────────────────────────────────────────
  const searchParamsRaw = useSearchParams();
  const isAutoSearch = searchParamsRaw?.get('auto') === 'true';
  const autoSearchId = searchParamsRaw?.get('search_id') || null;
  const [showOnboardingBanner, setShowOnboardingBanner] = useState(isAutoSearch);
  const [autoSearchDismissed, setAutoSearchDismissed] = useState(false);

  // ── UI State ────────────────────────────────────────────────────────
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [upgradeSource, setUpgradeSource] = useState<string | undefined>();
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);

  const hasSearchedBefore = useMemo(() => {
    return safeGetItem('smartlic-has-searched') === 'true';
  }, []);

  const isProfileComplete = useMemo(() => {
    try {
      const cached = safeGetItem('profileContext');
      if (!cached) return false;
      const ctx = JSON.parse(cached);
      return !!(ctx.porte_empresa && ctx.ufs_atuacao?.length > 0);
    } catch { return false; }
  }, []);

  const [lastSearchAvailable, setLastSearchAvailable] = useState(() => checkHasLastSearch());

  const [customizeOpen, setCustomizeOpen] = useState(() => {
    if (safeGetItem('smartlic-has-searched') !== 'true') return false;
    const legacy = safeGetItem('smartlic-customize-open');
    const current = safeGetItem('smartlic:buscar:filters-expanded');
    if (current !== null) return current === 'true';
    if (legacy !== null) {
      const wasOpen = legacy === 'open';
      safeSetItem('smartlic:buscar:filters-expanded', String(wasOpen));
      safeRemoveItem('smartlic-customize-open');
      return wasOpen;
    }
    return false;
  });

  useEffect(() => {
    safeSetItem('smartlic:buscar:filters-expanded', String(customizeOpen));
  }, [customizeOpen]);

  const [showFirstUseTip, setShowFirstUseTip] = useState(() => {
    return safeGetItem('smartlic-has-searched') !== 'true'
      && safeGetItem('smartlic-first-tip-dismissed') !== 'true';
  });

  const dismissFirstUseTip = useCallback(() => {
    setShowFirstUseTip(false);
    safeSetItem('smartlic-first-tip-dismissed', 'true');
  }, []);

  // ── Tours ───────────────────────────────────────────────────────────
  const reportTourEvent = useCallback(async (tourId: string, event: string, stepsSeen: number) => {
    try {
      const token = session?.access_token;
      await fetch('/api/onboarding?endpoint=tour-event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ tour_id: tourId, event, steps_seen: stepsSeen }),
      });
    } catch { /* fire-and-forget */ }
  }, [session?.access_token]);

  const {
    isCompleted: isSearchTourCompleted,
    startTour: startSearchTour,
    restartTour: restartSearchTour,
  } = useShepherdTour({
    tourId: 'search',
    steps: SEARCH_TOUR_STEPS,
    onComplete: (stepsSeen) => {
      trackEvent('onboarding_tour_completed', { tour: 'search', steps_seen: stepsSeen });
      reportTourEvent('search', 'completed', stepsSeen);
    },
    onSkip: (stepsSeen) => {
      trackEvent('onboarding_tour_skipped', { tour: 'search', skipped_at_step: stepsSeen });
      reportTourEvent('search', 'skipped', stepsSeen);
    },
  });

  const {
    isCompleted: isResultsTourCompleted,
    startTour: startResultsTour,
    restartTour: restartResultsTour,
  } = useShepherdTour({
    tourId: 'results',
    steps: RESULTS_TOUR_STEPS,
    onComplete: (stepsSeen) => {
      trackEvent('onboarding_tour_completed', { tour: 'results', steps_seen: stepsSeen });
      reportTourEvent('results', 'completed', stepsSeen);
    },
    onSkip: (stepsSeen) => {
      trackEvent('onboarding_tour_skipped', { tour: 'results', skipped_at_step: stepsSeen });
      reportTourEvent('results', 'skipped', stepsSeen);
    },
  });

  const searchTourStartRef = useRef<() => void>(() => {});
  searchTourStartRef.current = () => {
    if (!isSearchTourCompleted()) {
      startSearchTour();
      trackEvent('onboarding_tour_started', { tour: 'search' });
    }
  };

  const { shouldShowOnboarding, restartTour } = useOnboarding({
    autoStart: true,
    onComplete: () => {
      trackEvent('onboarding_completed', { completion_time: Date.now() });
      setTimeout(() => searchTourStartRef.current(), 500);
    },
    onDismiss: () => {
      trackEvent('onboarding_dismissed', { dismissed_at: Date.now() });
      setTimeout(() => searchTourStartRef.current(), 500);
    },
    onStepChange: (stepId, stepIndex) => trackEvent('onboarding_step', { step_id: stepId, step_index: stepIndex }),
  });

  useEffect(() => {
    const welcomeDone = safeGetItem('smartlic_onboarding_completed') === 'true' ||
                         safeGetItem('smartlic_onboarding_dismissed') === 'true';
    if (welcomeDone && !isSearchTourCompleted()) {
      const timer = setTimeout(() => {
        startSearchTour();
        trackEventRef.current('onboarding_tour_started', { tour: 'search' });
      }, 500);
      return () => clearTimeout(timer);
    }
    // Mount-only: start tour once after onboarding; stable fns accessed via ref.
  }, [isSearchTourCompleted, startSearchTour]);

  // ── Search Core ─────────────────────────────────────────────────────
  const progressAreaRef = useRef<HTMLDivElement>(null);
  const clearResultRef = useRef<() => void>(() => {});
  const filters = useSearchFilters(() => clearResultRef.current());
  const search = useSearch(filters);
  clearResultRef.current = () => search.setResult(null);

  // ── Cross-Tab Sync ──────────────────────────────────────────────────
  const { broadcastSearchComplete } = useBroadcastChannel({
    onSearchComplete: useCallback((result: BuscaResult) => {
      if (!search.loading) {
        search.setResult(result);
        toast.info("Resultados atualizados de outra aba.");
      }
    }, [search.loading, search.setResult]),
  });

  const prevLoadingRef = useRef(false);
  useEffect(() => {
    if (prevLoadingRef.current && !search.loading && search.result) {
      broadcastSearchComplete(search.result, search.searchId);
    }
    prevLoadingRef.current = search.loading;
  }, [search.loading, search.result, search.searchId, broadcastSearchComplete]);

  useEffect(() => {
    if (search.quotaError === "trial_expired") {
      setShowTrialConversion(true);
      fetchTrialValue();
    }
  }, [search.quotaError, fetchTrialValue]);

  // ── Search Actions ──────────────────────────────────────────────────
  const handleLoadLastSearch = useCallback(() => {
    const cached = getLastSearch();
    if (cached?.result) {
      search.setResult(cached.result as BuscaResult);
      toast.success("Resultados da ultima analise restaurados.");
    }
  }, [search.setResult]);

  useEffect(() => {
    if (!search.loading) {
      setLastSearchAvailable(checkHasLastSearch());
    }
  }, [search.loading]);

  const originalBuscar = search.buscar;
  const buscarWithCollapse = useCallback(() => {
    if (backendStatus.status === "offline") {
      toast.info("Servidor indisponivel no momento. A analise sera iniciada quando o servidor estiver disponivel.");
      queuedSearchRef.current = () => {
        setCustomizeOpen(false);
        safeSetItem('smartlic-has-searched', 'true');
        setShowFirstUseTip(false);
        originalBuscar();
        setTimeout(() => {
          progressAreaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      };
      return;
    }
    setCustomizeOpen(false);
    safeSetItem('smartlic-has-searched', 'true');
    setShowFirstUseTip(false);
    originalBuscar();
    setTimeout(() => {
      progressAreaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }, [originalBuscar, backendStatus.status]);

  useEffect(() => {
    if ((backendStatus.status === "online" || backendStatus.status === "recovering") && queuedSearchRef.current) {
      const queuedFn = queuedSearchRef.current;
      queuedSearchRef.current = null;
      toast.success("Servidor disponivel. Executando analise...");
      queuedFn();
    }
  }, [backendStatus.status]);

  useNavigationGuard({ isLoading: search.loading });

  // ── PDF ─────────────────────────────────────────────────────────────
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);

  const handleGeneratePdf = useCallback(async (options: { clientName: string; maxItems: number }) => {
    if (!session?.access_token || !search.searchId) return;
    setPdfLoading(true);
    setPdfModalOpen(false);
    try {
      const response = await fetch("/api/reports/diagnostico", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          search_id: search.searchId,
          client_name: options.clientName || null,
          max_items: options.maxItems,
        }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({ error: "Erro ao gerar PDF" }));
        toast.error(err.error || "Erro ao gerar relatorio PDF");
        return;
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `diagnostico-${filters.sectorName.toLowerCase().replace(/\s+/g, "-")}-${new Date().toISOString().split("T")[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      trackEvent("pdf_diagnostico_generated", { max_items: options.maxItems, has_client: !!options.clientName });
    } catch (err) {
      toast.error("Erro ao gerar relatorio PDF. Tente novamente.");
    } finally {
      setPdfLoading(false);
    }
  }, [session, search.searchId, filters.sectorName, trackEvent]);

  // ── Error Boundary Reset ────────────────────────────────────────────
  const handleErrorBoundaryReset = useCallback(() => {
    search.setResult(null);
    search.setError(null);
  }, [search]);

  // ── Elapsed / Partial / Drawer ──────────────────────────────────────
  const [searchElapsed, setSearchElapsed] = useState(0);
  const [partialDismissed, setPartialDismissed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (!search.loading) {
      setSearchElapsed(0);
      setPartialDismissed(false);
      return;
    }
    const interval = setInterval(() => setSearchElapsed(prev => prev + 1), 1000);
    return () => clearInterval(interval);
  }, [search.loading]);

  useEffect(() => { search.restoreSearchStateOnMount(); }, []);

  useEffect(() => {
    if (isAutoSearch && autoSearchId && !autoSearchDismissed) {
      setShowOnboardingBanner(true);
    }
  }, [isAutoSearch, autoSearchId, autoSearchDismissed]);

  // ── Keyboard Shortcuts ──────────────────────────────────────────────
  useKeyboardShortcuts({ shortcuts: [
    { key: 'k', ctrlKey: true, action: () => { if (filters.canSearch && !search.loading) buscarWithCollapse(); }, description: 'Search' },
    { key: 'a', ctrlKey: true, action: filters.selecionarTodos, description: 'Select all' },
    { key: 'Enter', ctrlKey: true, action: () => { if (filters.canSearch && !search.loading) buscarWithCollapse(); }, description: 'Search alt' },
    { key: '/', action: () => setShowKeyboardHelp(true), description: 'Show shortcuts' },
    { key: 'Escape', action: filters.limparSelecao, description: 'Clear' },
  ] });

  const handleShowUpgradeModal = useCallback((_plan?: string, source?: string) => {
    setUpgradeSource(source);
    setShowUpgradeModal(true);
  }, []);

  // ── Computed: SearchResults props ───────────────────────────────────
  const isTrialExpiredOrQuota = isTrialExpired || search.quotaError === "trial_expired";

  const searchResultsProps = useMemo((): SearchResultsProps => ({
    // Group 1: SearchResultsData
    result: search.result,
    rawCount: search.rawCount,
    filterSummary: search.filterSummary,
    pendingReviewCount: search.result?.pending_review_count ?? 0,
    pendingReviewUpdate: search.pendingReviewUpdate,
    zeroMatchProgress: search.zeroMatchProgress,

    // Group 2: SearchLoadingState
    loading: search.loading,
    loadingStep: search.loadingStep,
    estimatedTime: search.estimateSearchTime(filters.ufsSelecionadas.size, dateDiffInDays(filters.dataInicial, filters.dataFinal)),
    stateCount: filters.ufsSelecionadas.size,
    statesProcessed: search.statesProcessed,
    sseEvent: search.sseEvent,
    useRealProgress: search.useRealProgress,
    sseAvailable: search.sseAvailable,
    sseDisconnected: search.sseDisconnected,
    isReconnecting: search.isReconnecting,
    isDegraded: search.isDegraded,
    degradedDetail: search.degradedDetail,
    skeletonTimeoutReached: search.skeletonTimeoutReached,
    ufStatuses: search.ufStatuses,
    ufTotalFound: search.ufTotalFound,
    ufAllComplete: search.ufAllComplete,
    sourceStatuses: search.sourceStatuses,
    partialProgress: search.partialProgress,

    // Group 3: SearchResultsFilters
    ufsSelecionadas: filters.ufsSelecionadas,
    sectorName: filters.sectorName,
    searchMode: filters.searchMode,
    termosArray: filters.termosArray,
    ordenacao: filters.ordenacao,

    // Group 4: SearchResultsActions
    onCancel: search.cancelSearch,
    onStageChange: (stage: number) => trackEvent('search_progress_stage', { stage, is_sse: search.useRealProgress && search.sseAvailable }),
    onOrdenacaoChange: filters.setOrdenacao,
    onDownload: search.handleDownload,
    onSearch: search.buscar,
    onRegenerateExcel: search.handleRegenerateExcel,
    onShowUpgradeModal: handleShowUpgradeModal,
    onTrackEvent: trackEvent,
    onViewPartial: search.viewPartialResults,
    onDismissPartial: () => setPartialDismissed(true),
    onRetryForceFresh: search.buscarForceFresh,
    onLoadLastSearch: handleLoadLastSearch,
    onRefreshResults: search.handleRefreshResults,
    onRetryNow: search.retryNow,
    onCancelRetry: search.cancelRetry,
    onAdjustPeriod: undefined,
    onAddNeighborStates: undefined,
    onViewNearbyResults: undefined,
    onGeneratePdf: () => setPdfModalOpen(true),
    onStartResultsTour: () => {
      startResultsTour();
      trackEvent('onboarding_tour_started', { tour: 'results' });
    },

    // Group 5: SearchDisplayState
    error: search.error,
    quotaError: search.quotaError,
    downloadLoading: search.downloadLoading,
    downloadError: search.downloadError,
    excelFailCount: search.excelFailCount,
    searchElapsedSeconds: searchElapsed,
    partialDismissed,
    liveFetchInProgress: search.liveFetchInProgress,
    refreshAvailable: search.refreshAvailable,
    hasLastSearch: lastSearchAvailable,
    retryCountdown: search.retryCountdown,
    retryMessage: search.retryMessage,
    retryExhausted: search.retryExhausted,
    nearbyResultsCount: undefined,
    pdfLoading,

    // Group 6: SearchAuthState
    planInfo,
    session,
    isTrialExpired: isTrialExpiredOrQuota,
    trialPhase,
    paywallApplied: search.result?.paywall_applied,
    totalBeforePaywall: search.result?.total_before_paywall,
    isProfileComplete,

    // Group 7: SearchFeedbackState
    searchId: search.searchId || undefined,
    setorId: filters.setorId,
    isResultsTourCompleted,
  }), [
    search.result, search.rawCount, search.filterSummary, search.pendingReviewUpdate,
    search.zeroMatchProgress, search.loading, search.loadingStep, search.statesProcessed,
    search.sseEvent, search.useRealProgress, search.sseAvailable, search.sseDisconnected,
    search.isReconnecting, search.isDegraded, search.degradedDetail, search.skeletonTimeoutReached,
    search.ufStatuses, search.ufTotalFound, search.ufAllComplete, search.sourceStatuses,
    search.partialProgress, search.cancelSearch, search.buscar, search.handleDownload,
    search.handleRegenerateExcel, search.viewPartialResults, search.buscarForceFresh,
    search.handleRefreshResults, search.retryNow, search.cancelRetry,
    search.error, search.quotaError, search.downloadLoading, search.downloadError,
    search.excelFailCount, search.liveFetchInProgress, search.refreshAvailable,
    search.retryCountdown, search.retryMessage, search.retryExhausted, search.searchId,
    search.estimateSearchTime,
    filters.ufsSelecionadas, filters.sectorName, filters.searchMode, filters.termosArray,
    filters.ordenacao, filters.setOrdenacao, filters.dataInicial, filters.dataFinal,
    filters.setorId,
    trackEvent, handleShowUpgradeModal, handleLoadLastSearch, startResultsTour,
    isResultsTourCompleted, searchElapsed, partialDismissed, lastSearchAvailable,
    pdfLoading, planInfo, session, isTrialExpiredOrQuota, trialPhase, isProfileComplete,
  ]);

  return {
    // Auth
    authLoading,
    session,

    // Plan/Trial
    planInfo,
    trialPhase,
    trialDaysRemaining,
    isTrialExpired,
    isGracePeriod,
    graceDaysRemaining,
    showTrialConversion,
    setShowTrialConversion,
    trialValue,
    trialValueLoading,
    fetchTrialValue,
    showPaymentRecovery,
    setShowPaymentRecovery,

    // Core search
    filters,
    search,
    buscarWithCollapse,

    // UI state
    showUpgradeModal,
    setShowUpgradeModal,
    upgradeSource,
    handleShowUpgradeModal,
    showKeyboardHelp,
    setShowKeyboardHelp,
    customizeOpen,
    setCustomizeOpen,
    showFirstUseTip,
    dismissFirstUseTip,
    drawerOpen,
    setDrawerOpen,
    lastSearchAvailable,
    hasSearchedBefore,
    isProfileComplete,

    // Onboarding
    showOnboardingBanner,
    setShowOnboardingBanner,
    autoSearchDismissed,
    setAutoSearchDismissed,
    shouldShowOnboarding,
    restartTour,
    restartSearchTour,
    restartResultsTour,

    // Progress
    progressAreaRef,
    searchElapsed,
    partialDismissed,
    setPartialDismissed,

    // PDF
    pdfLoading,
    pdfModalOpen,
    setPdfModalOpen,
    handleGeneratePdf,

    // Error
    handleErrorBoundaryReset,
    handleLoadLastSearch,

    // Backend
    backendStatus,

    // Analytics
    trackEvent,

    // Router
    router,

    // Computed
    searchResultsProps,
  };
}
