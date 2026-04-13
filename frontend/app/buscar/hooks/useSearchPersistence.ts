"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import type { BuscaResult } from "../../types";
import type { SavedSearch } from "../../../lib/savedSearches";
import type { SearchFiltersSnapshot } from "./useSearch";
import { useSavedSearches } from "../../../hooks/useSavedSearches";
import { useAnalytics } from "../../../hooks/useAnalytics";
import { restoreSearchState } from "../../../lib/searchStatePersistence";
import {
  saveNavSearch,
  restoreNavSearch,
  clearNavSearch,
} from "../../../lib/navSearchCache";
import type { NavSearchMeta } from "../../../lib/navSearchCache";
import { toast } from "sonner";

interface UseSearchPersistenceFilters {
  searchMode: "setor" | "termos";
  sectorName: string;
  termosArray: string[];
  ufsSelecionadas: Set<string>;
  dataInicial: string;
  dataFinal: string;
  setorId: string;
  status: import("../components/StatusFilter").StatusLicitacao;
  modalidades: number[];
  valorMin: number | null;
  valorMax: number | null;
  esferas: import("../../components/EsferaFilter").Esfera[];
  municipios: import("../../components/MunicipioFilter").Municipio[];
  ordenacao: import("../../components/OrdenacaoSelect").OrdenacaoOption;
  // Setters
  setUfsSelecionadas: (ufs: Set<string>) => void;
  setDataInicial: (d: string) => void;
  setDataFinal: (d: string) => void;
  setSearchMode: (m: "setor" | "termos") => void;
  setSetorId: (id: string) => void;
  setTermosArray: (t: string[]) => void;
  setStatus: (s: import("../components/StatusFilter").StatusLicitacao) => void;
  setModalidades: (m: number[]) => void;
  setValorMin: (v: number | null) => void;
  setValorMax: (v: number | null) => void;
  setEsferas: (e: import("../../components/EsferaFilter").Esfera[]) => void;
  setMunicipios: (m: import("../../components/MunicipioFilter").Municipio[]) => void;
}

interface UseSearchPersistenceParams {
  filters: UseSearchPersistenceFilters;
  result: BuscaResult | null;
  setResult: (r: BuscaResult | null) => void;
  buscar: (options?: { forceFresh?: boolean }) => Promise<void>;
}

export interface UseSearchPersistenceReturn {
  showSaveDialog: boolean;
  setShowSaveDialog: (show: boolean) => void;
  saveSearchName: string;
  setSaveSearchName: (name: string) => void;
  saveError: string | null;
  isMaxCapacity: boolean;
  showingPartialResults: boolean;
  setShowingPartialResults: (v: boolean) => void;
  lastSearchParamsRef: React.MutableRefObject<SearchFiltersSnapshot | null>;
  handleSaveSearch: () => void;
  confirmSaveSearch: () => void;
  handleLoadSearch: (search: SavedSearch) => void;
  handleRefresh: () => Promise<void>;
  restoreSearchStateOnMount: () => void;
  dismissPartialResults: () => void;
  buscarForceFresh: () => Promise<void>;
  // UX-432: Navigation persistence
  isRestoredFromNav: boolean;
  restoredNavMeta: NavSearchMeta | null;
  handleNovaBusca: () => void;
}

