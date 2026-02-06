"use client";

/**
 * EsferaFilter Component
 *
 * Filter component for government sphere selection (Federal, Estadual, Municipal).
 * Based on specs from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 *
 * Features:
 * - ToggleGroup with 3 options: Federal, Estadual, Municipal
 * - Icons for each sphere (Building, Building2, Home)
 * - Multi-select support
 * - Counter showing selected count
 * - Full keyboard accessibility
 * - ARIA compliant
 * - Visual consistency with design system
 */

export type Esfera = "F" | "E" | "M";

interface EsferaOption {
  value: Esfera;
  label: string;
  description: string;
}

const ESFERAS: EsferaOption[] = [
  {
    value: "F",
    label: "Federal",
    description: "Uniao, ministerios, autarquias federais",
  },
  {
    value: "E",
    label: "Estadual",
    description: "Estados, secretarias estaduais",
  },
  {
    value: "M",
    label: "Municipal",
    description: "Prefeituras, camaras municipais",
  },
];

export interface EsferaFilterProps {
  value: Esfera[];
  onChange: (esferas: Esfera[]) => void;
  disabled?: boolean;
}

// Icon components inline to avoid external dependencies
function BuildingIcon({ className }: { className?: string }) {
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
        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
      />
    </svg>
  );
}

function Building2Icon({ className }: { className?: string }) {
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
        d="M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z"
      />
    </svg>
  );
}

function HomeIcon({ className }: { className?: string }) {
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
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
      />
    </svg>
  );
}

const ESFERA_ICONS: Record<Esfera, React.ComponentType<{ className?: string }>> = {
  F: BuildingIcon,
  E: Building2Icon,
  M: HomeIcon,
};

export function EsferaFilter({
  value,
  onChange,
  disabled = false,
}: EsferaFilterProps) {
  const handleToggle = (esfera: Esfera) => {
    if (disabled) return;

    if (value.includes(esfera)) {
      onChange(value.filter((e) => e !== esfera));
    } else {
      onChange([...value, esfera]);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent, esfera: Esfera) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleToggle(esfera);
    }
  };

  return (
    <div className="space-y-3">
      {/* Label */}
      <label className="text-base font-semibold text-ink">
        Esfera Governamental:
      </label>

      {/* Toggle Group */}
      <div
        role="group"
        aria-label="Esfera governamental"
        className="flex flex-wrap gap-3"
      >
        {ESFERAS.map((esfera) => {
          const Icon = ESFERA_ICONS[esfera.value];
          const isSelected = value.includes(esfera.value);

          return (
            <div
              key={esfera.value}
              role="checkbox"
              aria-checked={isSelected}
              aria-disabled={disabled}
              aria-label={esfera.label}
              tabIndex={disabled ? -1 : 0}
              onClick={() => handleToggle(esfera.value)}
              onKeyDown={(e) => handleKeyDown(e, esfera.value)}
              title={esfera.description}
              className={`
                flex flex-col items-center gap-1.5 p-3 min-w-[90px]
                border-2 rounded-card cursor-pointer
                transition-all duration-200
                ${disabled ? "cursor-not-allowed opacity-50" : ""}
                ${
                  isSelected
                    ? "border-brand-blue bg-brand-blue-subtle"
                    : "border-strong bg-surface-0 hover:border-accent hover:bg-surface-1"
                }
                focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2 focus:ring-offset-[var(--canvas)]
              `}
            >
              <Icon
                className={`h-5 w-5 ${
                  isSelected ? "text-brand-blue" : "text-ink-muted"
                }`}
              />
              <span
                className={`text-sm font-medium ${
                  isSelected ? "text-brand-navy dark:text-brand-blue" : "text-ink"
                }`}
              >
                {esfera.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Counter */}
      {value.length > 0 && (
        <p className="text-sm text-ink-muted">
          {value.length}{" "}
          {value.length === 1 ? "esfera selecionada" : "esferas selecionadas"}
        </p>
      )}
    </div>
  );
}

export { ESFERAS };
