"use client";

import type { BuscaResult } from "../../types";
import type { TermValidation } from "../hooks/useSearchFilters";
import { Button } from "../../../components/ui/button";
import { Bookmark } from "lucide-react";

export interface SearchFormActionsProps {
  loading: boolean;
  buscar: () => void;
  searchButtonRef: React.RefObject<HTMLButtonElement | null>;
  canSearch: boolean;
  searchLabel: string;
  searchMode: "setor" | "termos";
  termValidation: TermValidation | null;
  result: BuscaResult | null;
  handleSaveSearch: () => void;
  isMaxCapacity: boolean;
  isTrialExpired?: boolean;
  isGracePeriod?: boolean;
}

export default function SearchFormActions({
  loading, buscar, searchButtonRef,
  canSearch, searchLabel, searchMode, termValidation,
  result, handleSaveSearch, isMaxCapacity,
  isTrialExpired, isGracePeriod,
}: SearchFormActionsProps) {
  return (
    <div className="mb-6 space-y-3 sm:relative sticky bottom-4 sm:bottom-auto z-20 bg-[var(--canvas)] sm:bg-transparent pt-2 sm:pt-0 -mx-4 px-4 sm:mx-0 sm:px-0 pb-2 sm:pb-0 animate-fade-in-up stagger-2">
      <Button
        ref={searchButtonRef}
        onClick={buscar}
        disabled={loading || !canSearch || isTrialExpired || isGracePeriod}
        loading={loading}
        type="button"
        aria-label="Iniciar busca de licitações"
        aria-busy={loading}
        data-tour="search-button"
        title={isGracePeriod ? "Análises suspensas ate regularizacao do pagamento." : isTrialExpired ? "Seu trial expirou. Ative um plano para continuar buscando." : undefined}
        variant="primary"
        size="lg"
        className="w-full py-3.5 sm:py-4 text-base sm:text-lg font-semibold
                   active:bg-brand-blue
                   disabled:bg-ink-faint disabled:text-ink-muted
                   min-h-[48px] sm:min-h-[52px]"
      >
        {loading ? (
          "Consultando múltiplas fontes e aplicando filtros inteligentes..."
        ) : searchMode === "termos" && termValidation ? (
          termValidation.valid.length === 0
            ? "Adicione termos válidos para buscar"
            : `Buscar ${termValidation.valid.length} termo${termValidation.valid.length > 1 ? 's' : ''}`
        ) : (
          `Buscar ${searchLabel}`
        )}
      </Button>

      {result && result.resumo.total_oportunidades > 0 && (
        <Button
          onClick={handleSaveSearch}
          disabled={isMaxCapacity}
          type="button"
          variant="outline"
          size="lg"
          className="w-full text-brand-navy border-brand-navy hover:bg-brand-blue-subtle
                     disabled:text-ink-muted disabled:border-ink-faint"
          title={isMaxCapacity ? "Máximo de 10 análises salvas atingido" : "Salvar esta análise"}
        >
          <Bookmark className="w-5 h-5" strokeWidth={2} aria-hidden="true" />
          {isMaxCapacity ? "Limite de análises atingido" : "Salvar Análise"}
        </Button>
      )}
    </div>
  );
}