export function useSearchPersistence(params: UseSearchPersistenceParams): UseSearchPersistenceReturn {
  const { filters, result, setResult, buscar } = params;
  const { trackEvent } = useAnalytics();
  const { saveNewSearch, isMaxCapacity } = useSavedSearches();

  // Save search
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveSearchName, setSaveSearchName] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);

  // STAB-006 AC3: Partial results recovery from localStorage
  const [showingPartialResults, setShowingPartialResults] = useState(false);

  // UX-432: Navigation cache state
  const [isRestoredFromNav, setIsRestoredFromNav] = useState(false);
  const [restoredNavMeta, setRestoredNavMeta] = useState<NavSearchMeta | null>(null);

  const lastSearchParamsRef = useRef<SearchFiltersSnapshot | null>(null);

  // UX-432 AC1: Auto-save results to nav cache whenever result changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!result) return;
    const formState = {
      ufs: Array.from(filters.ufsSelecionadas),
      startDate: filters.dataInicial,
      endDate: filters.dataFinal,
      setor: filters.searchMode === 'setor' ? filters.setorId : undefined,
      includeKeywords: filters.searchMode === 'termos' ? filters.termosArray : undefined,
      municipios: filters.municipios.map((m) => m.codigoIBGE ?? m.nome),
    };
    const ufsLabel = Array.from(filters.ufsSelecionadas).join(', ');
    const meta: NavSearchMeta = {
      sectorName: filters.searchMode === 'setor' ? (filters.sectorName || '') : (filters.termosArray.join(', ') || ''),
      ufsLabel,
    };
    saveNavSearch(result, formState, meta);
  }, [result]); // intentionally only re-runs when result changes; filters captured via closure

  const handleSaveSearch = useCallback(() => {
    if (!result) return;
    const defaultName = filters.searchMode === "setor"
      ? (filters.sectorName || "Análise personalizada")
      : filters.termosArray.length > 0
        ? `Análise: "${filters.termosArray.join(', ')}"`
        : "Análise personalizada";
    setSaveSearchName(defaultName);
    setSaveError(null);
    setShowSaveDialog(true);
  }, [result, filters.searchMode, filters.sectorName, filters.termosArray]);

  const confirmSaveSearch = useCallback(() => {
    try {
      saveNewSearch(saveSearchName || "Análise sem nome", {
        ufs: Array.from(filters.ufsSelecionadas),
        dataInicial: filters.dataInicial,
        dataFinal: filters.dataFinal,
        searchMode: filters.searchMode,
        setorId: filters.searchMode === "setor" ? filters.setorId : undefined,
        termosBusca: filters.searchMode === "termos" ? filters.termosArray.join(", ") : undefined,
      });
      trackEvent('saved_search_created', { search_name: saveSearchName, search_mode: filters.searchMode });
      toast.success(`Análise "${saveSearchName || "Análise sem nome"}" salva com sucesso!`);
      setShowSaveDialog(false);
      setSaveSearchName("");
      setSaveError(null);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Erro ao salvar análise");
      toast.error(`Erro ao salvar: ${error instanceof Error ? error.message : "Erro desconhecido"}`);
    }
  }, [saveSearchName, filters, saveNewSearch, trackEvent]);

  const handleLoadSearch = useCallback((search: SavedSearch) => {
    filters.setUfsSelecionadas(new Set(search.searchParams.ufs));
    filters.setDataInicial(search.searchParams.dataInicial);
    filters.setDataFinal(search.searchParams.dataFinal);
    filters.setSearchMode(search.searchParams.searchMode);
    if (search.searchParams.searchMode === "setor" && search.searchParams.setorId) {
      filters.setSetorId(search.searchParams.setorId);
    } else if (search.searchParams.searchMode === "termos" && search.searchParams.termosBusca) {
      const savedTerms = search.searchParams.termosBusca;
      if (savedTerms.includes(",")) {
        filters.setTermosArray(savedTerms.split(",").map((t: string) => t.trim()).filter(Boolean));
      } else {
        filters.setTermosArray(savedTerms.split(" ").filter(Boolean));
      }
    }
    setResult(null);
  }, [filters, setResult]);

  const handleRefresh = useCallback(async (): Promise<void> => {
    if (!lastSearchParamsRef.current) return;
    const params = lastSearchParamsRef.current;
    filters.setUfsSelecionadas(new Set(params.ufs));
    filters.setDataInicial(params.dataInicial);
    filters.setDataFinal(params.dataFinal);
    filters.setSearchMode(params.searchMode);
    if (params.searchMode === "setor" && params.setorId) filters.setSetorId(params.setorId);
    else if (params.searchMode === "termos" && params.termosArray) filters.setTermosArray(params.termosArray);
    filters.setStatus(params.status);
    filters.setModalidades(params.modalidades);
    filters.setValorMin(params.valorMin);
    filters.setValorMax(params.valorMax);
    filters.setEsferas(params.esferas);
    filters.setMunicipios(params.municipios);
    trackEvent('pull_to_refresh_triggered', { search_mode: params.searchMode });
    await buscar();
  }, [filters, buscar, trackEvent]);

  const restoreSearchStateOnMount = useCallback(() => {
    // 1. Auth-flow cache (one-time use, for OAuth redirect recovery — existing behaviour)
    const restored = restoreSearchState();
    if (restored) {
      if (restored.result) setResult(restored.result as BuscaResult);
      const { formState } = restored;
      if (formState.ufs?.length) filters.setUfsSelecionadas(new Set(formState.ufs));
      if (formState.startDate) filters.setDataInicial(formState.startDate);
      if (formState.endDate) filters.setDataFinal(formState.endDate);
      if (formState.setor) { filters.setSearchMode('setor'); filters.setSetorId(formState.setor); }
      if (formState.includeKeywords?.length) { filters.setSearchMode('termos'); filters.setTermosArray(formState.includeKeywords); }
      toast.success('Resultados da análise restaurados! Voce pode fazer o download agora.');
      trackEvent('search_state_auto_restored', { download_id: restored.downloadId });
      return; // auth-flow cache takes priority — skip nav cache
    }

    // 2. UX-432 AC2: Nav cache — restore results when returning from another page
    const navEntry = restoreNavSearch();
    if (navEntry) {
      if (navEntry.result) setResult(navEntry.result as BuscaResult);
      const { formState, meta } = navEntry;
      if (formState.ufs?.length) filters.setUfsSelecionadas(new Set(formState.ufs));
      if (formState.startDate) filters.setDataInicial(formState.startDate);
      if (formState.endDate) filters.setDataFinal(formState.endDate);
      if (formState.setor) { filters.setSearchMode('setor'); filters.setSetorId(formState.setor); }
      if (formState.includeKeywords?.length) { filters.setSearchMode('termos'); filters.setTermosArray(formState.includeKeywords); }
      setIsRestoredFromNav(true);
      setRestoredNavMeta(meta);
      trackEvent('nav_search_state_restored', { sector: meta.sectorName });
    }
  }, [setResult, filters, trackEvent]);

  // UX-432 AC3: Dismiss banner and discard cached results — start fresh
  const handleNovaBusca = useCallback(() => {
    clearNavSearch();
    setIsRestoredFromNav(false);
    setRestoredNavMeta(null);
    setResult(null);
  }, [setResult]);

  const buscarForceFresh = useCallback(async () => buscar({ forceFresh: true }), [buscar]);

  /** STAB-006 AC3: Dismiss partial results banner */
  const dismissPartialResults = useCallback(() => {
    setShowingPartialResults(false);
  }, []);

  return {
    showSaveDialog,
    setShowSaveDialog,
    saveSearchName,
    setSaveSearchName,
    saveError,
    isMaxCapacity,
    showingPartialResults,
    setShowingPartialResults,
    lastSearchParamsRef,
    handleSaveSearch,
    confirmSaveSearch,
    handleLoadSearch,
    handleRefresh,
    restoreSearchStateOnMount,
    dismissPartialResults,
    buscarForceFresh,
    // UX-432
    isRestoredFromNav,
    restoredNavMeta,
    handleNovaBusca,
  };
}
