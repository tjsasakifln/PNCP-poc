"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Image from "next/image";
import PullToRefresh from "react-simple-pull-to-refresh";
import type { BuscaResult, ValidationErrors, Setor } from "./types";
import { EnhancedLoadingProgress } from "../components/EnhancedLoadingProgress";
import { LoadingResultsSkeleton } from "./components/LoadingResultsSkeleton";
import { EmptyState } from "./components/EmptyState";
import { ThemeToggle } from "./components/ThemeToggle";
import { UserMenu } from "./components/UserMenu";
import { RegionSelector } from "./components/RegionSelector";
import { SavedSearchesDropdown } from "./components/SavedSearchesDropdown";
import { CustomSelect } from "./components/CustomSelect";
import { CustomDateInput } from "./components/CustomDateInput";
import { useAnalytics } from "../hooks/useAnalytics";
import { useSavedSearches } from "../hooks/useSavedSearches";
import { useOnboarding } from "../hooks/useOnboarding";
import { useKeyboardShortcuts, getShortcutDisplay } from "../hooks/useKeyboardShortcuts";
import { useQuota } from "../hooks/useQuota";
import { usePlan } from "../hooks/usePlan";
import { useAuth } from "./components/AuthProvider";
import { QuotaBadge } from "./components/QuotaBadge";
import { PlanBadge } from "./components/PlanBadge";
import { QuotaCounter } from "./components/QuotaCounter";
import { UpgradeModal } from "./components/UpgradeModal";
import { LicitacoesPreview } from "./components/LicitacoesPreview";
import type { SavedSearch } from "../lib/savedSearches";

// P0 Filters
import { StatusFilter, type StatusLicitacao } from "../components/StatusFilter";
import { ModalidadeFilter } from "../components/ModalidadeFilter";
import { ValorFilter } from "../components/ValorFilter";

// P1 Filters
import { EsferaFilter, type Esfera } from "./components/EsferaFilter";
import { MunicipioFilter, type Municipio } from "./components/MunicipioFilter";
import { OrdenacaoSelect, type OrdenacaoOption } from "./components/OrdenacaoSelect";

// White label branding configuration
const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic";
const LOGO_URL = process.env.NEXT_PUBLIC_LOGO_URL || "/logo.svg";

const UFS = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
  "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
  "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

const UF_NAMES: Record<string, string> = {
  AC: "Acre", AL: "Alagoas", AP: "Amapá", AM: "Amazonas", BA: "Bahia",
  CE: "Ceará", DF: "Distrito Federal", ES: "Espírito Santo", GO: "Goiás",
  MA: "Maranhão", MT: "Mato Grosso", MS: "Mato Grosso do Sul", MG: "Minas Gerais",
  PA: "Pará", PB: "Paraíba", PR: "Paraná", PE: "Pernambuco", PI: "Piauí",
  RJ: "Rio de Janeiro", RN: "Rio Grande do Norte", RS: "Rio Grande do Sul",
  RO: "Rondônia", RR: "Roraima", SC: "Santa Catarina", SP: "São Paulo",
  SE: "Sergipe", TO: "Tocantins",
};

// Portuguese stopwords — filtered out of custom search terms to avoid generic matches.
// Mirrors the backend STOPWORDS_PT set in filter.py.
const STOPWORDS_PT = new Set([
  "o","a","os","as","um","uma","uns","umas",
  "de","do","da","dos","das","em","no","na","nos","nas",
  "por","pelo","pela","pelos","pelas","para","pra","pro",
  "com","sem","sob","sobre","entre","ate","desde","apos",
  "perante","contra","ante",
  "ao","aos","num","numa","nuns","numas",
  "e","ou","mas","porem","que","se","como","quando","porque","pois",
  "nem","tanto","quanto","logo","portanto",
  "nao","mais","muito","tambem","ja","ainda","so","apenas",
  "ser","ter","estar","ir","vir","fazer","dar","ver",
  "ha","foi","sao","era","sera",
]);

