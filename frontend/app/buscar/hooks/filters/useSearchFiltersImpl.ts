"use client";

import { useCallback } from "react";
import type { ValidationErrors } from "../../../types";
import { UFS } from "../../../../lib/constants/uf-names";
import { useSearchSectorData } from "./useSearchSectorData";
import { useSearchFormState } from "./useSearchFormState";
import { useSearchValidation, type TermValidation } from "./useSearchValidation";
import { useSearchFilterPersistence } from "./useSearchFilterPersistence";
import type { StatusLicitacao } from "../../components/StatusFilter";
import type { Esfera } from "../../../components/EsferaFilter";
import type { Municipio } from "../../../components/MunicipioFilter";
import type { OrdenacaoOption } from "../../../components/OrdenacaoSelect";
import type { Setor } from "../../../types";

export type { TermValidation };
export { validateTermsClientSide } from "./useSearchValidation";
export { SETORES_FALLBACK } from "./sectorData";
export { DEFAULT_SEARCH_DAYS } from "./useSearchFormState";
export type { StatusLicitacao, Esfera, Municipio, OrdenacaoOption };

export interface SearchFiltersState {
  setores: Setor[];
  setoresLoading: boolean;
  setoresError: boolean;
  setoresUsingFallback: boolean;
  setoresUsingStaleCache: boolean;
  staleCacheAge: number | null;
  setoresRetryCount: number;
  setorId: string;
  setSetorId: (id: string) => void;
  fetchSetores: (attempt?: number) => Promise<void>;
  searchMode: "setor" | "termos";
  setSearchMode: (mode: "setor" | "termos") => void;
  modoBusca: "abertas" | "publicacao";
  setModoBusca: (mode: "abertas" | "publicacao") => void;
  termosArray: string[];
  setTermosArray: (terms: string[]) => void;
  termoInput: string;
  setTermoInput: (input: string) => void;
  termValidation: TermValidation | null;
  addTerms: (newTerms: string[]) => void;
  removeTerm: (term: string) => void;
  ufsSelecionadas: Set<string>;
  setUfsSelecionadas: (ufs: Set<string>) => void;
  toggleUf: (uf: string) => void;
  toggleRegion: (regionUfs: string[]) => void;
  selecionarTodos: () => void;
  limparSelecao: () => void;
  dataInicial: string;
  setDataInicial: (date: string) => void;
  dataFinal: string;
  setDataFinal: (date: string) => void;
  status: StatusLicitacao;
  setStatus: (status: StatusLicitacao) => void;
  modalidades: number[];
  setModalidades: (modalidades: number[]) => void;
  valorMin: number | null;
  setValorMin: (val: number | null) => void;
  valorMax: number | null;
  setValorMax: (val: number | null) => void;
  valorValid: boolean;
  setValorValid: (valid: boolean) => void;
  esferas: Esfera[];
  setEsferas: (esferas: Esfera[]) => void;
  municipios: Municipio[];
  setMunicipios: (municipios: Municipio[]) => void;
  ordenacao: OrdenacaoOption;
  setOrdenacao: (ord: OrdenacaoOption) => void;
  locationFiltersOpen: boolean;
  setLocationFiltersOpen: (open: boolean) => void;
  advancedFiltersOpen: boolean;
  setAdvancedFiltersOpen: (open: boolean) => void;
  validationErrors: ValidationErrors;
  canSearch: boolean;
  sectorName: string;
  searchLabel: string;
  dateLabel: string;
  isUsingDefaults: boolean;
  allUfsSelected: boolean;
  clearResult: () => void;
}

