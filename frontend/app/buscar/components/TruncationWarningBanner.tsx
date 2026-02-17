"use client";

/**
 * GTM-FIX-004: Warning banner shown when PNCP search results are truncated
 * due to hitting the max_pages limit (500 pages = ~250,000 records per UF).
 */

interface TruncationWarningBannerProps {
  truncatedUfs?: string[];
}

export function TruncationWarningBanner({ truncatedUfs }: TruncationWarningBannerProps) {
  const ufsText = truncatedUfs && truncatedUfs.length > 0
    ? truncatedUfs.join(", ")
    : null;

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
            {ufsText
              ? `Sua busca retornou mais registros do que o limite para ${ufsText}. `
              : "Sua busca retornou mais de 250.000 registros do PNCP. "}
            Para garantir análise completa, refine os filtros (selecione menos
            UFs, reduza o período, ou ajuste a faixa de valores).
          </p>
        </div>
      </div>
    </div>
  );
}
