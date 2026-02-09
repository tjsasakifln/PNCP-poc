"use client";

import { useMemo } from "react";

/**
 * EsferaFilter Component
 *
 * Filter for government spheres (Federal, Estadual, Municipal).
 * Allows multi-selection with toggle buttons and visual icons.
 *
 * Based on specification from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
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

// SVG Icons for each sphere
function BuildingIcon({ className }: { className?: string }) {
  return (
    <svg
              role="img"
              aria-label="Ícone"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.5}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z"
      />
    </svg>
  );
}

function Building2Icon({ className }: { className?: string }) {
  return (
    <svg
              role="img"
              aria-label="Ícone"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.5}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z"
      />
    </svg>
  );
}

function HomeIcon({ className }: { className?: string }) {
  return (
    <svg
              role="img"
              aria-label="Ícone"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.5}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"
      />
    </svg>
  );
}

const ESFERA_ICONS: Record<Esfera, React.ComponentType<{ className?: string }>> = {
  F: BuildingIcon,
  E: Building2Icon,
  M: HomeIcon,
};

interface EsferaFilterProps {
  value: Esfera[];
  onChange: (esferas: Esfera[]) => void;
  disabled?: boolean;
}

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

  const selectedCount = value.length;

  const countLabel = useMemo(() => {
    if (selectedCount === 0) return null;
    if (selectedCount === 1) return "1 esfera selecionada";
    return `${selectedCount} esferas selecionadas`;
  }, [selectedCount]);

  return (
    <div className="space-y-3">
      <label className="block text-base font-semibold text-ink">
        Esfera Governamental:
      </label>

      <div className="flex flex-wrap gap-3" role="group" aria-label="Selecionar esferas governamentais">
        {ESFERAS.map((esfera) => {
          const Icon = ESFERA_ICONS[esfera.value];
          const isSelected = value.includes(esfera.value);

          return (
            <button
              key={esfera.value}
              type="button"
              onClick={() => handleToggle(esfera.value)}
              disabled={disabled}
              title={esfera.description}
              aria-pressed={isSelected}
              aria-label={`${esfera.label}: ${esfera.description}`}
              className={`
                flex flex-col items-center gap-1.5 p-3 min-w-[90px]
                border-2 rounded-button transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2
                disabled:opacity-50 disabled:cursor-not-allowed
                ${
                  isSelected
                    ? "border-brand-blue bg-brand-blue-subtle text-brand-navy dark:text-brand-blue"
                    : "border-strong bg-surface-0 text-ink-secondary hover:border-accent hover:text-brand-blue hover:bg-surface-1"
                }
              `}
            >
              <Icon
                className={`h-6 w-6 ${
                  isSelected ? "text-brand-blue" : "text-ink-muted"
                }`}
              />
              <span className="text-sm font-medium">{esfera.label}</span>
            </button>
          );
        })}
      </div>

      {countLabel && (
        <p className="text-sm text-ink-muted">{countLabel}</p>
      )}
    </div>
  );
}

export { ESFERAS };
