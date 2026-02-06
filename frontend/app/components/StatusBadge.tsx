"use client";

/**
 * StatusBadge Component
 *
 * Reusable badge for displaying licitacao status with appropriate colors and icons.
 * Supports: aberta (green), em_julgamento (yellow), encerrada (red), suspensa (gray)
 *
 * Based on specification from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 */

export type LicitacaoStatus =
  | "aberta"
  | "recebendo_proposta"
  | "em_julgamento"
  | "encerrada"
  | "suspensa"
  | "cancelada";

interface StatusBadgeProps {
  status: LicitacaoStatus | string;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
  className?: string;
}

// Status configuration with colors, labels, and icons
const STATUS_CONFIG: Record<
  string,
  {
    label: string;
    bgColor: string;
    textColor: string;
    borderColor: string;
    icon: "circle" | "clock" | "check" | "x" | "pause";
  }
> = {
  aberta: {
    label: "Aberta",
    bgColor: "bg-success-subtle",
    textColor: "text-success",
    borderColor: "border-success/30",
    icon: "circle",
  },
  recebendo_proposta: {
    label: "Recebendo Propostas",
    bgColor: "bg-success-subtle",
    textColor: "text-success",
    borderColor: "border-success/30",
    icon: "circle",
  },
  em_julgamento: {
    label: "Em Julgamento",
    bgColor: "bg-warning-subtle",
    textColor: "text-warning",
    borderColor: "border-warning/30",
    icon: "clock",
  },
  encerrada: {
    label: "Encerrada",
    bgColor: "bg-error-subtle",
    textColor: "text-error",
    borderColor: "border-error/30",
    icon: "check",
  },
  suspensa: {
    label: "Suspensa",
    bgColor: "bg-surface-2",
    textColor: "text-ink-muted",
    borderColor: "border-strong",
    icon: "pause",
  },
  cancelada: {
    label: "Cancelada",
    bgColor: "bg-surface-2",
    textColor: "text-ink-muted",
    borderColor: "border-strong",
    icon: "x",
  },
};

// Fallback for unknown status
const DEFAULT_CONFIG = {
  label: "Desconhecido",
  bgColor: "bg-surface-2",
  textColor: "text-ink-muted",
  borderColor: "border-strong",
  icon: "circle" as const,
};

// SVG Icons
function CircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="currentColor"
      viewBox="0 0 8 8"
      aria-hidden="true"
    >
      <circle cx="4" cy="4" r="3" />
    </svg>
  );
}

function ClockIcon({ className }: { className?: string }) {
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
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
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
        d="M5 13l4 4L19 7"
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
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  );
}

function PauseIcon({ className }: { className?: string }) {
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
        d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

const ICON_COMPONENTS = {
  circle: CircleIcon,
  clock: ClockIcon,
  check: CheckIcon,
  x: XIcon,
  pause: PauseIcon,
};

// Size configurations
const SIZE_CLASSES = {
  sm: {
    padding: "px-2 py-0.5",
    text: "text-xs",
    icon: "w-2 h-2",
    gap: "gap-1",
  },
  md: {
    padding: "px-2.5 py-1",
    text: "text-sm",
    icon: "w-3 h-3",
    gap: "gap-1.5",
  },
  lg: {
    padding: "px-3 py-1.5",
    text: "text-base",
    icon: "w-4 h-4",
    gap: "gap-2",
  },
};

export function StatusBadge({
  status,
  size = "md",
  showIcon = true,
  className = "",
}: StatusBadgeProps) {
  // Normalize status to lowercase for lookup
  const normalizedStatus = status.toLowerCase().replace(/\s+/g, "_");
  const config = STATUS_CONFIG[normalizedStatus] || DEFAULT_CONFIG;
  const sizeClasses = SIZE_CLASSES[size];
  const IconComponent = ICON_COMPONENTS[config.icon];

  return (
    <span
      className={`
        inline-flex items-center ${sizeClasses.gap} ${sizeClasses.padding}
        ${config.bgColor} ${config.textColor}
        border ${config.borderColor}
        rounded-full font-medium ${sizeClasses.text}
        ${className}
      `}
      role="status"
      aria-label={`Status: ${config.label}`}
    >
      {showIcon && <IconComponent className={sizeClasses.icon} />}
      <span>{config.label}</span>
    </span>
  );
}

/**
 * Utility function to parse status from PNCP API response
 * Maps various status strings to our standardized status type
 */
export function parseStatus(rawStatus: string | null | undefined): LicitacaoStatus {
  if (!rawStatus) return "aberta";

  const normalized = rawStatus.toLowerCase().trim();

  if (
    normalized.includes("recebendo") ||
    normalized.includes("aberta") ||
    normalized.includes("aberto")
  ) {
    return "recebendo_proposta";
  }

  if (
    normalized.includes("julgamento") ||
    normalized.includes("analise") ||
    normalized.includes("avaliacao")
  ) {
    return "em_julgamento";
  }

  if (
    normalized.includes("encerrad") ||
    normalized.includes("homologad") ||
    normalized.includes("adjudicad") ||
    normalized.includes("finaliz")
  ) {
    return "encerrada";
  }

  if (normalized.includes("suspens")) {
    return "suspensa";
  }

  if (normalized.includes("cancel") || normalized.includes("revogad")) {
    return "cancelada";
  }

  // Default to aberta if unknown
  return "aberta";
}

export { STATUS_CONFIG };
