"use client";

import { useState, useEffect, useRef, useMemo, useCallback, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import PullToRefresh from "react-simple-pull-to-refresh";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useOnboarding } from "../../hooks/useOnboarding";
import { useShepherdTour, type TourStep } from "../../hooks/useShepherdTour";
import { OnboardingTourButton } from "../../components/OnboardingTourButton";
import { useKeyboardShortcuts, getShortcutDisplay, type KeyboardShortcut } from "../../hooks/useKeyboardShortcuts";
import { usePlan } from "../../hooks/usePlan";
import { useTrialPhase } from "../../hooks/useTrialPhase";
import { useAuth } from "../components/AuthProvider";
import { ThemeToggle } from "../components/ThemeToggle";
import { UserMenu } from "../components/UserMenu";
import { SavedSearchesDropdown } from "../components/SavedSearchesDropdown";
import { QuotaBadge } from "../components/QuotaBadge";
import { PlanBadge } from "../components/PlanBadge";
import { UpgradeModal } from "../components/UpgradeModal";
import { TrialConversionScreen } from "../components/TrialConversionScreen";
import { TrialExpiringBanner } from "../components/TrialExpiringBanner";
import { TrialCountdown } from "../components/TrialCountdown";
import { Dialog } from "../components/Dialog";
import { useSearchFilters } from "./hooks/useSearchFilters";
import { useSearch } from "./hooks/useSearch";
import { useNavigationGuard } from "../../hooks/useNavigationGuard";
import SearchForm from "./components/SearchForm";
import SearchResults from "./components/SearchResults";
import BackendStatusIndicator, { useBackendStatusContext } from "../../components/BackendStatusIndicator";
import { SearchErrorBoundary } from "./components/SearchErrorBoundary";
import { MobileDrawer } from "../../components/MobileDrawer";
import { PaymentRecoveryModal } from "../../components/billing/PaymentRecoveryModal";
import PdfOptionsModal from "../../components/reports/PdfOptionsModal";

import { dateDiffInDays } from "../../lib/utils/dateDiffInDays";
import { toast } from "sonner";
import { checkHasLastSearch, getLastSearch } from "../../lib/lastSearchCache";
import type { BuscaResult } from "../types";

// White label branding configuration
const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic.tech";

// ============================================================================
// GTM-004: Onboarding Auto-Search Banners (AC11-13)
// ============================================================================

function OnboardingBanner({ message }: { message?: string }) {
  return (
    <div className="mb-4 p-4 rounded-lg bg-[var(--brand-blue)]/5 border border-[var(--brand-blue)]/20 flex items-center gap-3">
      <div className="w-5 h-5 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin flex-shrink-0" />
      <div>
        <p className="text-sm font-medium text-[var(--brand-blue)]">
          {message || "Analisando oportunidades com base no seu perfil..."}
        </p>
        <p className="text-xs text-[var(--ink-secondary)] mt-0.5">
          Isso leva ~15 segundos. Aguarde enquanto analisamos as fontes de dados.
        </p>
      </div>
    </div>
  );
}

function OnboardingSuccessBanner({
  count,
  onDismiss,
}: {
  count: number;
  onDismiss: () => void;
}) {
  return (
    <div className="mb-4 p-4 rounded-lg bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 flex items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <svg className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-sm font-medium text-green-800 dark:text-green-200">
          Encontramos {count} {count === 1 ? "oportunidade" : "oportunidades"} para você! Explore abaixo.
        </p>
      </div>
      <button
        onClick={onDismiss}
        className="px-3 py-1 text-xs font-medium rounded bg-green-100 dark:bg-green-800 text-green-700 dark:text-green-200 hover:bg-green-200 dark:hover:bg-green-700 transition-colors whitespace-nowrap"
      >
        Entendi
      </button>
    </div>
  );
}

