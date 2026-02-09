"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";

/**
 * OrgaoFilter Component
 *
 * Multi-select autocomplete filter for government agencies/entities.
 * Searches through existing search results to find matching agencies.
 *
 * Features:
 * - Debounced search (300ms)
 * - Maximum 20 suggestions
 * - Removable badges for selected agencies
 * - Shows frequent agencies based on search results
 *
 * Based on specification from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md (Section 6)
 */

export interface Orgao {
  codigo: string; // Unique identifier (CNPJ or internal code)
  nome: string;
  uf?: string;
}

interface OrgaoFilterProps {
  value: Orgao[];
  onChange: (orgaos: Orgao[]) => void;
  disabled?: boolean;
  // Optional: pass available agencies from search results
  availableOrgaos?: Orgao[];
}

/**
 * Custom debounce hook - lightweight alternative to use-debounce package
 */
function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const callbackRef = useRef(callback);

  // Update callback ref on each render
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        callbackRef.current(...args);
      }, delay);
    },
    [delay]
  ) as T;

  return debouncedCallback;
}

// Common Brazilian government agencies for quick selection
const ORGAOS_FREQUENTES: Orgao[] = [
  { codigo: "ms", nome: "Ministerio da Saude", uf: "DF" },
  { codigo: "mec", nome: "Ministerio da Educacao", uf: "DF" },
  { codigo: "inss", nome: "INSS - Instituto Nacional do Seguro Social", uf: "DF" },
  { codigo: "petrobras", nome: "Petrobras", uf: "RJ" },
  { codigo: "bb", nome: "Banco do Brasil", uf: "DF" },
  { codigo: "caixa", nome: "Caixa Economica Federal", uf: "DF" },
];