/** Strip accents from a string for stopword comparison */
function stripAccents(s: string): string {
  return s.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function isStopword(word: string): boolean {
  return STOPWORDS_PT.has(stripAccents(word.toLowerCase()));
}

function dateDiffInDays(date1: string, date2: string): number {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// Inner component that uses searchParams
function HomePageContent() {
  // URL search params for re-run search (Issue #154)
  const searchParams = useSearchParams();
  const [urlParamsApplied, setUrlParamsApplied] = useState(false);

  // Auth and quota
  const { session, loading: authLoading } = useAuth();
  const { quota, refresh: refreshQuota } = useQuota();
  const { planInfo, refresh: refreshPlan } = usePlan();

  // Upgrade modal state
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [preSelectedPlan, setPreSelectedPlan] = useState<"consultor_agil" | "maquina" | "sala_guerra" | undefined>();
  const [upgradeSource, setUpgradeSource] = useState<string | undefined>();

  // Analytics tracking
  // IMPORTANT: All hooks must be called unconditionally BEFORE any early returns
  // to comply with React's Rules of Hooks (Error #310 fix)
  const { trackEvent } = useAnalytics();

  // Saved searches
  const { saveNewSearch, isMaxCapacity } = useSavedSearches();
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveSearchName, setSaveSearchName] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);

  // Interactive onboarding (Feature #3)
  const { shouldShowOnboarding, restartTour } = useOnboarding({
    autoStart: true,
    onComplete: () => {
      trackEvent('onboarding_completed', {
        completion_time: Date.now(),
      });
    },
    onDismiss: () => {
      trackEvent('onboarding_dismissed', {
        dismissed_at: Date.now(),
      });
    },
    onStepChange: (stepId, stepIndex) => {
      trackEvent('onboarding_step', {
        step_id: stepId,
        step_index: stepIndex,
      });
    },
  });

  const [setores, setSetores] = useState<Setor[]>([]);
  const [setorId, setSetorId] = useState("vestuario");
  const [searchMode, setSearchMode] = useState<"setor" | "termos">("setor");
  const [termosArray, setTermosArray] = useState<string[]>([]);
  const [termoInput, setTermoInput] = useState("");

  // P0 Filter states
  const [status, setStatus] = useState<StatusLicitacao>("recebendo_proposta");
  const [modalidades, setModalidades] = useState<number[]>([]);
  const [valorMin, setValorMin] = useState<number | null>(null);
  const [valorMax, setValorMax] = useState<number | null>(null);

  // P1 Filter states
  const [esferas, setEsferas] = useState<Esfera[]>([]);
  const [municipios, setMunicipios] = useState<Municipio[]>([]);
  const [ordenacao, setOrdenacao] = useState<OrdenacaoOption>("data_desc");

  const [ufsSelecionadas, setUfsSelecionadas] = useState<Set<string>>(
    new Set(["SC", "PR", "RS"])
  );
  const [dataInicial, setDataInicial] = useState(() => {
    const now = new Date(new Date().toLocaleString("en-US", { timeZone: "America/Sao_Paulo" }));
    now.setDate(now.getDate() - 7);
    return now.toISOString().split("T")[0];
  });
  const [dataFinal, setDataFinal] = useState(() => {
    const now = new Date(new Date().toLocaleString("en-US", { timeZone: "America/Sao_Paulo" }));
    return now.toISOString().split("T")[0];
  });

  // Apply URL params on mount (Issue #154: Re-run search from history)
  useEffect(() => {
    if (urlParamsApplied) return;

    const ufsParam = searchParams.get('ufs');
    const dataInicialParam = searchParams.get('data_inicial');
    const dataFinalParam = searchParams.get('data_final');
    const modeParam = searchParams.get('mode');
    const setorParam = searchParams.get('setor');
    const termosParam = searchParams.get('termos');

    // Only apply if we have UFs (minimum required param)
    if (ufsParam) {
      const ufsArray = ufsParam.split(',').filter(uf => UFS.includes(uf));
      if (ufsArray.length > 0) {
        setUfsSelecionadas(new Set(ufsArray));

        if (dataInicialParam) setDataInicial(dataInicialParam);
        if (dataFinalParam) setDataFinal(dataFinalParam);

        if (modeParam === 'termos' && termosParam) {
          setSearchMode('termos');
          setTermosArray(termosParam.split(' ').filter(Boolean));
        } else if (modeParam === 'setor' && setorParam) {
          setSearchMode('setor');
          setSetorId(setorParam);
        }

        // Track that params were loaded from URL (re-run search)
        trackEvent('search_params_loaded_from_url', {
          ufs: ufsArray,
          mode: modeParam,
          setor: setorParam,
          has_termos: Boolean(termosParam),
        });
      }
    }

    setUrlParamsApplied(true);
  }, [searchParams, urlParamsApplied, trackEvent]);

  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(1);
  const [statesProcessed, setStatesProcessed] = useState(0); // Issue #109: Track state progress
  const [error, setError] = useState<string | null>(null);
  const [quotaError, setQuotaError] = useState<string | null>(null); // Issue #153: Quota exceeded
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [result, setResult] = useState<BuscaResult | null>(null);
  const [rawCount, setRawCount] = useState(0);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);

  // Refs for keyboard shortcuts
  const searchButtonRef = useRef<HTMLButtonElement>(null);

  // Ref to store last search params for pull-to-refresh (Issue #119)
  const lastSearchParamsRef = useRef<{
    ufs: Set<string>;
    dataInicial: string;
    dataFinal: string;
    searchMode: "setor" | "termos";
    setorId?: string;
    termosArray?: string[];
    status: StatusLicitacao;
    modalidades: number[];
    valorMin: number | null;
    valorMax: number | null;
    esferas: Esfera[];
    municipios: Municipio[];
    ordenacao: OrdenacaoOption;
  } | null>(null);

  // Clear municipios when UFs change (they depend on selected UFs)
  useEffect(() => {
    setMunicipios([]);
  }, [Array.from(ufsSelecionadas).sort().join(",")]);

  useEffect(() => {
    fetch("/api/setores")
      .then(res => res.json())
      .then(data => {
        if (data.setores) setSetores(data.setores);
      })
      .catch(() => {
        setSetores([
          { id: "vestuario", name: "Vestuário e Uniformes", description: "" },
          { id: "alimentos", name: "Alimentos e Merenda", description: "" },
          { id: "informatica", name: "Informática e Tecnologia", description: "" },
          { id: "limpeza", name: "Produtos de Limpeza", description: "" },
          { id: "mobiliario", name: "Mobiliário", description: "" },
          { id: "papelaria", name: "Papelaria e Material de Escritório", description: "" },
          { id: "engenharia", name: "Engenharia e Construção", description: "" },
          { id: "software", name: "Software e Sistemas", description: "" },
        ]);
      });
  }, []);

  function validateForm(): ValidationErrors {
    const errors: ValidationErrors = {};
    if (ufsSelecionadas.size === 0) {
      errors.ufs = "Selecione pelo menos um estado";
    }
    if (dataFinal < dataInicial) {
      errors.date_range = "Data final deve ser maior ou igual à data inicial";
    }
    return errors;
  }

  const canSearch = Object.keys(validateForm()).length === 0
    && (searchMode === "setor" || termosArray.length > 0);

  useEffect(() => {
    setValidationErrors(validateForm());
  }, [ufsSelecionadas, dataInicial, dataFinal]);

  // Keyboard shortcuts - Issue #122
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: 'k',
        ctrlKey: true,
        action: () => {
          if (!loading && canSearch) {
            searchButtonRef.current?.click();
            trackEvent('keyboard_shortcut_used', { shortcut: 'Ctrl+K', action: 'search' });
          }
        },
        description: 'Executar busca'
      },
      {
        key: 'Escape',
        action: () => {
          setUfsSelecionadas(new Set());
          setResult(null);
          trackEvent('keyboard_shortcut_used', { shortcut: 'Escape', action: 'clear_selection' });
        },
        description: 'Limpar seleção de UFs'
      },
      {
        key: 'a',
        ctrlKey: true,
        action: () => {
          selecionarTodos();
          trackEvent('keyboard_shortcut_used', { shortcut: 'Ctrl+A', action: 'select_all' });
        },
        description: 'Selecionar todos os estados'
      },
      {
        key: '/',
        action: () => {
          setShowKeyboardHelp(true);
          trackEvent('keyboard_shortcut_used', { shortcut: '/', action: 'show_help' });
        },
        description: 'Mostrar atalhos de teclado'
      }
    ],
    enabled: !showKeyboardHelp && !showSaveDialog
  });

  const toggleUf = (uf: string) => {
    const newSet = new Set(ufsSelecionadas);
    if (newSet.has(uf)) {
      newSet.delete(uf);
    } else {
      newSet.add(uf);
    }
    setUfsSelecionadas(newSet);
    setResult(null);
  };

  const toggleRegion = (regionUfs: string[]) => {
    const allSelected = regionUfs.every(uf => ufsSelecionadas.has(uf));
    const newSet = new Set(ufsSelecionadas);
    if (allSelected) {
      regionUfs.forEach(uf => newSet.delete(uf));
    } else {
      regionUfs.forEach(uf => newSet.add(uf));
    }
    setUfsSelecionadas(newSet);
    setResult(null);
  };

  const selecionarTodos = () => { setUfsSelecionadas(new Set(UFS)); setResult(null); };
  const limparSelecao = () => { setUfsSelecionadas(new Set()); setResult(null); };

  const sectorName = searchMode === "setor"
    ? (setores.find(s => s.id === setorId)?.name || "Licitações")
    : "Licitações";

  const searchLabel = searchMode === "setor"
    ? sectorName
    : termosArray.length > 0
      ? `"${termosArray.join('", "')}"`
      : "Licitações";

  const buscar = async () => {
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    // Save search params for pull-to-refresh (Issue #119)
    lastSearchParamsRef.current = {
      ufs: new Set(ufsSelecionadas),
      dataInicial,
      dataFinal,
      searchMode,
      setorId: searchMode === "setor" ? setorId : undefined,
      termosArray: searchMode === "termos" ? [...termosArray] : undefined,
      status,
      modalidades: [...modalidades],
      valorMin,
      valorMax,
      esferas: [...esferas],
      municipios: [...municipios],
      ordenacao,
    };

    setLoading(true);
    setLoadingStep(1);
    setStatesProcessed(0); // Issue #109: Reset progress counter
    setError(null);
    setQuotaError(null); // Issue #153: Reset quota error
    setResult(null);
    setRawCount(0);

    const searchStartTime = Date.now();

    // Issue #109: Simulate progressive state processing for better UX feedback
    // In a real streaming implementation, this would be updated by backend SSE events
    const totalStates = ufsSelecionadas.size;
    let stateIntervalId: ReturnType<typeof setInterval> | null = null;

    stateIntervalId = setInterval(() => {
      setStatesProcessed(prev => {
        if (prev >= totalStates) {
          if (stateIntervalId) clearInterval(stateIntervalId);
          return totalStates;
        }
        // Increment every ~3 seconds to simulate processing (totalStates * 6s / 2 intervals)
        return prev + 1;
      });
    }, totalStates > 0 ? Math.max(2000, (totalStates * 6000) / (totalStates + 1)) : 3000);

    // Helper to cleanup interval
    const cleanupInterval = () => {
      if (stateIntervalId) {
        clearInterval(stateIntervalId);
        stateIntervalId = null;
      }
    };

    // Track search_started event
    trackEvent('search_started', {
      ufs: Array.from(ufsSelecionadas),
      uf_count: ufsSelecionadas.size,
      date_range: {
        inicial: dataInicial,
        final: dataFinal,
        days: dateDiffInDays(dataInicial, dataFinal),
      },
      search_mode: searchMode,
      setor_id: searchMode === "setor" ? setorId : null,
      termos_busca: searchMode === "termos" ? termosArray.join(" ") : null,
      termos_count: termosArray.length,
    });

    try {
      // Issue #153: Include auth header for quota tracking
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (session?.access_token) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }

      const response = await fetch("/api/buscar", {
        method: "POST",
        headers,
        body: JSON.stringify({
          ufs: Array.from(ufsSelecionadas),
          data_inicial: dataInicial,
          data_final: dataFinal,
          setor_id: searchMode === "setor" ? setorId : null,
          termos_busca: searchMode === "termos" ? termosArray.join(" ") : null,
          // New filter parameters
          status,
          modalidades: modalidades.length > 0 ? modalidades : undefined,
          valor_minimo: valorMin,
          valor_maximo: valorMax,
          esferas: esferas.length > 0 ? esferas : undefined,
          municipios: municipios.length > 0 ? municipios.map(m => m.codigo) : undefined,
          ordenacao,
        })
      });

      if (!response.ok) {
        const err = await response.json();

        // Handle authentication required (401) - redirect to login
        if (response.status === 401) {
          window.location.href = "/login";
          throw new Error("Faça login para continuar");
        }

        // Issue #153: Handle quota exceeded (403)
        if (response.status === 403) {
          setQuotaError(err.message || "Suas buscas acabaram.");
          throw new Error(err.message || "Quota excedida");
        }

        throw new Error(err.message || "Erro ao buscar licitações");
      }

      const data: BuscaResult = await response.json();
      setResult(data);
      setRawCount(data.total_raw || 0);

      // Issue #153: Refresh quota after successful search
      if (session?.access_token) {
        refreshQuota();
      }

      const searchEndTime = Date.now();
      const timeElapsed = searchEndTime - searchStartTime;

      // Track search_completed event
      trackEvent('search_completed', {
        time_elapsed_ms: timeElapsed,
        time_elapsed_readable: `${Math.floor(timeElapsed / 1000)}s`,
        total_raw: data.total_raw || 0,
        total_filtered: data.total_filtrado || 0,
        filter_ratio: data.total_raw > 0
          ? ((data.total_filtrado / data.total_raw) * 100).toFixed(1) + '%'
          : '0%',
        valor_total: data.resumo?.valor_total || 0,
        has_summary: !!data.resumo?.resumo_executivo,
        ufs: Array.from(ufsSelecionadas),
        uf_count: ufsSelecionadas.size,
        search_mode: searchMode,
      });

    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : "Erro desconhecido";
      setError(errorMessage);

      // Track search_failed event
      trackEvent('search_failed', {
        error_message: errorMessage,
        error_type: e instanceof Error ? e.constructor.name : 'unknown',
        time_elapsed_ms: Date.now() - searchStartTime,
        ufs: Array.from(ufsSelecionadas),
        uf_count: ufsSelecionadas.size,
        search_mode: searchMode,
      });
    } finally {
      cleanupInterval(); // BUG FIX: Always cleanup interval to prevent memory leaks
      setLoading(false);
      setLoadingStep(1);
      setStatesProcessed(0); // Issue #109: Reset progress counter
    }
  };

  const handleDownload = async () => {
    if (!result?.download_id) return;
    setDownloadError(null);
    setDownloadLoading(true);

    const downloadStartTime = Date.now();

    // Track download_started event
    trackEvent('download_started', {
      download_id: result.download_id,
      total_filtered: result.total_filtrado || 0,
      valor_total: result.resumo?.valor_total || 0,
      search_mode: searchMode,
      ufs: Array.from(ufsSelecionadas),
      uf_count: ufsSelecionadas.size,
    });

    try {
      const downloadUrl = `/api/download?id=${result.download_id}`;

      // Include auth header for authenticated downloads
      const downloadHeaders: Record<string, string> = {};
      if (session?.access_token) {
        downloadHeaders["Authorization"] = `Bearer ${session.access_token}`;
      }

      const response = await fetch(downloadUrl, { headers: downloadHeaders });

      if (!response.ok) {
        if (response.status === 401) {
          window.location.href = "/login";
          throw new Error('Faça login para continuar');
        }
        if (response.status === 404) {
          throw new Error('Arquivo expirado. Faça uma nova busca para gerar o Excel.');
        }
        throw new Error('Não foi possível baixar o arquivo. Tente novamente.');
      }

      const blob = await response.blob();
      const setorLabel = sectorName.replace(/\s+/g, '_');
      const appNameSlug = APP_NAME.replace(/\s+/g, '_');
      const filename = `${appNameSlug}_${setorLabel}_${dataInicial}_a_${dataFinal}.xlsx`;

      // Feature detection: check if browser supports download attribute
      const anchor = document.createElement('a');
      const supportsDownload = 'download' in anchor;

      if (supportsDownload) {
        // Modern browsers: Use Blob URL with download attribute (best UX)
        const url = URL.createObjectURL(blob);
        anchor.href = url;
        anchor.download = filename;

        // Trigger download without visible DOM manipulation (cleaner UX)
        anchor.style.display = 'none';
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);

        // Clean up Blob URL after download starts
        setTimeout(() => URL.revokeObjectURL(url), 100);
      } else {
        // Fallback for older browsers and iOS Safari
        // Use window.open() approach for better mobile compatibility
        const url = URL.createObjectURL(blob);
        const newWindow = window.open(url, '_blank');

        if (!newWindow) {
          // If popup blocked, try location approach as last resort
          window.location.href = url;
        }

        // Clean up Blob URL after a delay
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }

      const downloadEndTime = Date.now();
      const timeElapsed = downloadEndTime - downloadStartTime;

      // Track download_completed event
      trackEvent('download_completed', {
        download_id: result.download_id,
        time_elapsed_ms: timeElapsed,
        time_elapsed_readable: `${Math.floor(timeElapsed / 1000)}s`,
        file_size_bytes: blob.size,
        file_size_readable: `${(blob.size / 1024).toFixed(2)} KB`,
        filename: filename,
        total_filtered: result.total_filtrado || 0,
        valor_total: result.resumo?.valor_total || 0,
        download_method: supportsDownload ? 'blob_download_attribute' : 'window_open_fallback',
        browser_supports_download: supportsDownload,
      });
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Não foi possível baixar o arquivo.';
      setDownloadError(errorMessage);

      // Track download_failed event
      trackEvent('download_failed', {
        download_id: result.download_id,
        error_message: errorMessage,
        error_type: e instanceof Error ? e.constructor.name : 'unknown',
        time_elapsed_ms: Date.now() - downloadStartTime,
        total_filtered: result.total_filtrado || 0,
      });
    } finally {
      setDownloadLoading(false);
    }
  };

  const handleSaveSearch = () => {
    if (!result) return;

    const defaultName = searchMode === "setor"
      ? (setores.find(s => s.id === setorId)?.name || "Busca personalizada")
      : termosArray.length > 0
        ? `Busca: "${termosArray.join(', ')}"`
        : "Busca personalizada";

    setSaveSearchName(defaultName);
    setSaveError(null);
    setShowSaveDialog(true);
  };

  const confirmSaveSearch = () => {
    try {
      saveNewSearch(saveSearchName || "Busca sem nome", {
        ufs: Array.from(ufsSelecionadas),
        dataInicial,
        dataFinal,
        searchMode,
        setorId: searchMode === "setor" ? setorId : undefined,
        termosBusca: searchMode === "termos" ? termosArray.join(" ") : undefined,
      });

      // Track analytics
      trackEvent('saved_search_created', {
        search_name: saveSearchName,
        search_mode: searchMode,
        ufs: Array.from(ufsSelecionadas),
        uf_count: ufsSelecionadas.size,
        setor_id: searchMode === "setor" ? setorId : null,
        termos_count: termosArray.length,
      });

      setShowSaveDialog(false);
      setSaveSearchName("");
      setSaveError(null);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Erro ao salvar busca");
    }
  };

  const handleLoadSearch = (search: SavedSearch) => {
    // Load search parameters into form
    setUfsSelecionadas(new Set(search.searchParams.ufs));
    setDataInicial(search.searchParams.dataInicial);
    setDataFinal(search.searchParams.dataFinal);
    setSearchMode(search.searchParams.searchMode);

    if (search.searchParams.searchMode === "setor" && search.searchParams.setorId) {
      setSetorId(search.searchParams.setorId);
    } else if (search.searchParams.searchMode === "termos" && search.searchParams.termosBusca) {
      setTermosArray(search.searchParams.termosBusca.split(" "));
    }

    // Clear current result to show updated form
    setResult(null);
  };

  // Pull-to-refresh handler (Issue #119)
  const handleRefresh = async (): Promise<void> => {
    if (!lastSearchParamsRef.current) {
      // No previous search to refresh
      return Promise.resolve();
    }

    const params = lastSearchParamsRef.current;

    // Restore search params if they were changed
    setUfsSelecionadas(new Set(params.ufs));
    setDataInicial(params.dataInicial);
    setDataFinal(params.dataFinal);
    setSearchMode(params.searchMode);

    if (params.searchMode === "setor" && params.setorId) {
      setSetorId(params.setorId);
    } else if (params.searchMode === "termos" && params.termosArray) {
      setTermosArray(params.termosArray);
    }

    // Restore new filter params
    setStatus(params.status);
    setModalidades(params.modalidades);
    setValorMin(params.valorMin);
    setValorMax(params.valorMax);
    setEsferas(params.esferas);
    setMunicipios(params.municipios);
    setOrdenacao(params.ordenacao);

    // Track pull-to-refresh event
    trackEvent('pull_to_refresh_triggered', {
      search_mode: params.searchMode,
      ufs: Array.from(params.ufs),
      uf_count: params.ufs.size,
    });

    // Execute search
    await buscar();
  };

  const isFormValid = Object.keys(validationErrors).length === 0;

  // Note: Authentication is handled by middleware.ts
  // If we reach this point, user is already authenticated (middleware validated session)
  // Show loading only during initial hydration
  // IMPORTANT: This check MUST come AFTER all hooks are called to comply with React's Rules of Hooks
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
      {/* Navigation Header */}
      <header className="border-b border-strong bg-[var(--surface-0)] sticky top-0 z-50 backdrop-blur-sm supports-[backdrop-filter]:bg-[var(--surface-0)]/95">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
          <div className="flex items-center gap-4">
            <Image
              src={LOGO_URL}
              alt={APP_NAME}
              width={140}
              height={67}
              className="h-10 w-auto"
              priority
            />
            <span className="hidden sm:block text-sm text-ink-muted font-medium border-l border-strong pl-4">
              Busca inteligente de licitações
            </span>
          </div>
          <div className="flex items-center gap-4">

            {/* Issue #153: Show quota badge */}
            <QuotaBadge />

            {/* STORY-165: Plan badge with upgrade modal */}
            {planInfo && (
              <PlanBadge
                planId={planInfo.plan_id}
                planName={planInfo.plan_name}
                trialExpiresAt={planInfo.trial_expires_at ?? undefined}
                onClick={() => {
                  setPreSelectedPlan(undefined);
                  setUpgradeSource("plan_badge");
                  setShowUpgradeModal(true);
                }}
              />
            )}

            {/* Re-trigger Onboarding Button */}
            {!shouldShowOnboarding && (
              <button
                onClick={restartTour}
                className="text-xs text-ink-muted hover:text-brand-blue transition-colors"
                title="Ver tutorial novamente"
                aria-label="Ver tutorial novamente"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            )}

            <SavedSearchesDropdown
              onLoadSearch={handleLoadSearch}
              onAnalyticsEvent={trackEvent}
            />
            <ThemeToggle />
            <UserMenu />
          </div>
        </div>
      </header>

      <main id="main-content" className="max-w-4xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        <PullToRefresh
          onRefresh={handleRefresh}
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
            {/* Page Title */}
            <div className="mb-8 animate-fade-in-up">
              <h1 className="text-2xl sm:text-3xl font-bold font-display text-ink">
                Busca de Licitações
              </h1>
              <p className="text-ink-secondary mt-1 text-sm sm:text-base">
                Encontre oportunidades de contratação pública no Portal Nacional (PNCP)
              </p>
            </div>

        {/* Search Mode Toggle */}
        <section className="mb-6 animate-fade-in-up stagger-1 relative z-30">
          <label className="block text-base font-semibold text-ink mb-3">
            Buscar por:
          </label>
          <div className="flex rounded-button border border-strong overflow-hidden mb-4">
            <button
              type="button"
              onClick={() => { setSearchMode("setor"); setResult(null); }}
              className={`flex-1 py-2.5 text-sm sm:text-base font-medium transition-all duration-200 ${
                searchMode === "setor"
                  ? "bg-brand-navy text-white"
                  : "bg-surface-0 text-ink-secondary hover:bg-surface-1"
              }`}
            >
              Setor
            </button>
            <button
              type="button"
              onClick={() => { setSearchMode("termos"); setResult(null); }}
              className={`flex-1 py-2.5 text-sm sm:text-base font-medium transition-all duration-200 ${
                searchMode === "termos"
                  ? "bg-brand-navy text-white"
                  : "bg-surface-0 text-ink-secondary hover:bg-surface-1"
              }`}
            >
              Termos Específicos
            </button>
          </div>

          {/* Sector Selector - Issue #89: Custom Select Component */}
          {searchMode === "setor" && (
            <div className="relative z-20">
              <CustomSelect
                id="setor"
                value={setorId}
                options={setores.map(s => ({ value: s.id, label: s.name, description: s.description }))}
                onChange={(value) => { setSetorId(value); setResult(null); }}
                placeholder="Selecione um setor"
              />
            </div>
          )}

          {/* Custom Terms Input with Tags */}
          {searchMode === "termos" && (
            <div>
              <div className="border border-strong rounded-input bg-surface-0 px-3 py-2 flex flex-wrap gap-2 items-center
                              focus-within:ring-2 focus-within:ring-brand-blue focus-within:border-brand-blue
                              transition-colors min-h-[48px]">
                {termosArray.map((termo, i) => (
                  <span
                    key={`${termo}-${i}`}
                    className="inline-flex items-center gap-1 bg-brand-blue-subtle text-brand-navy
                               px-2.5 py-1 rounded-full text-sm font-medium border border-brand-blue/20
                               animate-fade-in-up"
                  >
                    {termo}
                    <button
                      type="button"
                      onClick={() => {
                        setTermosArray(prev => prev.filter((_, idx) => idx !== i));
                        setResult(null);
                      }}
                      className="ml-0.5 hover:text-error transition-colors"
                      aria-label={`Remover termo ${termo}`}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </span>
                ))}
                <input
                  id="termos-busca"
                  type="text"
                  value={termoInput}
                  onChange={e => {
                    const val = e.target.value;
                    // When user types a space, commit the word as a tag
                    if (val.endsWith(" ")) {
                      const word = val.trim().toLowerCase();
                      if (word && isStopword(word)) {
                        // Skip stopwords silently
                        setTermoInput("");
                        return;
                      }
                      if (word && !termosArray.includes(word)) {
                        setTermosArray(prev => [...prev, word]);
                        setResult(null);
                      }
                      setTermoInput("");
                    } else {
                      setTermoInput(val);
                    }
                  }}
                  onKeyDown={e => {
                    // Backspace on empty input removes last tag
                    if (e.key === "Backspace" && termoInput === "" && termosArray.length > 0) {
                      setTermosArray(prev => prev.slice(0, -1));
                      setResult(null);
                    }
                    // Enter also commits the current word
                    if (e.key === "Enter") {
                      e.preventDefault();
                      const word = termoInput.trim().toLowerCase();
                      if (word && isStopword(word)) {
                        setTermoInput("");
                        return;
                      }
                      if (word && !termosArray.includes(word)) {
                        setTermosArray(prev => [...prev, word]);
                        setResult(null);
                      }
                      setTermoInput("");
                    }
                  }}
                  placeholder={termosArray.length === 0 ? "Digite um termo e pressione espaço..." : "Adicionar mais..."}
                  className="flex-1 min-w-[120px] outline-none bg-transparent text-base text-ink
                             placeholder:text-ink-faint py-1"
                />
              </div>
              <p className="text-sm text-ink-muted mt-1.5">
                Digite cada termo e pressione <kbd className="px-1.5 py-0.5 bg-surface-2 rounded text-xs font-mono border">espaço</kbd> para confirmar. Artigos e preposições (de, para, com...) são ignorados automaticamente.
                {termosArray.length > 0 && (
                  <span className="text-brand-blue font-medium">
                    {" "}{termosArray.length} termo{termosArray.length > 1 ? "s" : ""} selecionado{termosArray.length > 1 ? "s" : ""}
                  </span>
                )}
              </p>
            </div>
          )}
        </section>

        {/* UF Selection Section */}
        <section className="mb-6 animate-fade-in-up stagger-2 relative z-10">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 mb-3">
            <label className="text-base sm:text-lg font-semibold text-ink">
              Estados (UFs):
            </label>
            <div className="flex gap-3">
              <button
                onClick={selecionarTodos}
                className="text-sm sm:text-base font-medium text-brand-blue hover:text-brand-blue-hover hover:underline transition-colors"
                type="button"
              >
                Selecionar todos
              </button>
              <button
                onClick={limparSelecao}
                className="text-sm sm:text-base font-medium text-ink-muted hover:text-ink transition-colors"
                type="button"
              >
                Limpar
              </button>
            </div>
          </div>

          {/* Region quick-select */}
          <RegionSelector selected={ufsSelecionadas} onToggleRegion={toggleRegion} />

          {/* UF Grid - Improved mobile: 4 cols on xs, 5 on sm, 7 on md, 9 on lg */}
          <div className="grid grid-cols-4 xs:grid-cols-5 sm:grid-cols-7 md:grid-cols-9 gap-1.5 sm:gap-2">
            {UFS.map(uf => (
              <button
                key={uf}
                onClick={() => toggleUf(uf)}
                type="button"
                title={UF_NAMES[uf]}
                aria-pressed={ufsSelecionadas.has(uf)}
                className={`px-1.5 py-2.5 sm:px-4 sm:py-2 rounded-button border text-xs sm:text-base font-medium transition-all duration-200 min-h-[44px] ${
                  ufsSelecionadas.has(uf)
                    ? "bg-brand-navy text-white border-brand-navy hover:bg-brand-blue-hover"
                    : "bg-surface-0 text-ink-secondary border hover:border-accent hover:text-brand-blue hover:bg-brand-blue-subtle"
                }`}
              >
                {uf}
              </button>
            ))}
          </div>

          <p className="text-sm sm:text-base text-ink-muted mt-2">
            {ufsSelecionadas.size === 1 ? '1 estado selecionado' : `${ufsSelecionadas.size} estados selecionados`}
          </p>

          {validationErrors.ufs && (
            <p className="text-sm sm:text-base text-error mt-2 font-medium" role="alert">
              {validationErrors.ufs}
            </p>
          )}
        </section>

        {/* Date Range Section - Issue #89: Custom Date Inputs */}
        <section className="mb-6 animate-fade-in-up stagger-3 relative z-0">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <CustomDateInput
              id="data-inicial"
              value={dataInicial}
              onChange={(value) => { setDataInicial(value); setResult(null); }}
              label="Data inicial:"
            />
            <CustomDateInput
              id="data-final"
              value={dataFinal}
              onChange={(value) => { setDataFinal(value); setResult(null); }}
              label="Data final:"
            />
          </div>

          {validationErrors.date_range && (
            <p className="text-sm sm:text-base text-error mt-3 font-medium" role="alert">
              {validationErrors.date_range}
            </p>
          )}

          {/* STORY-165: Date range validation warning */}
          {planInfo && dataInicial && dataFinal && (() => {
            const days = dateDiffInDays(dataInicial, dataFinal);
            const maxDays = planInfo.capabilities.max_history_days;
            if (days > maxDays) {
              return (
                <div className="mt-3 p-4 bg-warning-subtle border border-warning/20 rounded-card" role="alert">
                  <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-warning mb-1">
                        Período muito longo para seu plano
                      </p>
                      <p className="text-sm text-ink-secondary">
                        Seu plano {planInfo.plan_name} permite buscas de até {maxDays} dias.
                        Você selecionou {days} dias. Ajuste as datas ou faça upgrade.
                      </p>
                      <button
                        onClick={() => {
                          const suggestedPlan = maxDays < 30 ? "consultor_agil" : maxDays < 365 ? "maquina" : "sala_guerra";
                          setPreSelectedPlan(suggestedPlan as any);
                          setUpgradeSource("date_range");
                          setShowUpgradeModal(true);
                        }}
                        className="mt-2 text-sm font-medium text-brand-blue hover:underline"
                      >
                        Ver planos →
                      </button>
                    </div>
                  </div>
                </div>
              );
            }
            return null;
          })()}
        </section>

        {/* P1 Filters: Esfera and Municipio (Location Section) */}
        <section className="mb-6 animate-fade-in-up stagger-3 relative z-0">
          <h3 className="text-base font-semibold text-ink mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-ink-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Filtragem por Localizacao
          </h3>
          <div className="space-y-6 p-4 bg-surface-1 rounded-card border border-strong">
            <EsferaFilter
              value={esferas}
              onChange={(newEsferas) => { setEsferas(newEsferas); setResult(null); }}
              disabled={loading}
            />
            <MunicipioFilter
              ufs={Array.from(ufsSelecionadas)}
              value={municipios}
              onChange={(newMunicipios) => { setMunicipios(newMunicipios); setResult(null); }}
              disabled={loading}
            />
          </div>
        </section>

        {/* P0 Filters: Status, Modalidade, Valor (Advanced Filters Section) */}
        <section className="mb-6 animate-fade-in-up stagger-4 relative z-0">
          <h3 className="text-base font-semibold text-ink mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-ink-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filtros Avancados
          </h3>
          <div className="space-y-6 p-4 bg-surface-1 rounded-card border border-strong">
            <StatusFilter
              value={status}
              onChange={(newStatus) => { setStatus(newStatus); setResult(null); }}
              disabled={loading}
            />
            <ModalidadeFilter
              value={modalidades}
              onChange={(newModalidades) => { setModalidades(newModalidades); setResult(null); }}
              disabled={loading}
            />
            <ValorFilter
              valorMin={valorMin}
              valorMax={valorMax}
              onChange={(min, max) => { setValorMin(min); setValorMax(max); setResult(null); }}
              disabled={loading}
            />
          </div>
        </section>

        {/* Search Buttons */}
        <div className="space-y-3">
          <button
            ref={searchButtonRef}
            onClick={buscar}
            disabled={loading || !canSearch}
            type="button"
            aria-busy={loading}
            className="w-full bg-brand-navy text-white py-3.5 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                       hover:bg-brand-blue-hover active:bg-brand-blue
                       disabled:bg-ink-faint disabled:text-ink-muted disabled:cursor-not-allowed
                       transition-all duration-200 min-h-[48px] sm:min-h-[52px]"
          >
            {loading ? "Buscando..." : `Buscar ${searchLabel}`}
          </button>

          {/* Save Search Button - Only show if there's a result */}
          {result && result.resumo.total_oportunidades > 0 && (
            <button
              onClick={handleSaveSearch}
              disabled={isMaxCapacity}
              type="button"
              className="w-full bg-surface-0 text-brand-navy py-2.5 sm:py-3 rounded-button text-sm sm:text-base font-medium
                         border border-brand-navy hover:bg-brand-blue-subtle
                         disabled:bg-surface-0 disabled:text-ink-muted disabled:border-ink-faint disabled:cursor-not-allowed
                         transition-all duration-200 flex items-center justify-center gap-2"
              title={isMaxCapacity ? "Máximo de 10 buscas salvas atingido" : "Salvar esta busca"}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
              </svg>
              {isMaxCapacity ? "Limite de buscas atingido" : "Salvar Busca"}
            </button>
          )}
        </div>

        {/* Loading State - Enhanced with 5-stage progress (Feature #2) + Skeleton (Issue #111) + Progress feedback (Issue #109) */}
        {loading && (
          <div aria-live="polite">
            <EnhancedLoadingProgress
              currentStep={loadingStep}
              estimatedTime={Math.max(30, ufsSelecionadas.size * 6)}
              stateCount={ufsSelecionadas.size}
              statesProcessed={statesProcessed}
              onStageChange={(stage) => {
                // Track stage changes for analytics
                trackEvent('search_progress_stage', {
                  stage: stage,
                  ufs: Array.from(ufsSelecionadas),
                  uf_count: ufsSelecionadas.size,
                });
              }}
            />
            {/* Show skeleton after initial connection phase (Issue #111) */}
            <LoadingResultsSkeleton count={1} />
          </div>
        )}

        {/* Error Display with Retry */}
        {error && !quotaError && (
          <div className="mt-6 sm:mt-8 p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-card animate-fade-in-up" role="alert">
            <p className="text-sm sm:text-base font-medium text-error mb-3">{error}</p>
            <button
              onClick={buscar}
              disabled={loading}
              className="px-4 py-2 bg-error text-white rounded-button text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              Tentar novamente
            </button>
          </div>
        )}

        {/* Issue #153: Quota Exceeded Display */}
        {quotaError && (
          <div className="mt-6 sm:mt-8 p-4 sm:p-5 bg-warning-subtle border border-warning/20 rounded-card animate-fade-in-up" role="alert">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-warning flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <p className="text-sm sm:text-base font-medium text-warning mb-2">{quotaError}</p>
                <p className="text-sm text-ink-secondary mb-4">
                  Escolha um plano para continuar buscando oportunidades de licitacao.
                </p>
                <a
                  href="/planos"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white rounded-button text-sm font-medium
                             hover:bg-brand-blue-hover transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                  </svg>
                  Ver Planos
                </a>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {result && result.resumo.total_oportunidades === 0 && (
          <EmptyState
            onAdjustSearch={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            rawCount={rawCount}
            stateCount={ufsSelecionadas.size}
            filterStats={result.filter_stats}
            sectorName={sectorName}
          />
        )}

        {/* Result Display */}
        {result && result.resumo.total_oportunidades > 0 && (
          <div className="mt-6 sm:mt-8 space-y-4 sm:space-y-6 animate-fade-in-up">
            {/* Results header with ordering */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-strong">
              <h2 className="text-lg font-semibold text-ink">
                Resultados da Busca
              </h2>
              <OrdenacaoSelect
                value={ordenacao}
                onChange={(newOrdenacao) => { setOrdenacao(newOrdenacao); }}
                disabled={loading}
              />
            </div>

            {/* Stopword / terms transparency banner */}
            {(result.termos_utilizados || result.stopwords_removidas) && (
              <div className="px-4 py-3 bg-surface-2 border border-border rounded-card text-sm text-ink-secondary">
                {result.termos_utilizados && result.termos_utilizados.length > 0 && (
                  <span>
                    Termos utilizados na busca:{" "}
                    {result.termos_utilizados.map(t => (
                      <span key={t} className="inline-block px-2 py-0.5 mr-1 bg-brand-blue-subtle text-brand-navy dark:text-brand-blue rounded font-medium text-xs">
                        {t}
                      </span>
                    ))}
                  </span>
                )}
                {result.stopwords_removidas && result.stopwords_removidas.length > 0 && (
                  <span className="ml-2 text-ink-faint">
                    (ignorados: {result.stopwords_removidas.join(", ")})
                  </span>
                )}
              </div>
            )}

            {/* Summary Card */}
            <div className="p-4 sm:p-6 bg-brand-blue-subtle border border-accent rounded-card">
              <p className="text-base sm:text-lg leading-relaxed text-ink">
                {result.resumo.resumo_executivo}
              </p>

              <div className="flex flex-col sm:flex-row flex-wrap gap-4 sm:gap-8 mt-4 sm:mt-6">
                <div>
                  <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-brand-navy dark:text-brand-blue">
                    {result.resumo.total_oportunidades}
                  </span>
                  <span className="text-sm sm:text-base text-ink-secondary block mt-1">licitações</span>
                </div>
                <div>
                  <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-brand-navy dark:text-brand-blue">
                    R$ {result.resumo.valor_total.toLocaleString("pt-BR")}
                  </span>
                  <span className="text-sm sm:text-base text-ink-secondary block mt-1">valor total</span>
                </div>
              </div>

              {result.resumo.alerta_urgencia && (
                <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-warning-subtle border border-warning/20 rounded-card" role="alert">
                  <p className="text-sm sm:text-base font-medium text-warning">
                    <span aria-hidden="true">Atenção: </span>
                    {result.resumo.alerta_urgencia}
                  </p>
                </div>
              )}

              {result.resumo.destaques.length > 0 && (
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

            {/* STORY-165: Quota Counter */}
            {planInfo && (
              <QuotaCounter
                quotaUsed={planInfo.quota_used}
                quotaLimit={planInfo.capabilities.max_requests_per_month}
                resetDate={planInfo.quota_reset_date}
                planId={planInfo.plan_id}
                onUpgradeClick={() => {
                  setPreSelectedPlan(undefined);
                  setUpgradeSource("quota_counter");
                  setShowUpgradeModal(true);
                }}
              />
            )}

            {/* FREE tier preview: Show bid items with blur effect */}
            {result.licitacoes && result.licitacoes.length > 0 && (
              <LicitacoesPreview
                licitacoes={result.licitacoes}
                previewCount={5}
                excelAvailable={planInfo?.capabilities.allow_excel ?? false}
                onUpgradeClick={() => {
                  setPreSelectedPlan("maquina");
                  setUpgradeSource("licitacoes_preview");
                  setShowUpgradeModal(true);
                }}
              />
            )}

            {/* Download Button - STORY-165: Conditional based on plan */}
            {planInfo?.capabilities.allow_excel ? (
              <button
                onClick={handleDownload}
                disabled={downloadLoading}
                aria-label={`Baixar Excel com ${result.resumo.total_oportunidades} licitações`}
                className="w-full bg-brand-navy text-white py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                           hover:bg-brand-blue-hover active:bg-brand-blue
                           disabled:bg-ink-faint disabled:text-ink-muted disabled:cursor-not-allowed
                           transition-all duration-200
                           flex items-center justify-center gap-3"
              >
                {downloadLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-label="Carregando" role="img">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Preparando download...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Baixar Excel ({result.resumo.total_oportunidades} licitações)
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={() => {
                  setPreSelectedPlan("maquina");
                  setUpgradeSource("excel_button");
                  setShowUpgradeModal(true);
                }}
                className="w-full bg-surface-0 border-2 border-brand-navy text-brand-navy py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                           hover:bg-brand-blue-subtle transition-all duration-200
                           flex items-center justify-center gap-3"
                aria-label="Export Excel feature locked. Available on Máquina plan at R$ 597 per month. Click to view plans"
                title="Exportar Excel disponível no plano Máquina (R$ 597/mês)"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                🔒 Exportar Excel (Disponível no plano Máquina)
              </button>
            )}

            {/* Download Error */}
            {downloadError && (
              <div className="p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-card" role="alert">
                <p className="text-sm sm:text-base font-medium text-error">{downloadError}</p>
              </div>
            )}

            {/* Stats */}
            <div className="text-xs sm:text-sm text-ink-muted text-center">
              {rawCount > 0 && (
                <p>
                  Encontradas {result.resumo.total_oportunidades} de {rawCount.toLocaleString("pt-BR")} licitações
                  ({((result.resumo.total_oportunidades / rawCount) * 100).toFixed(1)}% do setor {sectorName.toLowerCase()})
                </p>
              )}
            </div>
          </div>
        )}
          </div>
        </PullToRefresh>
      </main>

      {/* Save Search Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in">
          <div className="bg-surface-0 rounded-card shadow-xl max-w-md w-full p-6 animate-fade-in-up">
            <h3 className="text-lg font-semibold text-ink mb-4">Salvar Busca</h3>

            <div className="mb-4">
              <label htmlFor="save-search-name" className="block text-sm font-medium text-ink-secondary mb-2">
                Nome da busca:
              </label>
              <input
                id="save-search-name"
                type="text"
                value={saveSearchName}
                onChange={(e) => setSaveSearchName(e.target.value)}
                placeholder="Ex: Uniformes Sul do Brasil"
                className="w-full border border-strong rounded-input px-4 py-2.5 text-base
                           bg-surface-0 text-ink
                           focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue
                           transition-colors"
                maxLength={50}
                autoFocus
              />
              <p className="text-xs text-ink-muted mt-1">
                {saveSearchName.length}/50 caracteres
              </p>
            </div>

            {saveError && (
              <div className="mb-4 p-3 bg-error-subtle border border-error/20 rounded text-sm text-error" role="alert">
                {saveError}
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowSaveDialog(false);
                  setSaveSearchName("");
                  setSaveError(null);
                }}
                type="button"
                className="px-4 py-2 text-sm font-medium text-ink-secondary hover:text-ink
                           hover:bg-surface-1 rounded-button transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={confirmSaveSearch}
                disabled={!saveSearchName.trim()}
                type="button"
                className="px-4 py-2 text-sm font-medium text-white bg-brand-navy
                           hover:bg-brand-blue-hover rounded-button transition-colors
                           disabled:bg-ink-faint disabled:cursor-not-allowed"
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Keyboard Shortcuts Help Dialog - Issue #122 */}
      {showKeyboardHelp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in">
          <div className="bg-surface-0 rounded-card shadow-xl max-w-lg w-full p-6 animate-fade-in-up">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-ink">Atalhos de Teclado</h3>
              <button
                onClick={() => setShowKeyboardHelp(false)}
                type="button"
                className="text-ink-muted hover:text-ink transition-colors"
                aria-label="Fechar ajuda de atalhos"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-strong">
                <span className="text-ink">Executar busca</span>
                <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">
                  {getShortcutDisplay({ key: 'k', ctrlKey: true, action: () => {}, description: '' })}
                </kbd>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-strong">
                <span className="text-ink">Selecionar todos os estados</span>
                <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">
                  {getShortcutDisplay({ key: 'a', ctrlKey: true, action: () => {}, description: '' })}
                </kbd>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-strong">
                <span className="text-ink">Limpar seleção</span>
                <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">
                  Esc
                </kbd>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-ink">Mostrar atalhos</span>
                <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">
                  /
                </kbd>
              </div>
            </div>

            <div className="mt-6 p-3 bg-brand-blue-subtle rounded border border-accent">
              <p className="text-sm text-ink-secondary">
                💡 Dica: Pressione <kbd className="px-1.5 py-0.5 bg-surface-0 rounded text-xs font-mono border border-strong">?</kbd> a qualquer momento para ver estes atalhos.
              </p>
            </div>

            <button
              onClick={() => setShowKeyboardHelp(false)}
              type="button"
              className="mt-4 w-full px-4 py-2 text-sm font-medium text-white bg-brand-navy
                         hover:bg-brand-blue-hover rounded-button transition-colors"
            >
              Entendi
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t mt-12 py-6 text-center text-xs text-ink-muted" role="contentinfo">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 flex items-center justify-between">
          <span>{APP_NAME} &mdash; Busca Inteligente de Licitações no PNCP</span>
          <button
            onClick={() => setShowKeyboardHelp(true)}
            className="text-xs text-ink-muted hover:text-brand-blue transition-colors flex items-center gap-1"
            title="Ver atalhos de teclado"
            aria-label="Ver atalhos de teclado"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            Atalhos
          </button>
        </div>
      </footer>

      {/* STORY-165: Upgrade Modal */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        preSelectedPlan={preSelectedPlan}
        source={upgradeSource}
      />
    </div>
  );
}

// Wrapper component with Suspense for useSearchParams (Next.js App Router requirement)
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