function OnboardingEmptyState({ onAdjustFilters }: { onAdjustFilters: () => void }) {
  return (
    <div className="mb-4 p-6 rounded-lg bg-[var(--surface-1)] border border-[var(--border)] text-center">
      <svg className="w-12 h-12 mx-auto mb-3 text-[var(--ink-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <h3 className="text-lg font-semibold text-[var(--ink)] mb-2">
        Nenhuma oportunidade encontrada para seu perfil
      </h3>
      <p className="text-sm text-[var(--ink-secondary)] mb-4 max-w-md mx-auto">
        Não encontramos oportunidades recentes para o seu perfil. Isso é normal para segmentos muito específicos.
      </p>
      <div className="space-y-2 text-sm text-[var(--ink-secondary)] mb-4">
        <p>Sugestões para ampliar resultados:</p>
        <ul className="list-disc list-inside text-left max-w-sm mx-auto space-y-1">
          <li>Adicionar mais estados</li>
          <li>Ampliar a faixa de valor</li>
          <li>Expandir o período de análise</li>
        </ul>
      </div>
      <button
        onClick={onAdjustFilters}
        className="px-4 py-2 rounded-lg bg-[var(--brand-blue)] text-white text-sm font-medium hover:bg-[var(--brand-blue-hover)] transition-colors"
      >
        Ajustar Filtros
      </button>
    </div>
  );
}

// STORY-313: Tour step definitions (static, outside component to avoid re-creation)
const SEARCH_TOUR_STEPS: TourStep[] = [
  {
    id: 'search-setor',
    title: 'Escolha seu setor',
    text: '<span class="tour-step-counter">Passo 1 de 4</span><p>Escolha o setor da sua empresa para filtrar oportunidades relevantes.</p>',
    attachTo: { element: '[data-tour="setor-filter"]', on: 'bottom' },
  },
  {
    id: 'search-ufs',
    title: 'Selecione os estados',
    text: '<span class="tour-step-counter">Passo 2 de 4</span><p>Selecione os estados onde sua empresa atua ou quer atuar.</p>',
    attachTo: { element: '[data-tour="uf-selector"]', on: 'bottom' },
    beforeShowPromise: () => new Promise<void>((resolve) => {
      const btn = document.querySelector('[data-tour="customize-toggle"]') as HTMLElement;
      if (btn?.getAttribute('aria-expanded') === 'false') {
        btn.click();
        setTimeout(resolve, 400);
      } else {
        resolve();
      }
    }),
  },
  {
    id: 'search-period',
    title: 'Defina o periodo',
    text: '<span class="tour-step-counter">Passo 3 de 4</span><p>Defina o periodo para buscar editais recentes.</p>',
    attachTo: { element: '[data-tour="period-selector"]', on: 'bottom' },
  },
  {
    id: 'search-button',
    title: 'Inicie sua busca!',
    text: '<span class="tour-step-counter">Passo 4 de 4</span><p>Clique para iniciar sua busca inteligente!</p>',
    attachTo: { element: '[data-tour="search-button"]', on: 'top' },
  },
];

const RESULTS_TOUR_STEPS: TourStep[] = [
  {
    id: 'results-card',
    title: 'Suas oportunidades',
    text: '<span class="tour-step-counter">Passo 1 de 4</span><p>Cada card mostra uma oportunidade com data, valor e orgao.</p>',
    attachTo: { element: '[data-tour="result-card"]', on: 'bottom' },
  },
  {
    id: 'results-viability',
    title: 'Score de viabilidade',
    text: '<span class="tour-step-counter">Passo 2 de 4</span><p>O score de viabilidade indica o potencial desta oportunidade para sua empresa.</p>',
    attachTo: { element: '[data-tour="viability-badge"]', on: 'bottom' },
  },
  {
    id: 'results-pipeline',
    title: 'Pipeline de oportunidades',
    text: '<span class="tour-step-counter">Passo 3 de 4</span><p>Adicione ao pipeline para acompanhar oportunidades promissoras. Acesse pela pagina Pipeline no menu.</p>',
  },
  {
    id: 'results-excel',
    title: 'Exporte para Excel',
    text: '<span class="tour-step-counter">Passo 4 de 4</span><p>Exporte resultados para Excel para analise detalhada.</p>',
    attachTo: { element: '[data-tour="excel-button"]', on: 'top' },
  },
];

// Trial value type matching backend TrialValueResponse
interface TrialValue {
  total_opportunities: number;
  total_value: number;
  searches_executed: number;
  avg_opportunity_value: number;
  top_opportunity: { title: string; value: number } | null;
}

