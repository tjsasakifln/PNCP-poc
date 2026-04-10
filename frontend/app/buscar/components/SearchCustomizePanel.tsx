"use client";

import type { ValidationErrors } from "../../types";
import { RegionSelector } from "../../components/RegionSelector";
import { CustomDateInput } from "../../components/CustomDateInput";
import { Tooltip } from "../../components/ui/Tooltip";
import type { StatusLicitacao } from "./StatusFilter";
import type { Esfera } from "../../components/EsferaFilter";
import type { Municipio } from "../../components/MunicipioFilter";
import FilterPanel from "./FilterPanel";
import { UFS, UF_NAMES } from "../../../lib/constants/uf-names";
import { dateDiffInDays } from "../../../lib/utils/dateDiffInDays";
import {
  Info,
  AlertTriangle,
  SlidersHorizontal,
  ChevronDown,
  Globe,
  Check,
} from "lucide-react";

export interface SearchCustomizePanelProps {
  customizeOpen: boolean;
  setCustomizeOpen: (open: boolean) => void;
  ufsSelecionadas: Set<string>;
  toggleUf: (uf: string) => void;
  toggleRegion: (regionUfs: string[]) => void;
  selecionarTodos: () => void;
  limparSelecao: () => void;
  dataInicial: string;
  setDataInicial: (date: string) => void;
  dataFinal: string;
  setDataFinal: (date: string) => void;
  modoBusca: "abertas" | "publicacao";
  dateLabel: string;
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
  validationErrors: ValidationErrors;
  loading: boolean;
  clearResult: () => void;
  planInfo: { plan_name: string; capabilities: { max_history_days: number } } | null;
  onShowUpgradeModal: (plan?: string, source?: string) => void;
  compactSummary: string;
}

export default function SearchCustomizePanel({
  customizeOpen, setCustomizeOpen,
  ufsSelecionadas, toggleUf, toggleRegion, selecionarTodos, limparSelecao,
  dataInicial, setDataInicial, dataFinal, setDataFinal,
  modoBusca, dateLabel,
  locationFiltersOpen, setLocationFiltersOpen,
  advancedFiltersOpen, setAdvancedFiltersOpen,
  esferas, setEsferas, municipios, setMunicipios,
  status, setStatus, modalidades, setModalidades,
  valorMin, setValorMin, valorMax, setValorMax, setValorValid,
  validationErrors, loading, clearResult,
  planInfo, onShowUpgradeModal,
  compactSummary,
}: SearchCustomizePanelProps) {
  return (
    <section className="mb-6 animate-fade-in-up stagger-3">
      <button
        type="button"
        onClick={() => setCustomizeOpen(!customizeOpen)}
        aria-expanded={customizeOpen}
        data-tour="customize-toggle"
        className="w-full text-base font-semibold text-ink mb-2 flex items-center gap-2 hover:text-brand-blue transition-colors"
      >
        <SlidersHorizontal className="w-5 h-5 text-ink-muted" strokeWidth={2} aria-hidden="true" />
        Personalizar análise
        <ChevronDown className={`w-4 h-4 ml-auto transition-transform ${customizeOpen ? 'rotate-180' : ''}`} strokeWidth={2} aria-hidden="true" />
      </button>

      {!customizeOpen && (
        <button
          type="button"
          onClick={() => setCustomizeOpen(true)}
          className="w-full flex items-center justify-center gap-2 text-sm text-ink-secondary py-2 hover:text-brand-blue transition-colors cursor-pointer animate-fade-in-up"
          data-testid="compact-summary"
        >
          <Info className="w-4 h-4 flex-shrink-0" strokeWidth={2} aria-hidden="true" />
          <span>{compactSummary}</span>
        </button>
      )}

      {customizeOpen && (
        <div className="space-y-6 animate-fade-in-up">
          <div className="relative z-10" data-tour="uf-selector">
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

            <div className="flex items-center gap-3 mb-3">
              <button
                type="button"
                onClick={selecionarTodos}
                aria-pressed={ufsSelecionadas.size === UFS.length}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-button border text-sm font-semibold transition-all duration-200 ${
                  ufsSelecionadas.size === UFS.length
                    ? "bg-brand-navy text-white border-brand-navy"
                    : "bg-surface-0 text-ink border-strong hover:border-accent hover:text-brand-blue hover:bg-brand-blue-subtle"
                }`}
              >
                <Globe className="w-4 h-4 flex-shrink-0" strokeWidth={2} aria-hidden="true" />
                Todo o Brasil (27 estados)
                {ufsSelecionadas.size === UFS.length && (
                  <Check className="w-4 h-4 flex-shrink-0" strokeWidth={2} aria-hidden="true" />
                )}
              </button>
              <button
                type="button"
                onClick={limparSelecao}
                className="text-sm font-medium text-ink-muted hover:text-ink transition-colors whitespace-nowrap"
              >
                Limpar seleção
              </button>
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

          <div className="relative z-0" data-tour="period-selector">
            {modoBusca === "abertas" ? (
              <div className="p-3 bg-brand-blue-subtle rounded-card border border-brand-blue/20">
                <p className="text-sm font-medium text-brand-navy">
                  {dateLabel}
                </p>
                <p className="text-xs text-ink-secondary mt-1">
                  {status === "encerrada"
                    ? "Buscando licitações encerradas — processos finalizados ou homologados"
                    : status === "em_julgamento"
                    ? "Buscando licitações em julgamento — propostas encerradas, em análise"
                    : status === "todos"
                    ? "Todas as licitações abertas — todos os status incluídos"
                    : "Todas as licitações abertas para propostas"}
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
                      <AlertTriangle role="img" aria-label="Aviso" className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" strokeWidth={2} />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-warning mb-1">
                          Período muito longo para seu plano
                        </p>
                        <p className="text-sm text-ink-secondary">
                          Seu plano {planInfo.plan_name} permite análises de até {maxDays} dias.
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
  );
}
