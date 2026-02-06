"use client";

import { useState, useRef, useEffect } from "react";

/**
 * OrdenacaoSelect Component
 *
 * Dropdown select for sorting search results.
 * Follows the same pattern as CustomSelect for consistency.
 *
 * Options:
 * - Mais recente (data_desc) - default
 * - Mais antigo (data_asc)
 * - Maior valor (valor_desc)
 * - Menor valor (valor_asc)
 * - Prazo mais proximo (prazo_asc)
 * - Relevancia (relevancia)
 *
 * Based on specification from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 */

export type OrdenacaoOption =
  | "data_desc"
  | "data_asc"
  | "valor_desc"
  | "valor_asc"
  | "prazo_asc"
  | "relevancia";

interface OrdenacaoItem {
  value: OrdenacaoOption;
  label: string;
  description: string;
}

const ORDENACAO_OPTIONS: OrdenacaoItem[] = [
  {
    value: "data_desc",
    label: "Mais recente",
    description: "Data de publicacao decrescente",
  },
  {
    value: "data_asc",
    label: "Mais antigo",
    description: "Data de publicacao crescente",
  },
  {
    value: "valor_desc",
    label: "Maior valor",
    description: "Valor estimado decrescente",
  },
  {
    value: "valor_asc",
    label: "Menor valor",
    description: "Valor estimado crescente",
  },
  {
    value: "prazo_asc",
    label: "Prazo mais proximo",
    description: "Data de abertura crescente",
  },
  {
    value: "relevancia",
    label: "Relevancia",
    description: "Score de matching com termos de busca",
  },
];

// SVG Icons for each option
function ArrowDownIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19 14l-7 7m0 0l-7-7m7 7V3"
      />
    </svg>
  );
}

function ArrowUpIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 10l7-7m0 0l7 7m-7-7v18"
      />
    </svg>
  );
}

function DollarIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
      />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
      />
    </svg>
  );
}

const ORDENACAO_ICONS: Record<
  OrdenacaoOption,
  React.ComponentType<{ className?: string }>
> = {
  data_desc: ArrowDownIcon,
  data_asc: ArrowUpIcon,
  valor_desc: DollarIcon,
  valor_asc: DollarIcon,
  prazo_asc: CalendarIcon,
  relevancia: SparklesIcon,
};

interface OrdenacaoSelectProps {
  value: OrdenacaoOption;
  onChange: (value: OrdenacaoOption) => void;
  disabled?: boolean;
}

export function OrdenacaoSelect({
  value,
  onChange,
  disabled = false,
}: OrdenacaoSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const selectedOption = ORDENACAO_OPTIONS.find((opt) => opt.value === value);
  const SelectedIcon = selectedOption
    ? ORDENACAO_ICONS[selectedOption.value]
    : null;

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
      const currentIndex = ORDENACAO_OPTIONS.findIndex(
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
          onChange(ORDENACAO_OPTIONS[highlightedIndex].value);
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
            Math.min(prev + 1, ORDENACAO_OPTIONS.length - 1)
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

      case "Home":
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex(0);
        }
        break;

      case "End":
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex(ORDENACAO_OPTIONS.length - 1);
        }
        break;

      case "Tab":
        if (isOpen) {
          setIsOpen(false);
        }
        break;
    }
  };

  const handleOptionClick = (optionValue: OrdenacaoOption) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      <label className="block text-sm font-medium text-ink-secondary mb-1.5">
        Ordenar por:
      </label>

      {/* Select Button */}
      <button
        type="button"
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls="ordenacao-listbox"
        aria-activedescendant={
          isOpen && highlightedIndex >= 0
            ? `ordenacao-option-${highlightedIndex}`
            : undefined
        }
        disabled={disabled}
        onKeyDown={handleKeyDown}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`
          w-full min-w-[180px] border border-strong rounded-input px-3 py-2.5 text-sm text-left
          bg-surface-0 text-ink
          focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue
          disabled:bg-surface-1 disabled:text-ink-muted disabled:cursor-not-allowed
          transition-colors flex items-center justify-between gap-2
        `}
      >
        <div className="flex items-center gap-2">
          {SelectedIcon && (
            <SelectedIcon className="w-4 h-4 text-ink-muted flex-shrink-0" />
          )}
          <span className={selectedOption ? "text-ink" : "text-ink-muted"}>
            {selectedOption?.label || "Selecionar..."}
          </span>
        </div>
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
          id="ordenacao-listbox"
          role="listbox"
          className="absolute z-50 w-full mt-1 bg-surface-0 border border-strong rounded-input shadow-lg
                     max-h-60 overflow-auto animate-fade-in"
        >
          {ORDENACAO_OPTIONS.map((option, index) => {
            const Icon = ORDENACAO_ICONS[option.value];
            return (
              <li
                key={option.value}
                id={`ordenacao-option-${index}`}
                role="option"
                aria-selected={option.value === value}
                onClick={() => handleOptionClick(option.value)}
                onMouseEnter={() => setHighlightedIndex(index)}
                className={`
                  px-3 py-2.5 cursor-pointer transition-colors
                  ${
                    highlightedIndex === index
                      ? "bg-brand-blue-subtle text-brand-navy"
                      : option.value === value
                      ? "bg-surface-1 text-brand-blue font-medium"
                      : "text-ink hover:bg-surface-1"
                  }
                `}
              >
                <div className="flex items-center gap-2">
                  <Icon
                    className={`w-4 h-4 flex-shrink-0 ${
                      highlightedIndex === index || option.value === value
                        ? "text-brand-blue"
                        : "text-ink-muted"
                    }`}
                  />
                  <div className="flex flex-col">
                    <span className="text-sm">{option.label}</span>
                    <span className="text-xs text-ink-muted">
                      {option.description}
                    </span>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export { ORDENACAO_OPTIONS };
