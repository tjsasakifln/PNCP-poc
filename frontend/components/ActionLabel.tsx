import React from "react";

interface ActionLabelProps {
  acao_recomendada?: string | null;
}

type ActionConfig = {
  label: string;
  colorClasses: string;
  icon: React.ReactNode;
};

/**
 * STORY-259: Label showing the recommended action for a bid.
 * - "PARTICIPAR" — green badge with check icon
 * - "AVALIAR COM CAUTELA" — yellow badge with alert icon
 * - "NÃO PARTICIPAR" — gray badge with X icon
 */
export default function ActionLabel({ acao_recomendada }: ActionLabelProps) {
  if (!acao_recomendada) return null;

  const normalized = acao_recomendada
    .toUpperCase()
    .trim()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

  const configs: Record<string, ActionConfig> = {
    PARTICIPAR: {
      label: "PARTICIPAR",
      colorClasses:
        "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
      icon: (
        <svg
          className="w-3 h-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2.5}
            d="M5 13l4 4L19 7"
          />
        </svg>
      ),
    },
    "AVALIAR COM CAUTELA": {
      label: "AVALIAR COM CAUTELA",
      colorClasses:
        "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
      icon: (
        <svg
          className="w-3 h-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      ),
    },
    "NAO PARTICIPAR": {
      label: "NÃO PARTICIPAR",
      colorClasses:
        "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
      icon: (
        <svg
          className="w-3 h-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2.5}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      ),
    },
  };

  // Attempt exact match first, then partial match
  const config =
    configs[normalized] ??
    configs[
      Object.keys(configs).find((k) => normalized.includes(k)) ?? ""
    ];

  if (!config) return null;

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wide ${config.colorClasses}`}
      aria-label={`Ação recomendada: ${config.label}`}
      role="img"
      data-testid="action-label"
      data-action={normalized}
    >
      {config.icon}
      {config.label}
    </span>
  );
}