export function useSearchFilters(clearResult: () => void): SearchFiltersState {
  // ── Sector data ───────────────────────────────────────────────────────
  const sectorData = useSearchSectorData(clearResult);

  // ── Form state ────────────────────────────────────────────────────────
  const form = useSearchFormState(clearResult);

  // ── Validation ────────────────────────────────────────────────────────
  const validation = useSearchValidation({
    ufsSelecionadas: form.ufsSelecionadas,
    dataInicial: form.dataInicial,
    dataFinal: form.dataFinal,
    searchMode: form.searchMode,
    termosArray: form.termosArray,
    valorValid: form.valorValid,
  });

  // ── Persistence (URL params + profile context) ────────────────────────
  useSearchFilterPersistence({
    setUfsSelecionadas: form.setUfsSelecionadas,
    setDataInicial: form.setDataInicial,
    setDataFinal: form.setDataFinal,
    setSearchMode: form.setSearchMode,
    setSetorId: sectorData.setSetorId,
    setTermosArray: form.setTermosArray,
    setValorMin: form.setValorMin,
    setValorMax: form.setValorMax,
    setModalidades: form.setModalidades,
  });

  // ── UF helpers ────────────────────────────────────────────────────────
  const toggleUf = useCallback((uf: string) => {
    const newSet = new Set(form.ufsSelecionadas);
    if (newSet.has(uf)) newSet.delete(uf); else newSet.add(uf);
    form.setUfsSelecionadas(newSet);
    clearResult();
  }, [form.ufsSelecionadas, form.setUfsSelecionadas, clearResult]);

  const toggleRegion = useCallback((regionUfs: string[]) => {
    const allSelected = regionUfs.every(uf => form.ufsSelecionadas.has(uf));
    const newSet = new Set(form.ufsSelecionadas);
    if (allSelected) regionUfs.forEach(uf => newSet.delete(uf)); else regionUfs.forEach(uf => newSet.add(uf));
    form.setUfsSelecionadas(newSet);
    clearResult();
  }, [form.ufsSelecionadas, form.setUfsSelecionadas, clearResult]);

  const selecionarTodos = useCallback(() => { form.setUfsSelecionadas(new Set(UFS)); clearResult(); }, [form.setUfsSelecionadas, clearResult]);
  const limparSelecao = useCallback(() => { form.setUfsSelecionadas(new Set()); clearResult(); }, [form.setUfsSelecionadas, clearResult]);

  // ── Term helpers (addTerms/removeTerm update setTermosArray) ──────────
  const addTerms = useCallback((newTerms: string[]) => {
    const updated = validation.addTerms(newTerms, clearResult);
    form.setTermosArray(updated);
  }, [validation, form.setTermosArray, clearResult]);

  const removeTerm = useCallback((termToRemove: string) => {
    const updated = validation.removeTerm(termToRemove, clearResult);
    form.setTermosArray(updated);
  }, [validation, form.setTermosArray, clearResult]);

  // ── Computed values ───────────────────────────────────────────────────
  const sectorName = form.searchMode === "setor"
    ? (sectorData.setores.find((s: Setor) => s.id === sectorData.setorId)?.name || "Licitações")
    : "Licitações";

  const searchLabel = form.searchMode === "setor"
    ? sectorName
    : form.termosArray.length > 0 ? `"${form.termosArray.join('", "')}"` : "Licitações";

  const statusQualifier =
    form.status === "recebendo_proposta" ? "abertas para proposta"
    : form.status === "em_julgamento" ? "em fase de julgamento"
    : form.status === "encerrada" ? "encerradas" : "";

  const dateLabel = form.modoBusca === "abertas"
    ? `Mostrando licitações${statusQualifier ? ` ${statusQualifier}` : ""}`
    : "Período de publicação";

  const allUfsSelected = form.ufsSelecionadas.size === UFS.length;
  const isUsingDefaults = allUfsSelected && form.modalidades.length === 0;

  return {
    // Sector
    ...sectorData,
    setSetorId: (id: string) => { sectorData.setSetorId(id); clearResult(); },
    // Form state
    ...form,
    // Validation
    validationErrors: validation.validationErrors,
    termValidation: validation.termValidation,
    canSearch: validation.canSearch,
    // Term helpers (wired to setTermosArray)
    addTerms, removeTerm,
    // UF helpers
    toggleUf, toggleRegion, selecionarTodos, limparSelecao,
    // Computed
    sectorName, searchLabel, dateLabel, isUsingDefaults, allUfsSelected,
    clearResult,
  };
}
