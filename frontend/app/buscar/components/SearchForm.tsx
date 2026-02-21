"use client";

import Link from "next/link";
import type { BuscaResult, ValidationErrors, Setor } from "../../types";
import { RegionSelector } from "../../components/RegionSelector";
import { CustomSelect } from "../../components/CustomSelect";
import { CustomDateInput } from "../../components/CustomDateInput";
import { Tooltip } from "../../components/ui/Tooltip";
import type { TermValidation } from "../hooks/useSearchFilters";
import { DEFAULT_SEARCH_DAYS } from "../hooks/useSearchFilters";
import type { StatusLicitacao } from "../../../components/StatusFilter";
import type { Esfera } from "../../components/EsferaFilter";
import type { Municipio } from "../../components/MunicipioFilter";
import type { OrdenacaoOption } from "../../components/OrdenacaoSelect";
import FilterPanel from "./FilterPanel";
import { UFS, UF_NAMES } from "../../../lib/constants/uf-names";
import { dateDiffInDays } from "../../../lib/utils/dateDiffInDays";

export interface SearchFormProps {
  // Sectors
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

  // Search mode
  searchMode: "setor" | "termos";
  setSearchMode: (mode: "setor" | "termos") => void;

  // Search paradigm (STORY-240)
  modoBusca: "abertas" | "publicacao";
  dateLabel: string;

  // Terms
  termosArray: string[];
  termoInput: string;
  setTermoInput: (input: string) => void;
  termValidation: TermValidation | null;
  addTerms: (newTerms: string[]) => void;
  removeTerm: (term: string) => void;

  // UFs
  ufsSelecionadas: Set<string>;
  toggleUf: (uf: string) => void;
  toggleRegion: (regionUfs: string[]) => void;
  selecionarTodos: () => void;
  limparSelecao: () => void;

  // Dates
  dataInicial: string;
  setDataInicial: (date: string) => void;
  dataFinal: string;
  setDataFinal: (date: string) => void;

  // Validation
  validationErrors: ValidationErrors;
  canSearch: boolean;
  searchLabel: string;

  // Filters
  locationFiltersOpen: boolean;
  setLocationFiltersOpen: (open: boolean) => void;
  advancedFiltersOpen: boolean;
  setAdvancedFiltersOpen: (open: boolean) => void;
  esferas: Esfera[];
  setEsferas: (e: Esfera[]) => void;
  municipios: Municipio[];
  setMunicipios: (m: Municipio[]) => void;
  status: StatusLicitacao;
  setStatus: (s: StatusLicitacao) => void;
  modalidades: number[];
  setModalidades: (m: number[]) => void;
  valorMin: number | null;
  setValorMin: (v: number | null) => void;
  valorMax: number | null;
  setValorMax: (v: number | null) => void;
  setValorValid: (valid: boolean) => void;

  // Search execution
  loading: boolean;
  buscar: () => void;
  searchButtonRef: React.RefObject<HTMLButtonElement | null>;

  // Result (for save button visibility)
  result: BuscaResult | null;
  handleSaveSearch: () => void;
  isMaxCapacity: boolean;

  // Plan info (for date range warning)
  planInfo: { plan_name: string; capabilities: { max_history_days: number } } | null;
  onShowUpgradeModal: (plan?: string, source?: string) => void;

  // Clear result callback
  clearResult: () => void;

  // Customize accordion (AC6-AC8)
  customizeOpen: boolean;
  setCustomizeOpen: (open: boolean) => void;
}

