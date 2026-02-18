"use client";

/**
 * GTM-FIX-004: Warning banner shown when search results are truncated
 * due to hitting the max_pages limit on one or more data sources.
 *
 * AC6 revised: Shows which specific source(s) were truncated when
 * truncation_details is provided (PNCP, Portal de Compras, or both).
 */

/** Human-readable source names for display */
const SOURCE_DISPLAY_NAMES: Record<string, string> = {
  pncp: "PNCP",
  portal_compras: "Portal de Compras Publicas",
  compras_gov: "Compras.gov.br",
};

interface TruncationWarningBannerProps {
  truncatedUfs?: string[];
  /** Per-source truncation flags, e.g. { pncp: true, portal_compras: false } */
  truncationDetails?: Record<string, boolean>;
}

export function TruncationWarningBanner({
  truncatedUfs,
  truncationDetails,
}: TruncationWarningBannerProps) {
  const ufsText = truncatedUfs && truncatedUfs.length > 0
    ? truncatedUfs.join(", ")
    : null;

  // Determine which sources were truncated
  const truncatedSources: string[] = [];
  if (truncationDetails) {
    for (const [source, wasTruncated] of Object.entries(truncationDetails)) {
      if (wasTruncated) {
        truncatedSources.push(SOURCE_DISPLAY_NAMES[source] || source);
      }
    }
  }

  // Build the description text based on available information
  let description: string;
  if (truncatedSources.length > 1) {
    // Multiple sources truncated
    description = `Resultados truncados em ${truncatedSources.join(" e ")}. `;
  } else if (truncatedSources.length === 1) {
    // Single source truncated
    if (ufsText) {
      description = `Resultados do ${truncatedSources[0]} truncados para ${ufsText}. `;
    } else {
      description = `Resultados do ${truncatedSources[0]} atingiram o limite de registros. `;
    }
  } else if (ufsText) {
    // Legacy: no truncation_details but UFs provided
    description = `Sua busca retornou mais registros do que o limite para ${ufsText}. `;
  } else {
    // Generic fallback
    description = "Sua busca retornou mais de 250.000 registros do PNCP. ";
  }

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <svg
          className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          role="img"
          aria-label="Alerta"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
        <div>
          <h3 className="font-semibold text-yellow-900 dark:text-yellow-100">
            Resultados truncados
          </h3>
          <p className="text-sm text-yellow-800 dark:text-yellow-200 mt-1">
            {description}
            Para garantir análise completa, refine os filtros (selecione menos
            UFs, reduza o período, ou ajuste a faixa de valores).
          </p>
        </div>
      </div>
    </div>
  );
}
