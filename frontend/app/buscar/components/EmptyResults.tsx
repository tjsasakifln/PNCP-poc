"use client";

interface EmptyResultsProps {
  totalRaw?: number;
  sectorName?: string;
  ufCount?: number;
  onScrollToTop?: () => void;
}

export function EmptyResults({
  totalRaw = 0,
  sectorName,
  ufCount = 0,
  onScrollToTop,
}: EmptyResultsProps) {
  return (
    <div
      className="mt-6 sm:mt-8 animate-fade-in-up"
      data-testid="empty-results"
      aria-live="polite"
    >
      <div className="text-center py-10 px-4">
        {/* AC1: Icon */}
        <div className="mx-auto mb-4 w-14 h-14 flex items-center justify-center rounded-full bg-[var(--surface-1)]">
          <svg
            aria-hidden="true"
            className="w-7 h-7 text-[var(--ink-muted)]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m5.231 13.481L15 17.25m-4.5-15H5.625c-.621 0-1.125.504-1.125 1.125v16.5c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9zm3.75 11.625a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
            />
          </svg>
        </div>

        {/* AC1: Friendly message */}
        <h3 className="text-lg font-display font-semibold text-[var(--ink)] mb-2">
          Nenhum resultado compatível
        </h3>
        <p
          className="text-sm text-[var(--ink-secondary)] mb-6 max-w-md mx-auto"
          data-testid="empty-results-message"
        >
          {totalRaw > 0 ? (
            <>
              Encontramos{" "}
              <span className="font-semibold text-[var(--ink)]">
                {totalRaw.toLocaleString("pt-BR")}
              </span>{" "}
              licitações, mas nenhuma passou nos filtros
              {sectorName ? (
                <>
                  {" "}
                  para{" "}
                  <span className="font-medium">{sectorName}</span>
                </>
              ) : null}
              .
            </>
          ) : (
            <>
              Nenhuma licitação encontrada
              {sectorName ? (
                <>
                  {" "}
                  para{" "}
                  <span className="font-medium">{sectorName}</span>
                </>
              ) : null}
              {ufCount > 0 ? (
                <>
                  {" "}
                  em {ufCount} {ufCount === 1 ? "estado" : "estados"}
                </>
              ) : null}
              . Tente ajustar sua busca.
            </>
          )}
        </p>

        {/* AC2: Contextual suggestions */}
        <div className="text-left max-w-sm mx-auto mb-6 p-4 bg-[var(--surface-1)] rounded-card border border-[var(--border)]">
          <p className="text-sm font-semibold text-[var(--ink)] mb-3 flex items-center gap-2">
            <svg
              className="w-4 h-4 text-[var(--brand-blue)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            Sugestões para melhorar a busca:
          </p>
          <ul className="text-sm text-[var(--ink-secondary)] space-y-2">
            <li
              className="flex items-start gap-2"
              data-testid="suggestion-remover-uf"
            >
              <span className="text-[var(--brand-blue)] mt-0.5">•</span>
              <span>
                <strong>Remover filtros de UF</strong> — Selecione mais estados
                ou use &quot;Selecionar todos&quot;
              </span>
            </li>
            <li
              className="flex items-start gap-2"
              data-testid="suggestion-termos-genericos"
            >
              <span className="text-[var(--brand-blue)] mt-0.5">•</span>
              <span>
                <strong>Usar termos genéricos</strong> — Palavras mais amplas
                aumentam as chances de encontrar editais
              </span>
            </li>
          </ul>
        </div>

        {/* Action button */}
        {onScrollToTop && (
          <button
            onClick={onScrollToTop}
            className="px-5 py-2.5 bg-[var(--brand-navy)] text-white rounded-button text-sm font-medium
                       hover:bg-[var(--brand-blue)] transition-colors"
            data-testid="empty-results-adjust"
          >
            Ajustar critérios de busca
          </button>
        )}
      </div>
    </div>
  );
}
