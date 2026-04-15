"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAnalytics } from "../../../hooks/useAnalytics";
import { useOnboarding } from "../../../hooks/useOnboarding";
import type { ReactNode } from "react";
import { useKeyboardShortcuts } from "../../../hooks/useKeyboardShortcuts";
import { useAuth } from "../../components/AuthProvider";
import { useSearchFilters } from "./useSearchFilters";
import { useSearch } from "./useSearch";
import { useSearchBillingState } from "./useSearchBillingState";
import { useSearchComputedProps } from "./useSearchComputedProps";
import { useSearchState } from "./useSearchState";
import { useSearchSSE } from "./useSearchSSE";
import { useNavigationGuard } from "../../../hooks/useNavigationGuard";
import { useBroadcastChannel } from "../../../hooks/useBroadcastChannel";

import { toast } from "sonner";
import { getLastSearch, saveLastSearch, checkHasLastSearch } from "../../../lib/lastSearchCache";
import { safeSetItem, safeGetItem } from "../../../lib/storage";
import { getDaysInTrial } from "../../../lib/analytics-helpers";
import type { BuscaResult } from "../../types";

import { SEARCH_TOUR_STEPS, RESULTS_TOUR_STEPS } from "../constants/tour-steps";

export function useSearchOrchestration() {
  const { session, loading: authLoading } = useAuth();
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

  // ── Trial / Plan / Billing State ────────────────────────────────────
  const billing = useSearchBillingState();

  // ── UI State ─────────────────────────────────────────────────────────
  // DEBT-FE-001: Extracted to useSearchState sub-hook.
  const uiState = useSearchState();

  // ── Auto-Search / Onboarding ────────────────────────────────────────
  const searchParamsRaw = useSearchParams();
  const isAutoSearch = searchParamsRaw?.get('auto') === 'true';
  const autoSearchId = searchParamsRaw?.get('search_id') || null;
  const [showOnboardingBanner, setShowOnboardingBanner] = useState(isAutoSearch);
  const [autoSearchDismissed, setAutoSearchDismissed] = useState(false);
  const [shouldSearchAfterRestore, setShouldSearchAfterRestore] = useState(false);

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

  const SEARCH_TOUR_KEY = 'onboarding_search_tour_completed';
  const RESULTS_TOUR_KEY = 'onboarding_results_tour_completed';

  const [searchTourActive, setSearchTourActive] = useState(false);
  const [resultsTourActive, setResultsTourActive] = useState(false);

  const isSearchTourCompleted = useCallback(() => safeGetItem(SEARCH_TOUR_KEY) === 'true', []);
  const isResultsTourCompleted = useCallback(() => safeGetItem(RESULTS_TOUR_KEY) === 'true', []);

  const startSearchTour = useCallback(() => setSearchTourActive(true), []);
  const startResultsTour = useCallback(() => setResultsTourActive(true), []);
  const restartSearchTour = useCallback(() => { safeSetItem(SEARCH_TOUR_KEY, 'false'); setSearchTourActive(true); }, []);
  const restartResultsTour = useCallback(() => { safeSetItem(RESULTS_TOUR_KEY, 'false'); setResultsTourActive(true); }, []);

  // Handlers passed to <Tour /> in buscar/page.tsx
  const handleSearchTourComplete = useCallback((stepsSeen: number) => {
    safeSetItem(SEARCH_TOUR_KEY, 'true');
    setSearchTourActive(false);
    trackEventRef.current('onboarding_tour_completed', { tour: 'search', steps_seen: stepsSeen });
    void reportTourEvent('search', 'completed', stepsSeen);
  }, [reportTourEvent]);

  const handleSearchTourSkip = useCallback((skippedAtStep: number) => {
    safeSetItem(SEARCH_TOUR_KEY, 'true');
    setSearchTourActive(false);
    trackEventRef.current('onboarding_tour_skipped', { tour: 'search', skipped_at_step: skippedAtStep });
    void reportTourEvent('search', 'skipped', skippedAtStep);
  }, [reportTourEvent]);

  const handleResultsTourComplete = useCallback((stepsSeen: number) => {
    safeSetItem(RESULTS_TOUR_KEY, 'true');
    setResultsTourActive(false);
    trackEventRef.current('onboarding_tour_completed', { tour: 'results', steps_seen: stepsSeen });
    void reportTourEvent('results', 'completed', stepsSeen);
  }, [reportTourEvent]);

  const handleResultsTourSkip = useCallback((skippedAtStep: number) => {
    safeSetItem(RESULTS_TOUR_KEY, 'true');
    setResultsTourActive(false);
    trackEventRef.current('onboarding_tour_skipped', { tour: 'results', skipped_at_step: skippedAtStep });
    void reportTourEvent('results', 'skipped', skippedAtStep);
  }, [reportTourEvent]);

  const searchTourStartRef = useRef<() => void>(() => {});
  searchTourStartRef.current = () => {
    if (!isSearchTourCompleted()) {
      startSearchTour();
      trackEvent('onboarding_tour_started', { tour: 'search' });
    }
  };

  const { shouldShowOnboarding, restartTour, tourElement: onboardingTourElement } = useOnboarding({
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
  // Typed as ReactNode — the consumer (buscar/page.tsx) must render this
  const onboardingElement: ReactNode = onboardingTourElement;

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
  const clearResultRef = useRef<() => void>(() => {});
  const filters = useSearchFilters(() => clearResultRef.current());
  const search = useSearch(filters);
  clearResultRef.current = () => search.setResult(null);

  // ── SSE / Backend Status / Progress ─────────────────────────────────
  // DEBT-FE-001: Extracted to useSearchSSE sub-hook.
  const onSearchStart = useCallback(() => {
    uiState.setCustomizeOpen(false);
    uiState.setShowFirstUseTip(false);
  }, [uiState.setCustomizeOpen, uiState.setShowFirstUseTip]);

  const sse = useSearchSSE({
    originalBuscar: search.buscar,
    searchLoading: search.loading,
    onSearchStart,
    setUfsSelecionadas: filters.setUfsSelecionadas,
  });

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
      billing.setShowTrialConversion(true);
      billing.fetchTrialValue();
    }
  }, [search.quotaError, billing.fetchTrialValue, billing.setShowTrialConversion]);

  // ── ISSUE-060: Save last search with form state so restore is consistent ──
  const prevResultRef = useRef<BuscaResult | null>(null);
  useEffect(() => {
    if (search.result && search.result !== prevResultRef.current) {
      prevResultRef.current = search.result;
      saveLastSearch(search.result, {
        ufs: Array.from(filters.ufsSelecionadas),
        startDate: filters.dataInicial ?? "",
        endDate: filters.dataFinal ?? "",
        setor: filters.searchMode === "setor" ? filters.setorId : undefined,
        includeKeywords: filters.searchMode === "termos" ? filters.termosArray : undefined,
      });
    }
  }, [search.result, filters.ufsSelecionadas, filters.dataInicial, filters.dataFinal, filters.searchMode, filters.setorId, filters.termosArray]);

  // ── STORY-370: Funnel analytics — first search + first relevant result ──
  useEffect(() => {
    if (!search.result) return;

    const setor = filters.searchMode === "setor" ? filters.setorId : undefined;
    const ufs = Array.from(filters.ufsSelecionadas);
    const resultCount = search.result.licitacoes?.length ?? 0;
    const daysInTrial = getDaysInTrial(session?.user?.created_at);

    // first_search_executed: fire once per browser
    if (!localStorage.getItem('first_search_tracked')) {
      localStorage.setItem('first_search_tracked', 'true');
      trackEventRef.current('first_search_executed', {
        setor,
        ufs,
        resultado_count: resultCount,
        days_in_trial: daysInTrial,
      });
    }

    // first_relevant_result_found: fire once when there is at least 1 result
    if (resultCount > 0 && !localStorage.getItem('first_relevant_result_tracked')) {
      localStorage.setItem('first_relevant_result_tracked', 'true');
      trackEventRef.current('first_relevant_result_found', {
        setor,
        ufs,
        resultado_count: resultCount,
        days_in_trial: daysInTrial,
      });
    }
  }, [search.result]);
  // ────────────────────────────────────────────────────────────────────

  // ── Search Actions ──────────────────────────────────────────────────
  const handleLoadLastSearch = useCallback(() => {
    const cached = getLastSearch();
    if (cached?.result) {
      search.setResult(cached.result as BuscaResult);
      // ISSUE-060: restore form state that matches this result
      if (cached.formState) {
        const fs = cached.formState;
        if (fs.ufs?.length) filters.setUfsSelecionadas(new Set(fs.ufs));
        if (fs.startDate) filters.setDataInicial(fs.startDate);
        if (fs.endDate) filters.setDataFinal(fs.endDate);
        if (fs.setor) { filters.setSearchMode("setor"); filters.setSetorId(fs.setor); }
        else if (fs.includeKeywords?.length) { filters.setSearchMode("termos"); filters.setTermosArray(fs.includeKeywords); }
      }
      // ISSUE-061: trigger search automatically after state flush (1 click = sync + search)
      setShouldSearchAfterRestore(true);
    }
  }, [search.setResult, filters]);

  useEffect(() => {
    if (shouldSearchAfterRestore) {
      setShouldSearchAfterRestore(false);
      search.buscar();
    }
  }, [shouldSearchAfterRestore, search.buscar]);

  useEffect(() => {
    if (!search.loading) {
      uiState.setLastSearchAvailable(checkHasLastSearch());
    }
  }, [search.loading, uiState.setLastSearchAvailable]);

  useNavigationGuard({ isLoading: search.loading });

  // ── PDF ─────────────────────────────────────────────────────────────
  // searchId é zerado após o search completar. Preservamos o último valor
  // não-nulo para que handleGeneratePdf funcione após a busca terminar.
  const lastSearchIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (search.searchId) {
      lastSearchIdRef.current = search.searchId;
    }
  }, [search.searchId]);

  const handleGeneratePdf = useCallback(async (options: { clientName: string; maxItems: number }) => {
    const effectiveSearchId = search.searchId ?? lastSearchIdRef.current;
    if (!session?.access_token || !effectiveSearchId) return;
    uiState.setPdfLoading(true);
    uiState.setPdfModalOpen(false);
    try {
      const response = await fetch("/api/reports/diagnostico", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          search_id: effectiveSearchId,
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
    } catch {
      toast.error("Erro ao gerar relatorio PDF. Tente novamente.");
    } finally {
      uiState.setPdfLoading(false);
    }
  }, [session, search.searchId, filters.sectorName, trackEvent, uiState.setPdfLoading, uiState.setPdfModalOpen]);

  // ── Error Boundary Reset ────────────────────────────────────────────
  const handleErrorBoundaryReset = useCallback(() => {
    search.setResult(null);
    search.setError(null);
  }, [search]);

  useEffect(() => { search.restoreSearchStateOnMount(); }, []);

  useEffect(() => {
    if (isAutoSearch && autoSearchId && !autoSearchDismissed) {
      setShowOnboardingBanner(true);
    }
  }, [isAutoSearch, autoSearchId, autoSearchDismissed]);

  // ── Keyboard Shortcuts ──────────────────────────────────────────────
  useKeyboardShortcuts({ shortcuts: [
    { key: 'k', ctrlKey: true, action: () => { if (filters.canSearch && !search.loading) sse.buscarWithCollapse(); }, description: 'Search' },
    { key: 'a', ctrlKey: true, action: filters.selecionarTodos, description: 'Select all' },
    { key: 'Enter', ctrlKey: true, action: () => { if (filters.canSearch && !search.loading) sse.buscarWithCollapse(); }, description: 'Search alt' },
    { key: '/', action: () => uiState.setShowKeyboardHelp(true), description: 'Show shortcuts' },
    { key: 'Escape', action: filters.limparSelecao, description: 'Clear' },
  ] });

  // ── Computed: SearchResults props ───────────────────────────────────
  const isTrialExpiredOrQuota = billing.isTrialExpired || search.quotaError === "trial_expired";

  const { searchResultsProps } = useSearchComputedProps({
    search,
    filters,
    billing: { planInfo: billing.planInfo, trialPhase: billing.trialPhase },
    session,
    isTrialExpiredOrQuota,
    isProfileComplete: uiState.isProfileComplete,
    searchElapsed: sse.searchElapsed,
    partialDismissed: sse.partialDismissed,
    lastSearchAvailable: uiState.lastSearchAvailable,
    pdfLoading: uiState.pdfLoading,
    handleShowUpgradeModal: uiState.handleShowUpgradeModal,
    handleLoadLastSearch,
    handleRetryWithUfs: sse.handleRetryWithUfs,
    startResultsTour,
    isResultsTourCompleted,
    setPdfModalOpen: uiState.setPdfModalOpen,
    setPartialDismissed: sse.setPartialDismissed,
    trackEvent,
  });

  return {
    // Auth
    authLoading,
    session,

    // Plan/Trial — delegated to useSearchBillingState
    planInfo: billing.planInfo,
    trialPhase: billing.trialPhase,
    trialDaysRemaining: billing.trialDaysRemaining,
    isTrialExpired: billing.isTrialExpired,
    isGracePeriod: billing.isGracePeriod,
    graceDaysRemaining: billing.graceDaysRemaining,
    showTrialConversion: billing.showTrialConversion,
    setShowTrialConversion: billing.setShowTrialConversion,
    trialValue: billing.trialValue,
    trialValueLoading: billing.trialValueLoading,
    fetchTrialValue: billing.fetchTrialValue,
    showPaymentRecovery: billing.showPaymentRecovery,
    setShowPaymentRecovery: billing.setShowPaymentRecovery,

    // Core search
    filters,
    search,
    buscarWithCollapse: sse.buscarWithCollapse,

    // UI state — delegated to useSearchState
    showUpgradeModal: uiState.showUpgradeModal,
    setShowUpgradeModal: uiState.setShowUpgradeModal,
    upgradeSource: uiState.upgradeSource,
    handleShowUpgradeModal: uiState.handleShowUpgradeModal,
    showKeyboardHelp: uiState.showKeyboardHelp,
    setShowKeyboardHelp: uiState.setShowKeyboardHelp,
    customizeOpen: uiState.customizeOpen,
    setCustomizeOpen: uiState.setCustomizeOpen,
    showFirstUseTip: uiState.showFirstUseTip,
    dismissFirstUseTip: uiState.dismissFirstUseTip,
    drawerOpen: uiState.drawerOpen,
    setDrawerOpen: uiState.setDrawerOpen,
    lastSearchAvailable: uiState.lastSearchAvailable,
    hasSearchedBefore: uiState.hasSearchedBefore,
    isProfileComplete: uiState.isProfileComplete,

    // Onboarding
    showOnboardingBanner,
    setShowOnboardingBanner,
    autoSearchDismissed,
    setAutoSearchDismissed,
    shouldShowOnboarding,
    restartTour,
    restartSearchTour,
    restartResultsTour,
    // Tour elements — rendered in buscar/page.tsx
    onboardingTourElement: onboardingElement,
    searchTourActive,
    resultsTourActive,
    handleSearchTourComplete,
    handleSearchTourSkip,
    handleResultsTourComplete,
    handleResultsTourSkip,

    // Progress — delegated to useSearchSSE
    progressAreaRef: sse.progressAreaRef,
    searchElapsed: sse.searchElapsed,
    partialDismissed: sse.partialDismissed,
    setPartialDismissed: sse.setPartialDismissed,

    // Backend
    backendStatus: sse.backendStatus,

    // PDF
    pdfLoading: uiState.pdfLoading,
    pdfModalOpen: uiState.pdfModalOpen,
    setPdfModalOpen: uiState.setPdfModalOpen,
    handleGeneratePdf,

    // Error
    handleErrorBoundaryReset,
    handleLoadLastSearch,

    // Analytics
    trackEvent,

    // Router
    router,

    // Computed
    searchResultsProps,
  };
}
