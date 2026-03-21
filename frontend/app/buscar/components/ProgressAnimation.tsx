/**
 * ProgressAnimation — Header spinner + "Analisando oportunidades..." label.
 * Extracted from EnhancedLoadingProgress. DEBT-FE-014.
 */

interface ProgressAnimationProps {
  isDegraded?: boolean;
}

export function ProgressAnimation({ isDegraded = false }: ProgressAnimationProps) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <svg
        className={`animate-spin h-6 w-6 ${isDegraded ? "text-amber-500" : "text-brand-blue"}`}
        viewBox="0 0 24 24"
        aria-hidden="true"
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
      <p className="text-base sm:text-lg font-semibold text-ink">
        Analisando oportunidades...
      </p>
    </div>
  );
}