function HomePageContent() {
  const { session, loading: authLoading } = useAuth();
  const { planInfo } = usePlan();
  const { phase: trialPhase } = useTrialPhase();
  const { trackEvent } = useAnalytics();
  const router = useRouter();

  // GTM-010: Trial conversion state
  const [showTrialConversion, setShowTrialConversion] = useState(false);
  const [trialValue, setTrialValue] = useState<TrialValue | null>(null);
  const [trialValueLoading, setTrialValueLoading] = useState(false);

  // GTM-010: Calculate days remaining for trial
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

  // STORY-309 AC13/AC16/AC17: Grace period — searches suspended, show recovery modal
  const isGracePeriod = useMemo(() => {
    return planInfo?.dunning_phase === "grace_period";
  }, [planInfo?.dunning_phase]);

  const graceDaysRemaining = useMemo(() => {
    if (!isGracePeriod || planInfo?.days_since_failure == null) return 0;
    return Math.max(0, 21 - planInfo.days_since_failure);
  }, [isGracePeriod, planInfo?.days_since_failure]);

  // STORY-309 AC13: Show recovery modal during grace period
  const [showPaymentRecovery, setShowPaymentRecovery] = useState(false);

  useEffect(() => {
    if (isGracePeriod) {
      setShowPaymentRecovery(true);
    } else {
      setShowPaymentRecovery(false);
    }
  }, [isGracePeriod]);

  // GTM-010: Fetch trial value when trial is expired (for conversion screen)
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
      console.error("[GTM-010] Failed to fetch trial value:", err);
    } finally {
      setTrialValueLoading(false);
    }
  }, [session?.access_token]);

  // GTM-010: Auto-show conversion screen when trial expired
  useEffect(() => {
    if (isTrialExpired) {
      setShowTrialConversion(true);
      fetchTrialValue();
    }
  }, [isTrialExpired, fetchTrialValue]);

  // CRIT-008 AC9-AC10: Backend connectivity status
  const backendStatus = useBackendStatusContext();
  const queuedSearchRef = useRef<(() => void) | null>(null);

  // GTM-004: Auto-search from onboarding
  const searchParamsRaw = useSearchParams();
  const isAutoSearch = searchParamsRaw?.get('auto') === 'true';
  const autoSearchId = searchParamsRaw?.get('search_id') || null;
  const [showOnboardingBanner, setShowOnboardingBanner] = useState(isAutoSearch);
  const [autoSearchDismissed, setAutoSearchDismissed] = useState(false);

  // Upgrade modal state
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [upgradeSource, setUpgradeSource] = useState<string | undefined>();
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);

  // UX-346 AC1: Track whether user has ever searched (for progressive disclosure)
  const hasSearchedBefore = useMemo(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('smartlic-has-searched') === 'true';
  }, []);

  // UX-350 AC6: Check profile completeness for recommendation context
  const isProfileComplete = useMemo(() => {
    if (typeof window === 'undefined') return true;
    try {
      const cached = localStorage.getItem('profileContext');
      if (!cached) return false;
      const ctx = JSON.parse(cached);
      return !!(ctx.porte_empresa && ctx.ufs_atuacao?.length > 0);
    } catch { return false; }
  }, []);

  // GTM-UX-004 AC5: Check if last search exists in localStorage
  const [lastSearchAvailable, setLastSearchAvailable] = useState(() => checkHasLastSearch());

  // Customize accordion state (AC7: maintain in localStorage)
  // UX-346 AC1: First-time users always see collapsed; returning users use persisted state
  const [customizeOpen, setCustomizeOpen] = useState(() => {
    if (typeof window === 'undefined') return false;
    if (localStorage.getItem('smartlic-has-searched') !== 'true') return false;
    return localStorage.getItem('smartlic-customize-open') === 'open';
  });

  useEffect(() => {
    localStorage.setItem('smartlic-customize-open', customizeOpen ? 'open' : 'closed');
  }, [customizeOpen]);

  // UX-346 AC5: First-use tip (shown until first search or dismiss)
  const [showFirstUseTip, setShowFirstUseTip] = useState(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('smartlic-has-searched') !== 'true'
      && localStorage.getItem('smartlic-first-tip-dismissed') !== 'true';
  });

  const dismissFirstUseTip = useCallback(() => {
    setShowFirstUseTip(false);
    localStorage.setItem('smartlic-first-tip-dismissed', 'true');
  }, []);

  // STORY-313: Interactive guided tours (search + results)
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

  // Ref to start search tour from welcome tour callbacks (avoids stale closures)
  const searchTourStartRef = useRef<() => void>(() => {});
  searchTourStartRef.current = () => {
    if (!isSearchTourCompleted()) {
      startSearchTour();
      trackEvent('onboarding_tour_started', { tour: 'search' });
    }
  };

  // Onboarding (existing welcome tour)
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

  // STORY-313 AC1: Auto-start search tour on return visit (welcome tour already done)
  useEffect(() => {
    const welcomeDone = localStorage.getItem('smartlic_onboarding_completed') === 'true' ||
                         localStorage.getItem('smartlic_onboarding_dismissed') === 'true';
    if (welcomeDone && !isSearchTourCompleted()) {
      const timer = setTimeout(() => {
        startSearchTour();
        trackEvent('onboarding_tour_started', { tour: 'search' });
      }, 500);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // GTM-FIX-035 AC1: Ref for progress/results area (scroll target)
  const progressAreaRef = useRef<HTMLDivElement>(null);

  // Ref to break circular dependency between hooks:
  // useSearchFilters needs clearResult (from useSearch), useSearch needs filters
  const clearResultRef = useRef<() => void>(() => {});
  const filters = useSearchFilters(() => clearResultRef.current());
  const search = useSearch(filters);
  clearResultRef.current = () => search.setResult(null);

  // STORY-265 AC13: Show TrialConversionScreen when API returns 403 trial_expired
  useEffect(() => {
    if (search.quotaError === "trial_expired") {
      setShowTrialConversion(true);
      fetchTrialValue();
    }
  }, [search.quotaError, fetchTrialValue]);

  // STORY-313 AC7: Auto-start results tour after first search with >= 1 result
  const hasTriggeredResultsTourRef = useRef(false);
  useEffect(() => {
    if (
      search.result &&
      search.result.resumo?.total_oportunidades >= 1 &&
      !hasTriggeredResultsTourRef.current &&
      !isResultsTourCompleted()
    ) {
      hasTriggeredResultsTourRef.current = true;
      const timer = setTimeout(() => {
        startResultsTour();
        trackEvent('onboarding_tour_started', { tour: 'results' });
      }, 1500);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search.result]);

  // GTM-UX-004 AC7: Load last search results from cache
  const handleLoadLastSearch = useCallback(() => {
    const cached = getLastSearch();
    if (cached?.result) {
      search.setResult(cached.result as BuscaResult);
      toast.success("Resultados da última busca restaurados.");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // GTM-UX-004 AC5: Re-check localStorage after each search completes
  useEffect(() => {
    if (!search.loading) {
      setLastSearchAvailable(checkHasLastSearch());
    }
  }, [search.loading]);

  // GTM-FIX-035 AC1: Auto-collapse filters + scroll to progress when search starts
  const originalBuscar = search.buscar;
  const buscarWithCollapse = useCallback(() => {
    // CRIT-008 AC10: Queue search if backend is offline
    if (backendStatus.status === "offline") {
      toast.info("Servidor indisponível no momento. A busca será iniciada quando o servidor estiver disponível.");
      queuedSearchRef.current = () => {
        setCustomizeOpen(false);
        // UX-346 AC1/AC5: Mark user as having searched + dismiss first-use tip
        localStorage.setItem('smartlic-has-searched', 'true');
        setShowFirstUseTip(false);
        originalBuscar();
        setTimeout(() => {
          progressAreaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      };
      return;
    }
    setCustomizeOpen(false);
    // UX-346 AC1/AC5: Mark user as having searched + dismiss first-use tip
    localStorage.setItem('smartlic-has-searched', 'true');
    setShowFirstUseTip(false);
    originalBuscar();
    // Smooth-scroll to progress area after a tick (let state update + render)
    setTimeout(() => {
      progressAreaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }, [originalBuscar, backendStatus.status]);

  // CRIT-008 AC10: Execute queued search when backend recovers
  useEffect(() => {
    if ((backendStatus.status === "online" || backendStatus.status === "recovering") && queuedSearchRef.current) {
      const queuedFn = queuedSearchRef.current;
      queuedSearchRef.current = null;
      toast.success("Servidor disponível. Executando busca...");
      queuedFn();
    }
  }, [backendStatus.status]);

  // TD-006 AC9-15: Navigation guard — warn before leaving with active results
  const [hasDownloaded, setHasDownloaded] = useState(false);
  // Reset download flag when a new search starts
  useEffect(() => {
    if (search.loading) setHasDownloaded(false);
  }, [search.loading]);
  const originalHandleDownload = search.handleDownload;
  const handleDownloadWithGuard = async () => {
    await originalHandleDownload();
    // After successful download, suppress navigation guard (AC15)
    if (!search.downloadError) {
      setHasDownloaded(true);
    }
  };

  // STORY-325: PDF Diagnostico Report
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
        toast.error(err.error || "Erro ao gerar relatório PDF");
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
      toast.error("Erro ao gerar relatório PDF. Tente novamente.");
    } finally {
      setPdfLoading(false);
    }
  }, [session, search.searchId, filters.sectorName, trackEvent]);

  // CRIT-002 AC2: Reset handler for error boundary
  const handleErrorBoundaryReset = useCallback(() => {
    search.setResult(null);
    search.setError(null);
  }, [search]);

  useNavigationGuard({
    hasResults: !!search.result && (search.result.total_filtrado ?? 0) > 0,
    hasDownloaded,
  });

  // STORY-257B AC5: Elapsed seconds tracker for partial results prompt
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

  // Restore search state on mount
  useEffect(() => { search.restoreSearchStateOnMount(); }, []);

  // GTM-004: Auto-search from onboarding
  useEffect(() => {
    if (isAutoSearch && autoSearchId && !autoSearchDismissed) {
      setShowOnboardingBanner(true);
    }
  }, [isAutoSearch, autoSearchId, autoSearchDismissed]);

  // Keyboard shortcuts
  useKeyboardShortcuts({ shortcuts: [
    { key: 'k', ctrlKey: true, action: () => { if (filters.canSearch && !search.loading) buscarWithCollapse(); }, description: 'Search' },
    { key: 'a', ctrlKey: true, action: filters.selecionarTodos, description: 'Select all' },
    { key: 'Enter', ctrlKey: true, action: () => { if (filters.canSearch && !search.loading) buscarWithCollapse(); }, description: 'Search alt' },
    { key: '/', action: () => setShowKeyboardHelp(true), description: 'Show shortcuts' },
    { key: 'Escape', action: filters.limparSelecao, description: 'Clear' },
  ] });

  const handleShowUpgradeModal = (_plan?: string, source?: string) => {
    setUpgradeSource(source);
    setShowUpgradeModal(true);
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--brand-blue)] mx-auto mb-4"></div>
          <p className="text-[var(--ink-secondary)]">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Page Header */}
      <header className="sticky top-0 z-40 bg-[var(--surface-0)] backdrop-blur-sm supports-[backdrop-filter]:bg-[var(--surface-0)]/95 border-b border-[var(--border)] shadow-sm">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <div className="flex items-center gap-3">
            {/* Logo visible only on mobile (sidebar hidden) */}
            <Link href="/buscar" className="lg:hidden text-xl font-bold text-brand-navy hover:text-brand-blue transition-colors">
              SmartLic<span className="text-brand-blue">.tech</span>
            </Link>
            <span className="hidden lg:block text-base font-semibold text-[var(--ink)]">
              Buscar Licitações
            </span>
          </div>

          {/* UX-340 AC1: Mobile — hamburger with "Menu" label (AC8: ≥44px touch) */}
          <button
            onClick={() => setDrawerOpen(true)}
            className="lg:hidden flex items-center gap-1.5 min-w-[44px] min-h-[44px] px-3 rounded-lg text-[var(--ink-secondary)] hover:text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors"
            aria-label="Abrir menu"
            data-testid="mobile-menu-button"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
            <span className="text-sm font-medium">Menu</span>
          </button>

          {/* AC10: Desktop — full controls (unchanged) */}
          <div className="hidden lg:flex items-center gap-2 sm:gap-3">
            <BackendStatusIndicator />
            <SavedSearchesDropdown onLoadSearch={search.handleLoadSearch} onAnalyticsEvent={trackEvent} />
            <ThemeToggle />
            <UserMenu
              onRestartTour={!shouldShowOnboarding ? restartTour : undefined}
              statusSlot={
                <>
                  <QuotaBadge />
                  {planInfo && (
                    <PlanBadge
                      planId={planInfo.plan_id}
                      planName={planInfo.plan_name}
                      trialExpiresAt={planInfo.trial_expires_at ?? undefined}
                      onClick={() => handleShowUpgradeModal(undefined, "plan_badge")}
                    />
                  )}
                  {/* GTM-010 AC10: Trial countdown badge */}
                  {trialDaysRemaining !== null && trialDaysRemaining > 0 && (
                    <TrialCountdown daysRemaining={trialDaysRemaining} />
                  )}
                </>
              }
            />
          </div>
        </div>
      </header>

      {/* UX-340 AC4: Mobile drawer */}
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />

      <main id="main-content" className="max-w-5xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        <PullToRefresh
          onRefresh={search.handleRefresh}
          pullingContent=""
          refreshingContent={
            <div className="flex justify-center py-4">
              <div className="w-6 h-6 border-2 border-brand-blue border-t-transparent rounded-full animate-spin" />
            </div>
          }
          resistance={3}
          className="pull-to-refresh-wrapper"
        >
          <div>
            {/* GTM-010 AC9: Trial expiring banner (day 6) */}
            {trialDaysRemaining !== null && trialDaysRemaining <= 1 && !isTrialExpired && (
              <TrialExpiringBanner
                daysRemaining={trialDaysRemaining}
                onConvert={() => {
                  setShowTrialConversion(true);
                  fetchTrialValue();
                }}
              />
            )}

            {/* Page Title */}
            <div className="mb-8 animate-fade-in-up">
              <h1 className="text-2xl sm:text-3xl font-bold font-display text-ink">Busca de Licitações</h1>
              <p className="text-ink-secondary mt-1 text-sm sm:text-base">
                Encontre oportunidades de contratação pública de acordo com o momento do seu negócio.
              </p>
            </div>

            <SearchForm
              {...filters}
              loading={search.loading}
              buscar={buscarWithCollapse}
              searchButtonRef={search.searchButtonRef}
              result={search.result}
              handleSaveSearch={search.handleSaveSearch}
              isMaxCapacity={search.isMaxCapacity}
              planInfo={planInfo}
              onShowUpgradeModal={handleShowUpgradeModal}
              clearResult={() => search.setResult(null)}
              customizeOpen={customizeOpen}
              setCustomizeOpen={setCustomizeOpen}
              showFirstUseTip={showFirstUseTip}
              onDismissFirstUseTip={dismissFirstUseTip}
              isTrialExpired={isTrialExpired || search.quotaError === "trial_expired"}
              isGracePeriod={isGracePeriod}
            />

            {/* GTM-004: Auto-search banners */}
            {showOnboardingBanner && !autoSearchDismissed && search.loading && (
              <OnboardingBanner />
            )}
            {showOnboardingBanner && !autoSearchDismissed && !search.loading && search.result && search.result.resumo.total_oportunidades > 0 && (
              <OnboardingSuccessBanner
                count={search.result.resumo.total_oportunidades}
                onDismiss={() => {
                  setAutoSearchDismissed(true);
                  setShowOnboardingBanner(false);
                }}
              />
            )}
            {showOnboardingBanner && !autoSearchDismissed && !search.loading && search.result && search.result.resumo.total_oportunidades === 0 && (
              <OnboardingEmptyState
                onAdjustFilters={() => {
                  setAutoSearchDismissed(true);
                  setShowOnboardingBanner(false);
                }}
              />
            )}

            {/* STAB-005 AC2: Removed inline empty state — now handled by ZeroResultsSuggestions in SearchResults with filter stats */}

            {/* GTM-FIX-035 AC1: Scroll target for progress area */}
            <div ref={progressAreaRef} />

            {/* CRIT-002 AC1: Error boundary wraps results area (NOT SearchForm) */}
            <SearchErrorBoundary onReset={handleErrorBoundaryReset}>
              <SearchResults
                loading={search.loading}
                loadingStep={search.loadingStep}
                estimatedTime={search.estimateSearchTime(filters.ufsSelecionadas.size, dateDiffInDays(filters.dataInicial, filters.dataFinal))}
                stateCount={filters.ufsSelecionadas.size}
                statesProcessed={search.statesProcessed}
                onCancel={search.cancelSearch}
                sseEvent={search.sseEvent}
                useRealProgress={search.useRealProgress}
                sseAvailable={search.sseAvailable}
                sseDisconnected={search.sseDisconnected}
                isReconnecting={search.isReconnecting}
                isDegraded={search.isDegraded}
                degradedDetail={search.degradedDetail}
                onStageChange={(stage) => trackEvent('search_progress_stage', { stage, is_sse: search.useRealProgress && search.sseAvailable })}
                error={search.error}
                quotaError={search.quotaError}
                result={search.result}
                rawCount={search.rawCount}
                ufsSelecionadas={filters.ufsSelecionadas}
                sectorName={filters.sectorName}
                searchMode={filters.searchMode}
                termosArray={filters.termosArray}
                ordenacao={filters.ordenacao}
                onOrdenacaoChange={filters.setOrdenacao}
                downloadLoading={search.downloadLoading}
                downloadError={search.downloadError}
                onDownload={handleDownloadWithGuard}
                onSearch={search.buscar}
                planInfo={planInfo}
                session={session}
                onShowUpgradeModal={handleShowUpgradeModal}
                onTrackEvent={trackEvent}
                // STORY-257B: UF Progress Grid (AC1-4)
                ufStatuses={search.ufStatuses}
                ufTotalFound={search.ufTotalFound}
                ufAllComplete={search.ufAllComplete}
                // STORY-257B: Partial results (AC5)
                searchElapsedSeconds={searchElapsed}
                onViewPartial={search.cancelSearch}
                partialDismissed={partialDismissed}
                onDismissPartial={() => setPartialDismissed(true)}
                // STORY-257B: Cache refresh (AC9)
                onRetryForceFresh={search.buscarForceFresh}
                // STORY-257B: Sources unavailable (AC10)
                hasLastSearch={lastSearchAvailable}
                onLoadLastSearch={handleLoadLastSearch}
                // A-04: Progressive delivery
                liveFetchInProgress={search.liveFetchInProgress}
                refreshAvailable={search.refreshAvailable}
                onRefreshResults={search.handleRefreshResults}
                // D-05: Feedback loop
                searchId={search.searchId || undefined}
                setorId={filters.setorId}
                // UX-350: Profile completeness
                isProfileComplete={isProfileComplete}
                // CRIT-008 + GTM-UX-003: Unified retry
                retryCountdown={search.retryCountdown}
                retryMessage={search.retryMessage}
                retryExhausted={search.retryExhausted}
                onRetryNow={search.retryNow}
                onCancelRetry={search.cancelRetry}
                // STORY-265 AC16: Disable Excel download when trial expired
                isTrialExpired={isTrialExpired || search.quotaError === "trial_expired"}
                // STORY-295: Progressive results
                sourceStatuses={search.sourceStatuses}
                partialProgress={search.partialProgress}
                filterSummary={search.filterSummary}
                // STORY-320: Trial paywall
                trialPhase={trialPhase}
                paywallApplied={search.result?.paywall_applied}
                totalBeforePaywall={search.result?.total_before_paywall}
                // STORY-325: PDF Diagnostico
                onGeneratePdf={() => setPdfModalOpen(true)}
                pdfLoading={pdfLoading}
                // SAB-005 AC1: Skeleton timeout
                skeletonTimeoutReached={search.skeletonTimeoutReached}
              />
            </SearchErrorBoundary>
          </div>
        </PullToRefresh>
      </main>

      {/* Save Search Dialog */}
      <Dialog
        isOpen={search.showSaveDialog}
        onClose={() => { search.setShowSaveDialog(false); search.setSaveSearchName(""); }}
        title="Salvar Busca"
        className="max-w-md"
        id="save-search"
      >
        <div className="mb-4">
          <label htmlFor="save-search-name" className="block text-sm font-medium text-ink-secondary mb-2">Nome da busca:</label>
          <input
            id="save-search-name"
            type="text"
            value={search.saveSearchName}
            onChange={(e) => search.setSaveSearchName(e.target.value)}
            placeholder="Ex: Informática Sul do Brasil"
            className="w-full border border-strong rounded-input px-4 py-2.5 text-base bg-surface-0 text-ink focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue transition-colors"
            maxLength={50}
            autoFocus
          />
          <p className="text-xs text-ink-muted mt-1">{(search.saveSearchName ?? '').length}/50 caracteres</p>
        </div>
        {search.saveError && (
          <div className="mb-4 p-3 bg-error-subtle border border-error/20 rounded text-sm text-error" role="alert">{search.saveError}</div>
        )}
        <div className="flex gap-3 justify-end">
          <button
            onClick={() => { search.setShowSaveDialog(false); search.setSaveSearchName(""); }}
            type="button"
            className="px-4 py-2 text-sm font-medium text-ink-secondary hover:text-ink hover:bg-surface-1 rounded-button transition-colors"
          >Cancelar</button>
          <button
            onClick={search.confirmSaveSearch}
            disabled={!(search.saveSearchName ?? '').trim()}
            type="button"
            className="px-4 py-2 text-sm font-medium text-white bg-brand-navy hover:bg-brand-blue-hover rounded-button transition-colors disabled:bg-ink-faint disabled:cursor-not-allowed"
          >Salvar</button>
        </div>
      </Dialog>

      {/* Keyboard Shortcuts Help */}
      <Dialog
        isOpen={showKeyboardHelp}
        onClose={() => setShowKeyboardHelp(false)}
        title="Atalhos de Teclado"
        className="max-w-lg"
        id="keyboard-help"
      >
        <div className="space-y-3">
          {([
            ["Executar busca", { key: 'k', ctrlKey: true, action: () => {}, description: '' }],
            ["Selecionar todos os estados", { key: 'a', ctrlKey: true, action: () => {}, description: '' }],
            ["Executar busca (alternativo)", { key: 'Enter', ctrlKey: true, action: () => {}, description: '' }],
          ] as [string, KeyboardShortcut][]).map(([label, shortcut]) => (
            <div key={label} className="flex items-center justify-between py-2 border-b border-strong">
              <span className="text-ink">{label}</span>
              <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">
                {getShortcutDisplay(shortcut)}
              </kbd>
            </div>
          ))}
          <div className="flex items-center justify-between py-2 border-b border-strong">
            <span className="text-ink">Limpar todos os filtros</span>
            <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">Ctrl+Shift+L</kbd>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-strong">
            <span className="text-ink">Limpar seleção</span>
            <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">Esc</kbd>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-ink">Mostrar atalhos</span>
            <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">/</kbd>
          </div>
        </div>
        <button
          onClick={() => setShowKeyboardHelp(false)}
          type="button"
          className="mt-4 w-full px-4 py-2 text-sm font-medium text-white bg-brand-navy hover:bg-brand-blue-hover rounded-button transition-colors"
        >Entendi</button>
      </Dialog>

      {/* GTM-POLISH-001 AC8: Footer always visible (not hidden without results) */}
      <footer className="bg-surface-1 text-ink border-t border-[var(--border)] mt-12" role="contentinfo">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Sobre</h3>
              <ul className="space-y-2 text-sm text-ink-secondary">
                <li><a href="/#sobre" className="hover:text-brand-blue transition-colors">Quem somos</a></li>
                <li><a href="/#como-funciona" className="hover:text-brand-blue transition-colors">Como funciona</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Planos</h3>
              <ul className="space-y-2 text-sm text-ink-secondary">
                <li><a href="/planos" className="hover:text-brand-blue transition-colors">Planos e Preços</a></li>
                <li><button onClick={() => setShowKeyboardHelp(true)} className="hover:text-brand-blue transition-colors text-left">Atalhos de Teclado</button></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Suporte</h3>
              <ul className="space-y-2 text-sm text-ink-secondary">
                <li><a href="/mensagens" className="hover:text-brand-blue transition-colors">Central de Ajuda</a></li>
                <li><a href="/mensagens" className="hover:text-brand-blue transition-colors">Contato</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Legal</h3>
              <ul className="space-y-2 text-sm text-ink-secondary">
                <li><a href="/privacidade" className="hover:text-brand-blue transition-colors">Política de Privacidade</a></li>
                <li><a href="/termos" className="hover:text-brand-blue transition-colors">Termos de Uso</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-[var(--border-strong)] pt-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <p className="text-sm text-ink-secondary">© 2026 {APP_NAME}. Todos os direitos reservados.</p>
              <p className="text-sm text-ink-secondary">CONFENGE Avaliações e Inteligência Artificial LTDA</p>
            </div>
          </div>
        </div>
      </footer>

      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        source={upgradeSource}
      />

      {/* STORY-325: PDF Diagnostico Options Modal */}
      <PdfOptionsModal
        isOpen={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
        onGenerate={handleGeneratePdf}
        isGenerating={pdfLoading}
        sectorName={filters.sectorName}
        totalResults={search.result?.resumo?.total_oportunidades ?? 0}
      />

      {/* GTM-010 AC4/AC7: Trial conversion screen (full-screen overlay) */}
      {showTrialConversion && (
        <TrialConversionScreen
          trialValue={trialValue}
          onClose={() => {
            // AC8: Close → redirect to /planos
            setShowTrialConversion(false);
            router.push("/planos");
          }}
          loading={trialValueLoading}
        />
      )}

      {/* STORY-313 AC15: Floating guide button */}
      <OnboardingTourButton
        availableTours={{
          search: restartSearchTour,
          results: restartResultsTour,
        }}
      />

      {/* STORY-309 AC13: Payment recovery modal during grace period */}
      {showPaymentRecovery && (
        <PaymentRecoveryModal
          daysRemaining={graceDaysRemaining}
          trialValue={trialValue}
          onClose={() => setShowPaymentRecovery(false)}
        />
      )}
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <p className="text-[var(--ink-secondary)]">Carregando...</p>
      </div>
    }>
      <HomePageContent />
    </Suspense>
  );
}
