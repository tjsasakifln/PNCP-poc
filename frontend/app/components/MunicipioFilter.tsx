"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";

/**
 * MunicipioFilter Component
 *
 * Multi-select autocomplete filter for municipalities.
 * Integrates with IBGE API for municipality data.
 *
 * Features:
 * - Debounced search (300ms)
 * - Parallel fetching for multiple UFs
 * - Maximum 20 suggestions
 * - Disabled when no UF is selected
 * - Removable badges for selected municipalities
 *
 * Based on specification from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 */

export interface Municipio {
  codigo: string; // IBGE code
  nome: string;
  uf: string;
}

interface MunicipioFilterProps {
  ufs: string[]; // Selected UFs - filter is disabled when empty
  value: Municipio[];
  onChange: (municipios: Municipio[]) => void;
  disabled?: boolean;
}

// Cache for IBGE municipality data to avoid repeated API calls
const municipioCache: Record<string, Municipio[]> = {};

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

export function MunicipioFilter({
  ufs,
  value,
  onChange,
  disabled = false,
}: MunicipioFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [suggestions, setSuggestions] = useState<Municipio[]>([]);
  const [loading, setLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const isDisabled = disabled || ufs.length === 0;

  // Fetch municipalities from IBGE API for a single UF
  const fetchMunicipiosForUF = async (uf: string): Promise<Municipio[]> => {
    // Check cache first
    if (municipioCache[uf]) {
      return municipioCache[uf];
    }

    try {
      const response = await fetch(
        `https://servicodados.ibge.gov.br/api/v1/localidades/estados/${uf}/municipios`
      );

      if (!response.ok) {
        console.error(`IBGE API error for UF ${uf}: ${response.status}`);
        return [];
      }

      const data = await response.json();
      const municipios: Municipio[] = data.map((m: { id: number; nome: string }) => ({
        codigo: m.id.toString(),
        nome: m.nome,
        uf: uf,
      }));

      // Cache the result
      municipioCache[uf] = municipios;

      return municipios;
    } catch (error) {
      console.error(`Error fetching municipalities for UF ${uf}:`, error);
      return [];
    }
  };

  // Search municipalities based on term
  const searchMunicipios = async (term: string) => {
    if (term.length < 2 || ufs.length === 0) {
      setSuggestions([]);
      return;
    }

    setLoading(true);

    try {
      // Fetch municipalities for all selected UFs in parallel
      const promises = ufs.map((uf) => fetchMunicipiosForUF(uf));
      const results = await Promise.all(promises);

      // Flatten and filter by search term
      const termLower = term.toLowerCase();
      const allMunicipios = results.flat();

      const filtered = allMunicipios.filter((m) =>
        m.nome.toLowerCase().includes(termLower)
      );

      // Remove duplicates (same codigo) and already selected
      const selectedCodes = new Set(value.map((m) => m.codigo));
      const unique = filtered.filter(
        (m, i, arr) =>
          arr.findIndex((x) => x.codigo === m.codigo) === i &&
          !selectedCodes.has(m.codigo)
      );

      // Sort by name and limit to 20
      unique.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
      setSuggestions(unique.slice(0, 20));
    } catch (error) {
      console.error("Error searching municipalities:", error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  // Debounced search (300ms)
  const debouncedSearch = useDebouncedCallback(searchMunicipios, 300);

  // Trigger search when search term or UFs change
  useEffect(() => {
    debouncedSearch(search);
  }, [search, ufs, debouncedSearch]);

  // Clear suggestions when UFs change
  useEffect(() => {
    setSuggestions([]);
    setSearch("");
  }, [ufs.join(",")]);

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
          // Remove last selected municipality
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

  const handleSelect = (municipio: Municipio) => {
    if (!value.find((m) => m.codigo === municipio.codigo)) {
      onChange([...value, municipio]);
    }
    setSearch("");
    setIsOpen(false);
    setHighlightedIndex(-1);
    inputRef.current?.focus();
  };

  const handleRemove = (codigo: string) => {
    onChange(value.filter((m) => m.codigo !== codigo));
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
    if (isDisabled) return "Selecione uma UF primeiro";
    if (value.length > 0) return "Adicionar mais...";
    return "Digite para buscar municipio...";
  }, [isDisabled, value.length]);

  return (
    <div className="space-y-3" ref={containerRef}>
      <div className="flex items-center justify-between">
        <label className="block text-base font-semibold text-ink">
          Municipio:{" "}
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
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
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
          disabled={isDisabled}
          aria-label="Buscar municipio"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          aria-controls="municipio-listbox"
          aria-activedescendant={
            highlightedIndex >= 0
              ? `municipio-option-${highlightedIndex}`
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
            id="municipio-listbox"
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
                  : "Nenhum municipio encontrado"}
              </li>
            ) : (
              suggestions.map((municipio, index) => (
                <li
                  key={municipio.codigo}
                  id={`municipio-option-${index}`}
                  role="option"
                  aria-selected={highlightedIndex === index}
                  onClick={() => handleSelect(municipio)}
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
                  <span className="text-sm">{municipio.nome}</span>
                  <span className="text-xs text-ink-muted ml-2">
                    {municipio.uf}
                  </span>
                </li>
              ))
            )}
          </ul>
        )}
      </div>

      {/* Selected Municipalities */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((municipio) => (
            <span
              key={municipio.codigo}
              className="inline-flex items-center gap-1.5 px-3 py-1.5
                         bg-brand-blue-subtle text-brand-navy dark:text-brand-blue
                         rounded-full text-sm font-medium
                         border border-brand-blue/20 animate-fade-in"
            >
              <span>
                {municipio.nome}/{municipio.uf}
              </span>
              <button
                type="button"
                onClick={() => handleRemove(municipio.codigo)}
                className="ml-0.5 p-0.5 rounded-full hover:bg-brand-blue/20 transition-colors"
                aria-label={`Remover ${municipio.nome}`}
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
        Deixe vazio para buscar em todos os municipios das UFs selecionadas
      </p>
    </div>
  );
}