export default function SearchForm({
  setores, setoresLoading, setoresError, setoresUsingFallback, setoresUsingStaleCache, staleCacheAge, setoresRetryCount,
  setorId, setSetorId, fetchSetores,
  searchMode, setSearchMode,
  modoBusca, dateLabel,
  termosArray, termoInput, setTermoInput, termValidation, addTerms, removeTerm,
  ufsSelecionadas, toggleUf, toggleRegion, selecionarTodos, limparSelecao,
  dataInicial, setDataInicial, dataFinal, setDataFinal,
  validationErrors, canSearch, searchLabel,
  locationFiltersOpen, setLocationFiltersOpen,
  advancedFiltersOpen, setAdvancedFiltersOpen,
  esferas, setEsferas, municipios, setMunicipios,
  status, setStatus, modalidades, setModalidades,
  valorMin, setValorMin, valorMax, setValorMax, setValorValid,
  loading, buscar, searchButtonRef,
  result, handleSaveSearch, isMaxCapacity,
  planInfo, onShowUpgradeModal, clearResult,
  customizeOpen, setCustomizeOpen,
}: SearchFormProps) {
  return (
    <>
      {/* AC3: Stale cache banner (blue/informative) */}
      {setoresUsingStaleCache && (
        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-card flex items-start gap-3 animate-fade-in-up" role="status">
          <svg className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Usando setores em cache
              {staleCacheAge != null && (
                <span className="font-normal"> (atualizado há {Math.round(staleCacheAge / 60000)} min)</span>
              )}
            </p>
            <p className="text-xs text-blue-600/70 dark:text-blue-400/70 mt-0.5">Atualizando em segundo plano...</p>
          </div>
        </div>
      )}

      {/* AC3: Hardcoded fallback banner (yellow/warning) — only when no cache at all */}
      {setoresUsingFallback && !setoresUsingStaleCache && (
        <div className="mb-4 p-3 bg-[var(--warning-subtle)] border border-[var(--warning)]/20 rounded-card flex items-start gap-3 animate-fade-in-up" role="alert">
          <svg className="w-5 h-5 text-[var(--warning)] flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-medium text-[var(--warning)]">Usando lista offline de setores</p>
            <p className="text-xs text-ink-secondary mt-0.5">Alguns setores novos podem não aparecer.</p>
          </div>
          <button
            onClick={() => fetchSetores(0)}
            className="text-xs font-medium text-brand-blue hover:underline flex-shrink-0"
            type="button"
          >
            Tentar atualizar
          </button>
        </div>
      )}

      {/* Search Mode Toggle */}
      <section className="mb-6 animate-fade-in-up stagger-1 relative z-30">
        <label className="block text-base font-semibold text-ink mb-3">
          Buscar por:
        </label>
        <div className="flex rounded-button border border-strong overflow-hidden mb-4">
          <button
            type="button"
            onClick={() => { setSearchMode("setor"); clearResult(); }}
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
            onClick={() => { setSearchMode("termos"); clearResult(); }}
            className={`flex-1 py-2.5 text-sm sm:text-base font-medium transition-all duration-200 ${
              searchMode === "termos"
                ? "bg-brand-navy text-white"
                : "bg-surface-0 text-ink-secondary hover:bg-surface-1"
            }`}
          >
            Termos Específicos
          </button>
        </div>

        {/* Sector Selector */}
        {searchMode === "setor" && (
          <div className="relative z-20">
            {setoresLoading ? (
              <div className="border border-strong rounded-input px-4 py-3 bg-surface-1 space-y-3">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-brand-blue"></div>
                  <div className="h-5 bg-surface-2 rounded w-48 animate-pulse"></div>
                </div>
                <div className="space-y-2">
                  <div className="h-4 bg-surface-2 rounded w-full animate-pulse"></div>
                  <div className="h-4 bg-surface-2 rounded w-3/4 animate-pulse"></div>
                  <div className="h-4 bg-surface-2 rounded w-5/6 animate-pulse"></div>
                </div>
              </div>
            ) : setoresError && !setoresUsingFallback ? (
              <div className="border border-error/20 rounded-input px-4 py-3 bg-error-subtle">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-error flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-error">Não foi possível carregar setores</p>
                    <p className="text-xs text-ink-secondary mt-0.5">
                      Tentativa {setoresRetryCount + 1} de 3
                    </p>
                  </div>
                  <button
                    onClick={() => fetchSetores(0)}
                    className="text-sm font-medium text-brand-blue hover:underline flex items-center gap-1 flex-shrink-0"
                    type="button"
                    aria-label="Tentar carregar setores novamente"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Tentar novamente
                  </button>
                </div>
              </div>
            ) : (
              <CustomSelect
                id="setor"
                value={setorId}
                options={setores.map(s => ({ value: s.id, label: s.name, description: s.description }))}
                onChange={(value) => { setSetorId(value); clearResult(); }}
                placeholder="Ex: Uniformes, TI, Engenharia, Facilities..."
              />
            )}
          </div>
        )}

        {/* Custom Terms Input with Tags */}
        {searchMode === "termos" && (
          <div>
            {termValidation && termValidation.ignored.length > 0 && (
              <div className="mb-4 border border-warning/30 bg-warning-subtle rounded-card p-4 animate-fade-in-up">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-semibold text-sm text-warning mb-2">
                      Atenção: {termValidation.ignored.length} termo{termValidation.ignored.length > 1 ? 's' : ''} não será{termValidation.ignored.length > 1 ? 'ão' : ''} utilizado{termValidation.ignored.length > 1 ? 's' : ''} na busca
                    </p>
                    <ul className="space-y-1.5 text-sm text-ink-secondary">
                      {termValidation.ignored.map(term => (
                        <li key={term} className="flex items-start gap-2">
                          <span className="text-warning font-medium">•</span>
                          <span>
                            <strong className="text-ink font-medium">&quot;{term}&quot;</strong>: {termValidation.reasons[term]}
                          </span>
                        </li>
                      ))}
                    </ul>
                    <p className="text-xs text-ink-muted mt-3">
                      Dica: Use termos com pelo menos 4 caracteres e evite palavras muito comuns como &quot;de&quot;, &quot;para&quot;, &quot;com&quot;.
                    </p>
                  </div>
                </div>
              </div>
            )}

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
                    onClick={() => removeTerm(termo)}
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
                  if (val.includes(",")) {
                    const segments = val.split(",");
                    const toCommit = segments.slice(0, -1);
                    const remaining = segments[segments.length - 1];
                    const validTerms = toCommit
                      .map(seg => seg.trim().toLowerCase())
                      .filter(term => term && !termosArray.includes(term));
                    if (validTerms.length > 0) {
                      addTerms(validTerms);
                    }
                    setTermoInput(remaining);
                  } else {
                    setTermoInput(val);
                  }
                }}
                onKeyDown={e => {
                  if (e.key === "Backspace" && termoInput === "" && termosArray.length > 0) {
                    removeTerm(termosArray[termosArray.length - 1]);
                  }
                  if (e.key === "Enter") {
                    e.preventDefault();
                    const term = termoInput.trim().toLowerCase();
                    if (term && !termosArray.includes(term)) {
                      addTerms([term]);
                    }
                    setTermoInput("");
                  }
                }}
                onPaste={e => {
                  const pasted = e.clipboardData.getData("text");
                  if (pasted.includes(",")) {
                    e.preventDefault();
                    const segments = pasted.split(",").map(s => s.trim().toLowerCase()).filter(Boolean);
                    const newTerms = segments.filter(t => !termosArray.includes(t));
                    if (newTerms.length > 0) {
                      addTerms(newTerms);
                    }
                    setTermoInput("");
                  }
                }}
                placeholder={termosArray.length === 0 ? "Ex: terraplenagem, drenagem, levantamento topográfico" : "Adicionar mais..."}
                className="flex-1 min-w-[120px] outline-none bg-transparent text-base text-ink
                           placeholder:text-ink-faint py-1"
              />
            </div>
            <p className="text-sm text-ink-muted mt-1.5">
              Dica: digite frases completas e separe com <kbd className="px-1.5 py-0.5 bg-surface-2 rounded text-xs font-mono border">vírgula</kbd> ou <kbd className="px-1.5 py-0.5 bg-surface-2 rounded text-xs font-mono border">Enter</kbd>. Ex: levantamento topográfico, pavimentação
              {termosArray.length > 0 && (
                <span className="text-brand-blue font-medium">
                  {" "}{termosArray.length} termo{termosArray.length > 1 ? "s" : ""} selecionado{termosArray.length > 1 ? "s" : ""}
                </span>
              )}
            </p>
          </div>
        )}
      </section>

      {/* Search Buttons - AC5: moved up, right after sector selection */}
      <div className="mb-6 space-y-3 sm:relative sticky bottom-4 sm:bottom-auto z-20 bg-[var(--canvas)] sm:bg-transparent pt-2 sm:pt-0 -mx-4 px-4 sm:mx-0 sm:px-0 pb-2 sm:pb-0 animate-fade-in-up stagger-2">
        <button
          ref={searchButtonRef}
          onClick={buscar}
          disabled={loading || !canSearch}
          type="button"
          aria-busy={loading}
          className="w-full bg-brand-navy text-white py-3.5 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                     hover:bg-brand-blue-hover active:bg-brand-blue
                     disabled:bg-ink-faint disabled:text-ink-muted disabled:cursor-not-allowed
                     transition-all duration-200 min-h-[48px] sm:min-h-[52px]
                     flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Consultando múltiplas fontes e aplicando filtros inteligentes...
            </>
          ) : searchMode === "termos" && termValidation ? (
            termValidation.valid.length === 0
              ? "Adicione termos válidos para buscar"
              : `Buscar ${termValidation.valid.length} termo${termValidation.valid.length > 1 ? 's' : ''}`
          ) : (
            `Buscar ${searchLabel}`
          )}
        </button>

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

      {/* AC6: Personalizar busca accordion - collapsed by default */}
      <section className="mb-6 animate-fade-in-up stagger-3">
        <button
          type="button"
          onClick={() => setCustomizeOpen(!customizeOpen)}
          aria-expanded={customizeOpen}
          className="w-full text-base font-semibold text-ink mb-2 flex items-center gap-2 hover:text-brand-blue transition-colors"
        >
          <svg className="w-5 h-5 text-ink-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          Personalizar busca
          <svg className={`w-4 h-4 ml-auto transition-transform ${customizeOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* AC8: Badge when collapsed */}
        {!customizeOpen && (
          <div className="flex items-center justify-center gap-2 text-sm text-ink-secondary py-2 animate-fade-in-up">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>
              Buscando em {ufsSelecionadas.size === 27 ? 'todo o Brasil' : `${ufsSelecionadas.size} estado${ufsSelecionadas.size !== 1 ? 's' : ''}`} • Licitações abertas
              {modalidades.length > 0 ? ` • ${modalidades.length} modalidade${modalidades.length !== 1 ? 's' : ''}` : ''}
            </span>
          </div>
        )}

        {customizeOpen && (
          <div className="space-y-6 animate-fade-in-up">
            {/* UF Selection Section - moved into accordion */}
            <div className="relative z-10">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 mb-3">
                <label className="text-base sm:text-lg font-semibold text-ink">
                  Estados (<Tooltip content="UF = Unidade Federativa (Estado brasileiro). Selecione os estados onde deseja buscar licitações.">UFs</Tooltip>):
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

              <RegionSelector selected={ufsSelecionadas} onToggleRegion={toggleRegion} />

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
            </div>

            {/* Date Range Section - moved into accordion */}
            <div className="relative z-0">
              {modoBusca === "abertas" ? (
                <div className="p-3 bg-brand-blue-subtle rounded-card border border-brand-blue/20">
                  <p className="text-sm font-medium text-brand-navy">
                    {dateLabel}
                  </p>
                  <p className="text-xs text-ink-secondary mt-1">
                    Buscando nos últimos {DEFAULT_SEARCH_DAYS} dias — somente licitações com prazo aberto
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <CustomDateInput
                    id="data-inicial"
                    value={dataInicial}
                    onChange={(value) => { setDataInicial(value); clearResult(); }}
                    label="Data inicial:"
                  />
                  <CustomDateInput
                    id="data-final"
                    value={dataFinal}
                    onChange={(value) => { setDataFinal(value); clearResult(); }}
                    label="Data final:"
                  />
                </div>
              )}

              {validationErrors.date_range && (
                <p className="text-sm sm:text-base text-error mt-3 font-medium" role="alert">
                  {validationErrors.date_range}
                </p>
              )}

              {planInfo && dataInicial && dataFinal && (() => {
                const days = dateDiffInDays(dataInicial, dataFinal);
                const maxDays = planInfo.capabilities.max_history_days;
                if (days > maxDays) {
                  return (
                    <div className="mt-3 p-4 bg-warning-subtle border border-warning/20 rounded-card" role="alert">
                      <div className="flex items-start gap-3">
                        <svg role="img" aria-label="Aviso" className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                              onShowUpgradeModal("smartlic_pro", "date_range");
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
            </div>

            {/* Filter Panels - moved into accordion */}
            <FilterPanel
              locationFiltersOpen={locationFiltersOpen}
              setLocationFiltersOpen={setLocationFiltersOpen}
              advancedFiltersOpen={advancedFiltersOpen}
              setAdvancedFiltersOpen={setAdvancedFiltersOpen}
              esferas={esferas}
              setEsferas={setEsferas}
              ufsSelecionadas={ufsSelecionadas}
              municipios={municipios}
              setMunicipios={setMunicipios}
              status={status}
              setStatus={setStatus}
              modalidades={modalidades}
              setModalidades={setModalidades}
              valorMin={valorMin}
              setValorMin={setValorMin}
              valorMax={valorMax}
              setValorMax={setValorMax}
              setValorValid={setValorValid}
              loading={loading}
              clearResult={clearResult}
            />
          </div>
        )}
      </section>

    </>
  );
}
