"use client";

import { useState, useRef, useEffect } from "react";

/**
 * PaginacaoSelect Component
 *
 * Dropdown select for configuring items per page in search results.
 *
 * Options:
 * - 10 items per page
 * - 20 items per page (default)
 * - 50 items per page
 * - 100 items per page
 *
 * Based on specification from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md (Section 8)
 */

export type PaginacaoOption = 10 | 20 | 50 | 100;

interface PaginacaoItem {
  value: PaginacaoOption;
  label: string;
}

const PAGINACAO_OPTIONS: PaginacaoItem[] = [
  { value: 10, label: "10 por pagina" },
  { value: 20, label: "20 por pagina" },
  { value: 50, label: "50 por pagina" },
  { value: 100, label: "100 por pagina" },
];

interface PaginacaoSelectProps {
  value: PaginacaoOption;
  onChange: (value: PaginacaoOption) => void;
  disabled?: boolean;
  totalItems?: number;
}

export function PaginacaoSelect({
  value,
  onChange,
  disabled = false,
  totalItems,
}: PaginacaoSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const selectedOption = PAGINACAO_OPTIONS.find((opt) => opt.value === value);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  // Close dropdown on Escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", handleEscapeKey, true);
    return () => window.removeEventListener("keydown", handleEscapeKey, true);
  }, [isOpen]);

  // Reset highlighted index when opening
  useEffect(() => {
    if (isOpen) {
      const currentIndex = PAGINACAO_OPTIONS.findIndex(
        (opt) => opt.value === value
      );
      setHighlightedIndex(currentIndex >= 0 ? currentIndex : 0);
    }
  }, [isOpen, value]);

  // Scroll highlighted option into view
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

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case "Enter":
      case " ":
        event.preventDefault();
        if (isOpen && highlightedIndex >= 0) {
          onChange(PAGINACAO_OPTIONS[highlightedIndex].value);
          setIsOpen(false);
        } else {
          setIsOpen(true);
        }
        break;

      case "Escape":
        event.preventDefault();
        setIsOpen(false);
        break;

      case "ArrowDown":
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex((prev) =>
            Math.min(prev + 1, PAGINACAO_OPTIONS.length - 1)
          );
        }
        break;

      case "ArrowUp":
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex((prev) => Math.max(prev - 1, 0));
        }
        break;

      case "Tab":
        if (isOpen) {
          setIsOpen(false);
        }
        break;
    }
  };

  const handleOptionClick = (optionValue: PaginacaoOption) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative inline-block">
      {/* Select Button */}
      <button
        type="button"
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls="paginacao-listbox"
        aria-label="Itens por pagina"
        disabled={disabled}
        onKeyDown={handleKeyDown}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`
          min-w-[140px] border border-strong rounded-input px-3 py-2 text-sm text-left
          bg-surface-0 text-ink
          focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue
          disabled:bg-surface-1 disabled:text-ink-muted disabled:cursor-not-allowed
          transition-colors flex items-center justify-between gap-2
        `}
      >
        <span className={selectedOption ? "text-ink" : "text-ink-muted"}>
          {selectedOption?.label || "Selecionar..."}
        </span>
        <svg
          className={`w-4 h-4 text-ink-secondary transition-transform duration-200 flex-shrink-0 ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown List */}
      {isOpen && (
        <ul
          ref={listRef}
          id="paginacao-listbox"
          role="listbox"
          className="absolute z-50 w-full mt-1 bg-surface-0 border border-strong rounded-input shadow-lg
                     overflow-auto animate-fade-in"
        >
          {PAGINACAO_OPTIONS.map((option, index) => (
            <li
              key={option.value}
              id={`paginacao-option-${index}`}
              role="option"
              aria-selected={option.value === value}
              onClick={() => handleOptionClick(option.value)}
              onMouseEnter={() => setHighlightedIndex(index)}
              className={`
                px-3 py-2 cursor-pointer transition-colors text-sm
                ${
                  highlightedIndex === index
                    ? "bg-brand-blue-subtle text-brand-navy"
                    : option.value === value
                    ? "bg-surface-1 text-brand-blue font-medium"
                    : "text-ink hover:bg-surface-1"
                }
              `}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}

      {/* Total items indicator */}
      {totalItems !== undefined && totalItems > 0 && (
        <span className="ml-2 text-xs text-ink-muted">
          de {totalItems.toLocaleString("pt-BR")} resultados
        </span>
      )}
    </div>
  );
}

/**
 * Pagination Controls Component
 *
 * Complete pagination controls with page navigation and items per page selector.
 */
interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  itemsPerPage: PaginacaoOption;
  totalItems: number;
  onPageChange: (page: number) => void;
  onItemsPerPageChange: (items: PaginacaoOption) => void;
  disabled?: boolean;
}

export function PaginationControls({
  currentPage,
  totalPages,
  itemsPerPage,
  totalItems,
  onPageChange,
  onItemsPerPageChange,
  disabled = false,
}: PaginationControlsProps) {
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-4">
      {/* Items per page selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-ink-secondary">Exibir:</span>
        <PaginacaoSelect
          value={itemsPerPage}
          onChange={onItemsPerPageChange}
          disabled={disabled}
        />
      </div>

      {/* Results info */}
      <div className="text-sm text-ink-secondary">
        Exibindo {startItem.toLocaleString("pt-BR")}-{endItem.toLocaleString("pt-BR")} de{" "}
        {totalItems.toLocaleString("pt-BR")} resultados
      </div>

      {/* Page navigation */}
      <div className="flex items-center gap-2">
        {/* First page */}
        <button
          type="button"
          onClick={() => onPageChange(1)}
          disabled={disabled || !canGoPrev}
          className="p-2 rounded-md border border-strong bg-surface-0 text-ink-secondary
                     hover:bg-surface-1 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          aria-label="Primeira pagina"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
            />
          </svg>
        </button>

        {/* Previous page */}
        <button
          type="button"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={disabled || !canGoPrev}
          className="p-2 rounded-md border border-strong bg-surface-0 text-ink-secondary
                     hover:bg-surface-1 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          aria-label="Pagina anterior"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>

        {/* Page indicator */}
        <span className="px-3 py-1 text-sm font-medium text-ink">
          {currentPage} / {totalPages}
        </span>

        {/* Next page */}
        <button
          type="button"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={disabled || !canGoNext}
          className="p-2 rounded-md border border-strong bg-surface-0 text-ink-secondary
                     hover:bg-surface-1 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          aria-label="Proxima pagina"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>

        {/* Last page */}
        <button
          type="button"
          onClick={() => onPageChange(totalPages)}
          disabled={disabled || !canGoNext}
          className="p-2 rounded-md border border-strong bg-surface-0 text-ink-secondary
                     hover:bg-surface-1 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          aria-label="Ultima pagina"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M13 5l7 7-7 7M5 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

export { PAGINACAO_OPTIONS };
