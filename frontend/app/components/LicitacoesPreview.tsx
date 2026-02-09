"use client";

import type { LicitacaoItem } from "../types";

interface LicitacoesPreviewProps {
  /** List of bid items to display */
  licitacoes: LicitacaoItem[];
  /** Number of items to show fully (rest will be blurred) */
  previewCount?: number;
  /** Whether Excel export is available for user's plan */
  excelAvailable: boolean;
  /** Callback when user clicks upgrade CTA */
  onUpgradeClick?: () => void;
}

/**
 * LicitacoesPreview - Displays bid items with FREE tier blur effect.
 *
 * Shows first N items fully with links, rest are blurred without links
 * to encourage upgrade to paid plans.
 */
export function LicitacoesPreview({
  licitacoes,
  previewCount = 5,
  excelAvailable,
  onUpgradeClick,
}: LicitacoesPreviewProps) {
  if (!licitacoes || licitacoes.length === 0) {
    return null;
  }

  const visibleItems = licitacoes.slice(0, previewCount);
  const blurredItems = licitacoes.slice(previewCount);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-";
    const [year, month, day] = dateStr.split("-");
    return `${day}/${month}/${year}`;
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-ink flex items-center gap-2">
        <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5 text-brand-navy" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        Oportunidades Encontradas
      </h3>

      {/* Visible items with full info */}
      <div className="space-y-3">
        {visibleItems.map((item, index) => (
          <div
            key={item.pncp_id || index}
            className="p-4 bg-surface-0 border border-strong rounded-card hover:border-brand-blue transition-colors"
          >
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
              <div className="flex-1 min-w-0">
                <h4 className="text-base font-medium text-ink line-clamp-2 mb-1">
                  {item.objeto}
                </h4>
                <p className="text-sm text-ink-secondary truncate">
                  {item.orgao}
                </p>
                <div className="flex flex-wrap gap-2 mt-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-brand-blue-subtle text-brand-navy text-xs font-medium">
                    {item.uf}
                    {item.municipio && ` - ${item.municipio}`}
                  </span>
                  {item.modalidade && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-2 text-ink-secondary text-xs">
                      {item.modalidade}
                    </span>
                  )}
                  {item.data_encerramento && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-success-subtle text-success text-xs font-medium">
                      Prazo: {formatDate(item.data_encerramento)}
                    </span>
                  )}
                  {item.data_abertura && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-2 text-ink-secondary text-xs">
                      Abertura: {formatDate(item.data_abertura)}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col items-end gap-2 shrink-0">
                <span className="text-lg font-bold font-data text-brand-navy">
                  {formatCurrency(item.valor)}
                </span>
                {item.link && (
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-brand-navy text-white text-sm font-medium rounded-button hover:bg-brand-blue-hover transition-colors"
                  >
                    <svg
              role="img"
              aria-label="Ícone" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    Ver no PNCP
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Blurred items (FREE tier) */}
      {blurredItems.length > 0 && !excelAvailable && (
        <div className="relative">
          {/* Blur overlay with gradient */}
          <div className="absolute inset-0 z-10 bg-gradient-to-b from-transparent via-[var(--canvas)]/70 to-[var(--canvas)] pointer-events-none" />

          {/* Blurred content */}
          <div className="space-y-3 blur-sm select-none" aria-hidden="true">
            {blurredItems.slice(0, 3).map((item, index) => (
              <div
                key={`blurred-${index}`}
                className="p-4 bg-surface-0 border border-strong rounded-card opacity-60"
              >
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-base font-medium text-ink line-clamp-2 mb-1">
                      {item.objeto.substring(0, 50)}...
                    </h4>
                    <p className="text-sm text-ink-secondary truncate">
                      {item.orgao.substring(0, 30)}...
                    </p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-2 text-ink-muted text-xs">
                        {item.uf}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <span className="text-lg font-bold font-data text-ink-muted">
                      R$ ***
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Upgrade CTA overlay */}
          <div className="absolute inset-0 z-20 flex items-center justify-center">
            <div className="bg-surface-0 border border-brand-navy shadow-lg rounded-card p-6 max-w-sm text-center mx-4">
              <div className="w-12 h-12 mx-auto mb-4 bg-brand-blue-subtle rounded-full flex items-center justify-center">
                <svg
              role="img"
              aria-label="Ícone" className="w-6 h-6 text-brand-navy" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-ink mb-2">
                +{blurredItems.length} oportunidades ocultas
              </h4>
              <p className="text-sm text-ink-secondary mb-4">
                Faça upgrade para ver todas as oportunidades com links diretos e exportar para Excel.
              </p>
              <button
                onClick={onUpgradeClick}
                className="w-full py-2.5 bg-brand-navy text-white rounded-button font-semibold hover:bg-brand-blue-hover transition-colors"
              >
                Ver Planos
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Show remaining count for paid users who have Excel */}
      {blurredItems.length > 0 && excelAvailable && (
        <div className="space-y-3">
          {blurredItems.map((item, index) => (
            <div
              key={item.pncp_id || `extra-${index}`}
              className="p-4 bg-surface-0 border border-strong rounded-card hover:border-brand-blue transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h4 className="text-base font-medium text-ink line-clamp-2 mb-1">
                    {item.objeto}
                  </h4>
                  <p className="text-sm text-ink-secondary truncate">
                    {item.orgao}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-brand-blue-subtle text-brand-navy text-xs font-medium">
                      {item.uf}
                      {item.municipio && ` - ${item.municipio}`}
                    </span>
                    {item.modalidade && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-2 text-ink-secondary text-xs">
                        {item.modalidade}
                      </span>
                    )}
                    {item.data_encerramento && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-success-subtle text-success text-xs font-medium">
                        Prazo: {formatDate(item.data_encerramento)}
                      </span>
                    )}
                    {item.data_abertura && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-2 text-ink-secondary text-xs">
                        Abertura: {formatDate(item.data_abertura)}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2 shrink-0">
                  <span className="text-lg font-bold font-data text-brand-navy">
                    {formatCurrency(item.valor)}
                  </span>
                  {item.link && (
                    <a
                      href={item.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-3 py-1.5 bg-brand-navy text-white text-sm font-medium rounded-button hover:bg-brand-blue-hover transition-colors"
                    >
                      <svg
              role="img"
              aria-label="Ícone" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      Ver no PNCP
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
