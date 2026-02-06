"use client";

/**
 * StatusFilter Component
 *
 * Filter component for bid status selection.
 * Based on specs from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 *
 * Features:
 * - 4 radio button options: Abertas, Em Julgamento, Encerradas, Todas
 * - Default: "Abertas" (recebendo_proposta)
 * - "Recomendado" badge on Abertas option
 * - Full keyboard accessibility
 * - ARIA compliant
 * - Visual consistency with design system
 */

export type StatusLicitacao =
  | "recebendo_proposta"
  | "em_julgamento"
  | "encerrada"
  | "todos";

interface StatusOption {
  value: StatusLicitacao;
  label: string;
  description: string;
  badge?: { text: string };
}

const STATUS_OPTIONS: StatusOption[] = [
  {
    value: "recebendo_proposta",
    label: "Abertas",
    description: "Licitacoes que ainda aceitam propostas",
    badge: { text: "Recomendado" },
  },
  {
    value: "em_julgamento",
    label: "Em Julgamento",
    description: "Propostas encerradas, em analise pelo orgao",
  },
  {
    value: "encerrada",
    label: "Encerradas",
    description: "Processo finalizado",
  },
  {
    value: "todos",
    label: "Todas",
    description: "Exibir todas independente do status",
  },
];

export interface StatusFilterProps {
  value: StatusLicitacao;
  onChange: (value: StatusLicitacao) => void;
  disabled?: boolean;
}

export function StatusFilter({
  value,
  onChange,
  disabled = false,
}: StatusFilterProps) {
  const handleKeyDown = (
    event: React.KeyboardEvent,
    optionValue: StatusLicitacao
  ) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (!disabled) {
        onChange(optionValue);
      }
    }
  };

  return (
    <div className="space-y-3">
      {/* Label with tooltip icon */}
      <div className="flex items-center gap-2">
        <label className="text-base font-semibold text-ink">
          Status da Licitacao:
        </label>
        <span
          className="text-ink-muted cursor-help"
          title="Filtre por licitacoes abertas para enviar propostas"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </span>
      </div>

      {/* Radio Group */}
      <div
        role="radiogroup"
        aria-label="Status da licitacao"
        className="grid grid-cols-2 gap-3"
      >
        {STATUS_OPTIONS.map((option) => {
          const isSelected = value === option.value;

          return (
            <div
              key={option.value}
              role="radio"
              aria-checked={isSelected}
              aria-disabled={disabled}
              tabIndex={disabled ? -1 : 0}
              onClick={() => !disabled && onChange(option.value)}
              onKeyDown={(e) => handleKeyDown(e, option.value)}
              title={option.description}
              className={`
                relative flex items-center justify-center gap-2
                rounded-button border-2 p-3 cursor-pointer
                transition-all duration-200 min-h-[48px]
                ${disabled ? "cursor-not-allowed opacity-50" : ""}
                ${
                  isSelected
                    ? "border-brand-blue bg-brand-blue-subtle"
                    : "border-strong bg-surface-0 hover:border-accent hover:bg-surface-1"
                }
                focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2 focus:ring-offset-[var(--canvas)]
              `}
            >
              {/* Radio indicator */}
              <span
                className={`
                  w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0
                  ${
                    isSelected
                      ? "border-brand-blue"
                      : "border-ink-muted"
                  }
                `}
              >
                {isSelected && (
                  <span className="w-2 h-2 rounded-full bg-brand-blue" />
                )}
              </span>

              {/* Label */}
              <span
                className={`font-medium ${
                  isSelected ? "text-brand-navy dark:text-brand-blue" : "text-ink"
                }`}
              >
                {option.label}
              </span>

              {/* Badge */}
              {option.badge && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-success text-white font-medium">
                  {option.badge.text}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Helper text */}
      <p className="text-sm text-ink-muted">
        Dica: "Abertas" mostra licitacoes que ainda aceitam propostas
      </p>
    </div>
  );
}
