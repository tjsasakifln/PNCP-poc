"use client";

import { StatusFilter, type StatusLicitacao } from "./StatusFilter";
import { ModalidadeFilter } from "./ModalidadeFilter";
import { ValorFilter } from "./ValorFilter";
import { EsferaFilter, type Esfera } from "../../components/EsferaFilter";
import { MunicipioFilter, type Municipio } from "../../components/MunicipioFilter";
import { MapPin, ChevronDown, Filter } from "lucide-react";

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
          <MapPin className="w-5 h-5 text-ink-muted" strokeWidth={2} aria-hidden="true" />
          Filtros avançados de localização
          {(() => {
            const activeCount = (esferas.length > 0 && esferas.length < 3 ? 1 : 0) + (municipios.length > 0 ? 1 : 0);
            return activeCount > 0 ? (
              <span className="ml-2 inline-flex items-center justify-center px-2 py-0.5 text-xs font-bold rounded-full bg-brand-blue text-white" aria-label={`${activeCount} filtro${activeCount > 1 ? 's' : ''} ativo${activeCount > 1 ? 's' : ''}`}>
                {activeCount}
              </span>
            ) : null;
          })()}
          <ChevronDown className={`w-4 h-4 ml-auto transition-transform ${locationFiltersOpen ? 'rotate-180' : ''}`} strokeWidth={2} aria-hidden="true" />
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
          <Filter className="w-5 h-5 text-ink-muted" strokeWidth={2} aria-hidden="true" />
          Filtros Avançados
          <ChevronDown className={`w-4 h-4 ml-auto transition-transform ${advancedFiltersOpen ? 'rotate-180' : ''}`} strokeWidth={2} aria-hidden="true" />
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
