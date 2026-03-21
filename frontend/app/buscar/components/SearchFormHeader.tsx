"use client";

import type { Setor } from "../../types";
import { CustomSelect } from "../../components/CustomSelect";
import type { TermValidation } from "../hooks/useSearchFilters";
import { Button } from "../../../components/ui/button";
import {
  Info,
  AlertTriangle,
  X,
  RefreshCw,
} from "lucide-react";

export interface SearchFormHeaderProps {
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
  termosArray: string[];
  termoInput: string;
  setTermoInput: (input: string) => void;
  termValidation: TermValidation | null;
  addTerms: (newTerms: string[]) => void;
  removeTerm: (term: string) => void;
  clearResult: () => void;
  showFirstUseTip?: boolean;
  onDismissFirstUseTip?: () => void;
}

export default function SearchFormHeader({
  setores, setoresLoading, setoresError, setoresUsingFallback, setoresUsingStaleCache, staleCacheAge, setoresRetryCount,
  setorId, setSetorId, fetchSetores,
  searchMode, setSearchMode,
  termosArray, termoInput, setTermoInput, termValidation, addTerms, removeTerm,
  clearResult,
  showFirstUseTip, onDismissFirstUseTip,
}: SearchFormHeaderProps) {
  return (
    <>
      {setoresUsingStaleCache && (
        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-card flex items-start gap-3 animate-fade-in-up" role="status">
          <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" strokeWidth={2} aria-hidden="true" />
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

      {setoresUsingFallback && !setoresUsingStaleCache && (
        <div className="mb-4 p-3 bg-[var(--warning-subtle)] border border-[var(--warning)]/20 rounded-card flex items-start gap-3 animate-fade-in-up" role="alert">
          <AlertTriangle className="w-5 h-5 text-[var(--warning)] flex-shrink-0 mt-0.5" strokeWidth={2} aria-hidden="true" />
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

      <section className="mb-6 animate-fade-in-up stagger-1 relative z-30" data-tour="setor-filter">
        <label className="block text-base font-semibold text-ink mb-3">
          Buscar por:
        </label>
        <div className="flex rounded-button border border-strong overflow-hidden mb-4">
          <button
            type="button"
            onClick={() => { setSearchMode("setor"); clearResult(); }}
            aria-pressed={searchMode === "setor"}
            aria-label="Buscar por setor"
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
            aria-pressed={searchMode === "termos"}
            aria-label="Buscar por termos específicos"
            className={`flex-1 py-2.5 text-sm sm:text-base font-medium transition-all duration-200 ${
              searchMode === "termos"
                ? "bg-brand-navy text-white"
                : "bg-surface-0 text-ink-secondary hover:bg-surface-1"
            }`}
          >
            Termos Específicos
          </button>
        </div>

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
                  <AlertTriangle className="w-5 h-5 text-error flex-shrink-0 mt-0.5" strokeWidth={2} aria-hidden="true" />
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
                    <RefreshCw className="w-4 h-4" strokeWidth={2} aria-hidden="true" />
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
                placeholder="Ex: TI, Engenharia, Facilities, Saúde..."
              />
            )}
          </div>
        )}

        {searchMode === "termos" && (
          <div>
            {termValidation && termValidation.ignored.length > 0 && (
              <div className="mb-4 border border-warning/30 bg-warning-subtle rounded-card p-4 animate-fade-in-up">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" strokeWidth={2} aria-hidden="true" />
                  <div className="flex-1">
                    <p className="font-semibold text-sm text-warning mb-2">
                      Atenção: {termValidation.ignored.length} termo{termValidation.ignored.length > 1 ? 's' : ''} não será{termValidation.ignored.length > 1 ? 'ão' : ''} utilizado{termValidation.ignored.length > 1 ? 's' : ''} na análise
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
                    <X className="w-3.5 h-3.5" strokeWidth={2.5} aria-hidden="true" />
                  </button>
                </span>
              ))}
              <input
                id="termos-busca"
                type="text"
                aria-label="Adicionar termos de busca"
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

      {showFirstUseTip && (
        <div className="mb-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 flex items-start gap-3 animate-fade-in-up" data-testid="first-use-tip">
          <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" strokeWidth={2} aria-hidden="true" />
          <p className="text-sm text-blue-700 dark:text-blue-300 flex-1">
            <strong>Dica:</strong> selecione seu setor e clique Buscar. Personalize depois se quiser.
          </p>
          <Button
            type="button"
            onClick={onDismissFirstUseTip}
            variant="ghost"
            size="icon"
            aria-label="Fechar dica"
            className="h-6 w-6 text-blue-400 hover:text-blue-600 dark:hover:text-blue-200 flex-shrink-0"
            data-testid="dismiss-first-use-tip"
          >
            <X className="w-4 h-4" strokeWidth={2} />
          </Button>
        </div>
      )}
    </>
  );
}