export function OrgaoFilter({
  value,
  onChange,
  disabled = false,
  availableOrgaos = [],
}: OrgaoFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [suggestions, setSuggestions] = useState<Orgao[]>([]);
  const [loading, setLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Combine available agencies with frequent ones for suggestions
  const allOrgaos = useMemo(() => {
    const combined = [...ORGAOS_FREQUENTES];

    // Add available agencies from search results
    for (const orgao of availableOrgaos) {
      if (!combined.find(o => o.codigo === orgao.codigo)) {
        combined.push(orgao);
      }
    }

    return combined;
  }, [availableOrgaos]);

  // Search agencies based on term
  const searchOrgaos = useCallback(
    (term: string) => {
      if (term.length < 2) {
        setSuggestions([]);
        return;
      }

      setLoading(true);

      try {
        const termLower = term.toLowerCase();

        // Filter agencies by search term
        const filtered = allOrgaos.filter((o) =>
          o.nome.toLowerCase().includes(termLower)
        );

        // Remove already selected agencies
        const selectedCodes = new Set(value.map((o) => o.codigo));
        const unique = filtered.filter((o) => !selectedCodes.has(o.codigo));

        // Sort by name and limit to 20
        unique.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
        setSuggestions(unique.slice(0, 20));
      } finally {
        setLoading(false);
      }
    },
    [allOrgaos, value]
  );

  // Debounced search (300ms)
  const debouncedSearch = useDebouncedCallback(searchOrgaos, 300);

  // Trigger search when search term changes
  useEffect(() => {
    debouncedSearch(search);
  }, [search, debouncedSearch]);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  // Keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        if (!isOpen && suggestions.length > 0) {
          setIsOpen(true);
        }
        setHighlightedIndex((prev) =>
          Math.min(prev + 1, suggestions.length - 1)
        );
        break;

      case "ArrowUp":
        event.preventDefault();
        setHighlightedIndex((prev) => Math.max(prev - 1, 0));
        break;

      case "Enter":
        event.preventDefault();
        if (highlightedIndex >= 0 && suggestions[highlightedIndex]) {
          handleSelect(suggestions[highlightedIndex]);
        }
        break;

      case "Escape":
        event.preventDefault();
        event.stopPropagation();
        setIsOpen(false);
        setHighlightedIndex(-1);
        setSearch("");
        break;

      case "Backspace":
        if (search === "" && value.length > 0) {
          // Remove last selected agency
          onChange(value.slice(0, -1));
        }
        break;
    }
  };

  // Scroll highlighted item into view
  useEffect(() => {
    if (isOpen && highlightedIndex >= 0 && listRef.current) {
      const highlightedElement = listRef.current.children[
        highlightedIndex
      ] as HTMLElement;
      if (highlightedElement) {
        highlightedElement.scrollIntoView({ block: "nearest" });
      }
    }
  }, [isOpen, highlightedIndex]);

  const handleSelect = (orgao: Orgao) => {
    if (!value.find((o) => o.codigo === orgao.codigo)) {
      onChange([...value, orgao]);
    }
    setSearch("");
    setIsOpen(false);
    setHighlightedIndex(-1);
    inputRef.current?.focus();
  };

  const handleRemove = (codigo: string) => {
    onChange(value.filter((o) => o.codigo !== codigo));
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setIsOpen(true);
    setHighlightedIndex(-1);
  };

  const handleInputFocus = () => {
    if (search.length >= 2 && suggestions.length > 0) {
      setIsOpen(true);
    }
  };

  const placeholderText = useMemo(() => {
    if (disabled) return "Filtros desabilitados";
    if (value.length > 0) return "Adicionar mais...";
    return "Buscar orgao...";
  }, [disabled, value.length]);

  return (
    <div className="space-y-3" ref={containerRef}>
      <div className="flex items-center justify-between">
        <label className="block text-base font-semibold text-ink">
          Orgao/Entidade:{" "}
          <span className="text-ink-muted font-normal">(opcional)</span>
        </label>
        {value.length > 0 && (
          <button
            type="button"
            onClick={handleClearAll}
            className="text-sm text-ink-muted hover:text-error transition-colors"
          >
            Limpar todos
          </button>
        )}
      </div>

      {/* Search Input */}
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
          <svg
              role="img"
              aria-label="Ícone"
            className="h-5 w-5 text-ink-muted"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
        </div>

        <input
          ref={inputRef}
          type="text"
          value={search}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onKeyDown={handleKeyDown}
          placeholder={placeholderText}
          disabled={disabled}
          aria-label="Buscar orgao"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          aria-controls="orgao-listbox"
          aria-activedescendant={
            highlightedIndex >= 0
              ? `orgao-option-${highlightedIndex}`
              : undefined
          }
          className={`
            w-full pl-10 pr-10 py-3 text-base
            border border-strong rounded-input
            bg-surface-0 text-ink placeholder-ink-faint
            focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue
            disabled:bg-surface-1 disabled:text-ink-muted disabled:cursor-not-allowed
            transition-colors
          `}
        />

        {/* Loading Spinner */}
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <svg
              className="animate-spin h-5 w-5 text-brand-blue"
              viewBox="0 0 24 24"
              role="img"
              aria-label="Carregando"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
        )}

        {/* Suggestions Dropdown */}
        {isOpen && (search.length >= 2 || suggestions.length > 0) && (
          <ul
            ref={listRef}
            id="orgao-listbox"
            role="listbox"
            className="absolute z-50 w-full mt-1 bg-surface-0 border border-strong rounded-input shadow-lg
                       max-h-60 overflow-auto animate-fade-in"
          >
            {suggestions.length === 0 ? (
              <li className="px-4 py-3 text-sm text-ink-muted text-center">
                {search.length < 2
                  ? "Digite pelo menos 2 caracteres"
                  : loading
                  ? "Buscando..."
                  : "Nenhum orgao encontrado"}
              </li>
            ) : (
              suggestions.map((orgao, index) => (
                <li
                  key={orgao.codigo}
                  id={`orgao-option-${index}`}
                  role="option"
                  aria-selected={highlightedIndex === index}
                  onClick={() => handleSelect(orgao)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  className={`
                    px-4 py-3 cursor-pointer transition-colors
                    flex items-center justify-between
                    ${
                      highlightedIndex === index
                        ? "bg-brand-blue-subtle text-brand-navy"
                        : "text-ink hover:bg-surface-1"
                    }
                  `}
                >
                  <span className="text-sm">{orgao.nome}</span>
                  {orgao.uf && (
                    <span className="text-xs text-ink-muted ml-2">
                      {orgao.uf}
                    </span>
                  )}
                </li>
              ))
            )}
          </ul>
        )}
      </div>

      {/* Frequent Agencies - show when no search */}
      {!search && value.length === 0 && !disabled && (
        <div className="space-y-2">
          <p className="text-xs text-ink-muted">Orgaos frequentes:</p>
          <div className="flex flex-wrap gap-2">
            {ORGAOS_FREQUENTES.slice(0, 4).map((orgao) => (
              <button
                key={orgao.codigo}
                type="button"
                onClick={() => handleSelect(orgao)}
                className="text-xs px-2 py-1 rounded-md
                           bg-surface-1 text-ink-secondary
                           hover:bg-surface-2 hover:text-ink
                           transition-colors"
              >
                {orgao.nome.length > 25
                  ? orgao.nome.substring(0, 25) + "..."
                  : orgao.nome}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Selected Agencies */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((orgao) => (
            <span
              key={orgao.codigo}
              className="inline-flex items-center gap-1.5 px-3 py-1.5
                         bg-brand-blue-subtle text-brand-navy dark:text-brand-blue
                         rounded-full text-sm font-medium
                         border border-brand-blue/20 animate-fade-in"
            >
              <span>
                {orgao.nome.length > 30
                  ? orgao.nome.substring(0, 30) + "..."
                  : orgao.nome}
              </span>
              <button
                type="button"
                onClick={() => handleRemove(orgao.codigo)}
                className="ml-0.5 p-0.5 rounded-full hover:bg-brand-blue/20 transition-colors"
                aria-label={`Remover ${orgao.nome}`}
              >
                <svg
              role="img"
              aria-label="Ícone"
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Helper text */}
      <p className="text-xs text-ink-muted">
        Filtre por orgaos/entidades especificos (ex: Prefeitura, Ministerio)
      </p>
    </div>
  );
}
