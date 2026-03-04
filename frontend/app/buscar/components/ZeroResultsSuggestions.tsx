"use client";

import type { FilterStats } from "../../types";
import { FilterStatsBreakdown } from "./FilterStatsBreakdown";

interface ZeroResultsSuggestionsProps {
  sectorName: string;
  ufCount: number;
  dayRange: number;
  // SAB-005 AC5: UF abbreviations for contextual message
  ufNames?: string[];
  onAdjustPeriod?: () => void;
  onAddNeighborStates?: () => void;
  onChangeSector?: () => void;
  // AC11: nearby results from cache
  nearbyResultsCount?: number;
  onViewNearbyResults?: () => void;
  // STAB-005 AC2: Total from sources + filter stats
  totalFromSources?: number;
  filterStats?: FilterStats | null;
}

export function ZeroResultsSuggestions({
  sectorName,
  ufCount,
  dayRange,
  ufNames,
  onAdjustPeriod,
  onAddNeighborStates,
  onChangeSector,
  nearbyResultsCount,
  onViewNearbyResults,
  totalFromSources,
  filterStats,
}: ZeroResultsSuggestionsProps) {
  const hasSourceData = totalFromSources != null && totalFromSources > 0;
  // SAB-005 AC5: Format UF list for contextual message
  const ufLabel = ufNames && ufNames.length > 0 && ufNames.length <= 5
    ? ufNames.join(", ")
    : `${ufCount} ${ufCount === 1 ? "estado" : "estados"}`;

  return (
    <div className="mt-6 sm:mt-8 animate-fade-in-up" data-testid="zero-results-suggestions">
      <div className="text-center py-10 px-4">
        {/* Icon */}
        <div className="mx-auto mb-4 w-14 h-14 flex items-center justify-center rounded-full bg-[var(--surface-1)]">
          <svg aria-hidden="true" className="w-7 h-7 text-[var(--ink-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </div>

        {/* AC10: Specific message */}
        <h3 className="text-lg font-display font-semibold text-[var(--ink)] mb-2">
          Nenhuma oportunidade encontrada
        </h3>

        {/* STAB-005 AC2: Show total from sources when available */}
        {hasSourceData ? (
          <p className="text-sm text-[var(--ink-secondary)] mb-4 max-w-lg mx-auto" data-testid="source-total-message">
            <span className="font-semibold text-[var(--ink)]">{totalFromSources}</span>{" "}
            {totalFromSources === 1 ? "licitação encontrada" : "licitações encontradas"}{" "}
            nas fontes oficiais, mas nenhuma corresponde ao setor{" "}
            <span className="font-medium">{sectorName}</span>.
          </p>
        ) : (
          <p className="text-sm text-[var(--ink-secondary)] mb-6 max-w-md mx-auto" data-testid="zero-results-context">
            Nenhuma licitação encontrada para <span className="font-medium">{sectorName}</span> em{" "}
            <span className="font-medium">{ufLabel}</span>.{" "}
            Tente ampliar o período ou os estados.
          </p>
        )}

        {/* STAB-005 AC2/AC3: Filter stats breakdown when available */}
        {filterStats && (
          <div className="max-w-md mx-auto mb-6 text-left">
            <FilterStatsBreakdown stats={filterStats} />
          </div>
        )}

        {/* AC11: Nearby results from cache */}
        {nearbyResultsCount != null && nearbyResultsCount > 0 && onViewNearbyResults && (
          <div className="mb-6 p-4 bg-[var(--brand-blue-subtle)] border border-[var(--border-accent)] rounded-card max-w-md mx-auto">
            <p className="text-sm text-[var(--ink)] mb-3">
              Encontramos <span className="font-bold text-[var(--brand-blue)]">{nearbyResultsCount}</span> oportunidades em estados próximos.
            </p>
            <button
              onClick={onViewNearbyResults}
              className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm font-medium
                         hover:bg-[var(--brand-blue)] transition-colors"
              data-testid="view-nearby-results"
            >
              Ver resultados
            </button>
          </div>
        )}

        {/* AC10 + AC12: Actionable suggestions as buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 max-w-lg mx-auto">
          {onAdjustPeriod && (
            <button
              onClick={onAdjustPeriod}
              className="w-full sm:w-auto px-4 py-2.5 border border-[var(--border)] rounded-button text-sm font-medium
                         text-[var(--ink)] hover:bg-[var(--surface-1)] hover:border-[var(--border-strong)] transition-colors
                         flex items-center justify-center gap-2"
              data-testid="suggestion-adjust-period"
            >
              <svg aria-hidden="true" className="w-4 h-4 text-[var(--ink-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Ampliar periodo
            </button>
          )}
          {onAddNeighborStates && (
            <button
              onClick={onAddNeighborStates}
              className="w-full sm:w-auto px-4 py-2.5 border border-[var(--border)] rounded-button text-sm font-medium
                         text-[var(--ink)] hover:bg-[var(--surface-1)] hover:border-[var(--border-strong)] transition-colors
                         flex items-center justify-center gap-2"
              data-testid="suggestion-add-neighbors"
            >
              <svg aria-hidden="true" className="w-4 h-4 text-[var(--ink-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Adicionar estados vizinhos
            </button>
          )}
          {onChangeSector && (
            <button
              onClick={onChangeSector}
              className="w-full sm:w-auto px-4 py-2.5 border border-[var(--border)] rounded-button text-sm font-medium
                         text-[var(--ink)] hover:bg-[var(--surface-1)] hover:border-[var(--border-strong)] transition-colors
                         flex items-center justify-center gap-2"
              data-testid="suggestion-change-sector"
            >
              <svg aria-hidden="true" className="w-4 h-4 text-[var(--ink-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              Verificar setor
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
