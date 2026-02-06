"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useDebouncedCallback } from "use-debounce";

/**
 * MunicipioFilter Component
 *
 * Autocomplete filter for municipality selection using IBGE API.
 * Based on specs from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 *
 * Features:
 * - Search field with autocomplete
 * - Fetches from IBGE API: https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios
 * - 300ms debounce on search
 * - Multi-select with badges
 * - Disabled when no UF is selected
 * - Results limited to 20
 * - Full keyboard accessibility
 * - ARIA compliant
 * - Visual consistency with design system
 */

export interface Municipio {
  codigo: string; // IBGE code
  nome: string;
  uf: string;
}

export interface MunicipioFilterProps {
  ufs: string[]; // Selected UFs
  value: Municipio[];
  onChange: (municipios: Municipio[]) => void;
  disabled?: boolean;
}

// Icon components inline to avoid external dependencies
function SearchIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>
  );
}

function LoaderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={`animate-spin ${className}`}
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  );
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

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fetch municipalities from IBGE API with debounce
  const searchMunicipios = useDebouncedCallback(async (term: string) => {
    if (term.length < 2 || ufs.length === 0) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      // Fetch in parallel for all selected UFs
      const promises = ufs.map(async (uf) => {
        const response = await fetch(
          `https://servicodados.ibge.gov.br/api/v1/localidades/estados/${uf}/municipios`
        );

        if (!response.ok) {
          console.error(`Error fetching municipalities for ${uf}: ${response.status}`);
          return [];
        }

        const data = await response.json();
        return data
          .filter((m: { nome: string }) =>
            m.nome.toLowerCase().includes(term.toLowerCase())
          )
          .map((m: { id: number; nome: string }) => ({
            codigo: m.id.toString(),
            nome: m.nome,
            uf: uf,
          }));
      });

      const results = await Promise.all(promises);
      const flattened = results.flat();

      // Remove duplicates and sort
      const unique = flattened.filter(
        (m, i, arr) => arr.findIndex((x) => x.codigo === m.codigo) === i
      );
      unique.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));

      setSuggestions(unique.slice(0, 20)); // Limit to 20 results
    } catch (error) {
      console.error("Error fetching municipalities:", error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, 300);

  // Trigger search when term or UFs change
  useEffect(() => {
    searchMunicipios(search);
  }, [search, ufs, searchMunicipios]);

  // Reset search when UFs change (municipalities may no longer be valid)
  useEffect(() => {
    // Remove selected municipalities that are no longer in selected UFs
    const validMunicipios = value.filter((m) => ufs.includes(m.uf));
    if (validMunicipios.length !== value.length) {
      onChange(validMunicipios);
    }
  }, [ufs, value, onChange]);

  const handleSelect = useCallback(
    (municipio: Municipio) => {
      if (!value.find((m) => m.codigo === municipio.codigo)) {
        onChange([...value, municipio]);
      }
      setSearch("");
      setIsOpen(false);
      setHighlightedIndex(-1);
      inputRef.current?.focus();
    },
    [value, onChange]
  );

  const handleRemove = useCallback(
    (codigo: string) => {
      onChange(value.filter((m) => m.codigo !== codigo));
    },
    [value, onChange]
  );

  const handleClearAll = useCallback(() => {
    onChange([]);
  }, [onChange]);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (!isOpen) {
      if (event.key === "ArrowDown" || event.key === "Enter") {
        setIsOpen(true);
      }
      return;
    }

    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        setHighlightedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case "ArrowUp":
        event.preventDefault();
        setHighlightedIndex((prev) =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case "Enter":
        event.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
          handleSelect(suggestions[highlightedIndex]);
        }
        break;
      case "Escape":
        event.preventDefault();
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
    }
  };

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const item = listRef.current.children[highlightedIndex] as HTMLElement;
      if (item) {
        item.scrollIntoView({ block: "nearest" });
      }
    }
  }, [highlightedIndex]);

  const isDisabled = disabled || ufs.length === 0;

  return (
    <div className="space-y-3" ref={containerRef}>
      {/* Header with label and clear button */}
      <div className="flex items-center justify-between">
        <label className="text-base font-semibold text-ink">
          Municipio: <span className="text-ink-muted font-normal">(opcional)</span>
        </label>
        {value.length > 0 && (
          <button
            type="button"
            onClick={handleClearAll}
            disabled={disabled}
            className={`
              text-sm text-ink-muted hover:text-ink transition-colors
              ${disabled ? "opacity-50 cursor-not-allowed" : "hover:underline"}
            `}
          >
            Limpar todos
          </button>
        )}
      </div>

      {/* Search input with autocomplete dropdown */}
      <div className="relative">
        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-muted" />
          <input
            ref={inputRef}
            type="text"
            placeholder={
              isDisabled
                ? "Selecione uma UF primeiro"
                : "Digite para buscar municipio..."
            }
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setIsOpen(true);
              setHighlightedIndex(-1);
            }}
            onFocus={() => search.length >= 2 && setIsOpen(true)}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            aria-expanded={isOpen}
            aria-haspopup="listbox"
            aria-controls="municipio-listbox"
            aria-autocomplete="list"
            className={`
              w-full border border-strong rounded-input pl-10 pr-10 py-2.5 text-sm
              bg-surface-0 text-ink placeholder:text-ink-muted
              focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue
              disabled:bg-surface-1 disabled:text-ink-muted disabled:cursor-not-allowed
              transition-colors
            `}
          />
          {loading && (
            <LoaderIcon className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-muted" />
          )}
        </div>

        {/* Dropdown suggestions */}
        {isOpen && (search.length >= 2 || suggestions.length > 0) && (
          <div className="absolute z-50 w-full mt-1 bg-surface-0 border border-strong rounded-card shadow-lg max-h-60 overflow-hidden">
            {suggestions.length === 0 ? (
              <div className="px-4 py-3 text-sm text-ink-muted">
                {loading
                  ? "Buscando..."
                  : search.length < 2
                  ? "Digite pelo menos 2 caracteres"
                  : "Nenhum municipio encontrado"}
              </div>
            ) : (
              <ul
                ref={listRef}
                id="municipio-listbox"
                role="listbox"
                aria-label="Municipios"
                className="max-h-60 overflow-y-auto"
              >
                {suggestions.map((municipio, index) => {
                  const isAlreadySelected = value.some(
                    (m) => m.codigo === municipio.codigo
                  );
                  const isHighlighted = index === highlightedIndex;

                  return (
                    <li
                      key={municipio.codigo}
                      role="option"
                      aria-selected={isAlreadySelected}
                      aria-disabled={isAlreadySelected}
                      onClick={() => !isAlreadySelected && handleSelect(municipio)}
                      onMouseEnter={() => setHighlightedIndex(index)}
                      className={`
                        px-4 py-2.5 text-sm cursor-pointer flex items-center justify-between
                        transition-colors duration-100
                        ${isAlreadySelected ? "opacity-50 cursor-not-allowed" : ""}
                        ${
                          isHighlighted && !isAlreadySelected
                            ? "bg-brand-blue-subtle"
                            : "hover:bg-surface-1"
                        }
                      `}
                    >
                      <span className="text-ink">{municipio.nome}</span>
                      <span className="text-xs text-ink-muted ml-2">
                        {municipio.uf}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* Selected municipalities as badges */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((municipio) => (
            <span
              key={municipio.codigo}
              className="
                inline-flex items-center gap-1.5 px-3 py-1.5
                bg-surface-1 border border-strong rounded-button
                text-sm text-ink
              "
            >
              <span>
                {municipio.nome}/{municipio.uf}
              </span>
              <button
                type="button"
                onClick={() => handleRemove(municipio.codigo)}
                disabled={disabled}
                aria-label={`Remover ${municipio.nome}`}
                className={`
                  p-0.5 rounded-full hover:bg-surface-2 transition-colors
                  focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-inset
                  ${disabled ? "opacity-50 cursor-not-allowed" : ""}
                `}
              >
                <XIcon className="h-3 w-3 text-ink-muted hover:text-ink" />
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
