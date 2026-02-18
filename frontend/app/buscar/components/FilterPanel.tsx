"use client";

import { StatusFilter, type StatusLicitacao } from "../../../components/StatusFilter";
import { ModalidadeFilter } from "../../../components/ModalidadeFilter";
import { ValorFilter } from "../../../components/ValorFilter";
import { EsferaFilter, type Esfera } from "../../components/EsferaFilter";
import { MunicipioFilter, type Municipio } from "../../components/MunicipioFilter";

export interface FilterPanelProps {
  // Location filters
  locationFiltersOpen: boolean;
  setLocationFiltersOpen: (open: boolean) => void;
  esferas: Esfera[];
  setEsferas: (e: Esfera[]) => void;
  ufsSelecionadas: Set<string>;
  municipios: Municipio[];
  setMunicipios: (m: Municipio[]) => void;

  // Advanced filters
  advancedFiltersOpen: boolean;
  setAdvancedFiltersOpen: (open: boolean) => void;
  status: StatusLicitacao;
  setStatus: (s: StatusLicitacao) => void;
  modalidades: number[];
  setModalidades: (m: number[]) => void;
  valorMin: number | null;
  setValorMin: (v: number | null) => void;
  valorMax: number | null;
  setValorMax: (v: number | null) => void;
  setValorValid: (valid: boolean) => void;

  loading: boolean;
  clearResult: () => void;
}

export default function FilterPanel({
  locationFiltersOpen, setLocationFiltersOpen,
  advancedFiltersOpen, setAdvancedFiltersOpen,
  esferas, setEsferas, ufsSelecionadas, municipios, setMunicipios,
  status, setStatus, modalidades, setModalidades,
  valorMin, setValorMin, valorMax, setValorMax, setValorValid,
  loading, clearResult,
}: FilterPanelProps) {
  return (
    <>
      {/* P1 Filters: Esfera and Municipio (Location Section) - STORY-170 AC7 */}
      <section className="mb-6 animate-fade-in-up stagger-3 relative z-0">
        <button
          type="button"
          onClick={() => setLocationFiltersOpen(!locationFiltersOpen)}
          className="w-full text-base font-semibold text-ink mb-4 flex items-center gap-2 hover:text-brand-blue transition-colors"
        >
          <svg className="w-5 h-5 text-ink-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Filtragem por Localização
          <svg className={`w-4 h-4 ml-auto transition-transform ${locationFiltersOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {locationFiltersOpen && (
          <div className="space-y-6 p-4 bg-surface-1 rounded-card border border-strong animate-fade-in-up">
            <EsferaFilter
              value={esferas}
              onChange={(newEsferas) => { setEsferas(newEsferas); clearResult(); }}
              disabled={loading}
            />
            <MunicipioFilter
              ufs={Array.from(ufsSelecionadas)}
              value={municipios}
              onChange={(newMunicipios) => { setMunicipios(newMunicipios); clearResult(); }}
              disabled={loading}
            />
          </div>
        )}
      </section>

      {/* P0 Filters: Status, Modalidade, Valor (Advanced Filters Section) - STORY-170 AC7 */}
      <section className="mb-6 animate-fade-in-up stagger-4 relative z-0">
        <button
          type="button"
          onClick={() => setAdvancedFiltersOpen(!advancedFiltersOpen)}
          aria-expanded={advancedFiltersOpen}
          className="w-full text-base font-semibold text-ink mb-4 flex items-center gap-2 hover:text-brand-blue transition-colors"
        >
          <svg className="w-5 h-5 text-ink-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filtros Avançados
          <svg className={`w-4 h-4 ml-auto transition-transform ${advancedFiltersOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {advancedFiltersOpen && (
          <div className="space-y-6 p-4 bg-surface-1 rounded-card border border-strong animate-fade-in-up">
            <StatusFilter
              value={status}
              onChange={(newStatus) => { setStatus(newStatus); clearResult(); }}
              disabled={loading}
            />
            <ModalidadeFilter
              value={modalidades}
              onChange={(newModalidades) => { setModalidades(newModalidades); clearResult(); }}
              disabled={loading}
            />
            <ValorFilter
              valorMin={valorMin}
              valorMax={valorMax}
              onChange={(min, max) => { setValorMin(min); setValorMax(max); clearResult(); }}
              onValidationChange={setValorValid}
              disabled={loading}
            />
          </div>
        )}
      </section>
    </>
  );
}
