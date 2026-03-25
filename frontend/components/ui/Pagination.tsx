"use client";

import { useCallback, useEffect } from "react";
import { safeSetItem, safeGetItem } from "../../lib/storage";

const PAGE_SIZE_KEY = "smartlic_page_size";
const PAGE_SIZES = [10, 20, 50] as const;
type PageSize = (typeof PAGE_SIZES)[number];

export interface PaginationProps {
  /** Total number of items */
  totalItems: number;
  /** Current page (1-based) */
  currentPage: number;
  /** Items per page */
  pageSize: PageSize;
  /** Called when page changes */
  onPageChange: (page: number) => void;
  /** Called when page size changes */
  onPageSizeChange: (size: PageSize) => void;
  /** ID of the element to scroll to on page change */
  scrollTargetId?: string;
}

function getStoredPageSize(): PageSize {
  const stored = safeGetItem(PAGE_SIZE_KEY);
  if (stored && PAGE_SIZES.includes(Number(stored) as PageSize)) {
    return Number(stored) as PageSize;
  }
  return 10;
}

function storePageSize(size: PageSize) {
  safeSetItem(PAGE_SIZE_KEY, String(size));
}

/** Initialize pagination state — call once at mount */
export function useInitPagination() {
  return getStoredPageSize();
}

export function Pagination({
  totalItems,
  currentPage,
  pageSize,
  onPageChange,
  onPageSizeChange,
  scrollTargetId,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const start = Math.min((currentPage - 1) * pageSize + 1, totalItems);
  const end = Math.min(currentPage * pageSize, totalItems);

  const handlePrev = useCallback(() => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  }, [currentPage, onPageChange]);

  const handleNext = useCallback(() => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  }, [currentPage, totalPages, onPageChange]);

  const handlePageSizeChange = useCallback(
    (newSize: PageSize) => {
      storePageSize(newSize);
      onPageSizeChange(newSize);
      onPageChange(1);
    },
    [onPageSizeChange, onPageChange]
  );

  // Scroll to target on page change
  useEffect(() => {
    if (scrollTargetId && currentPage > 1) {
      const el = document.getElementById(scrollTargetId);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }, [currentPage, scrollTargetId]);

  if (totalItems === 0) return null;

  // UX-421 AC1+AC2: Hide full pagination when results fit in one page; show simple count
  if (totalItems <= pageSize) {
    return (
      <div className="py-3" data-testid="pagination-simple">
        <p className="text-sm text-[var(--ink-secondary)]" data-testid="pagination-info">
          {totalItems} {totalItems === 1 ? 'oportunidade' : 'oportunidades'}
        </p>
      </div>
    );
  }

  return (
    <div
      className="flex flex-col sm:flex-row items-center justify-between gap-3 py-3"
      role="navigation"
      aria-label="Paginação de resultados"
    >
      {/* AC7: "Exibindo X-Y de Z oportunidades" */}
      <p className="text-sm text-[var(--ink-secondary)]" data-testid="pagination-info">
        Exibindo {start}-{end} de {totalItems} oportunidades
      </p>

      <div className="flex items-center gap-3">
        {/* Page size selector — AC5 */}
        <div className="flex items-center gap-1.5">
          <label htmlFor="page-size-select" className="text-xs text-[var(--ink-muted)]">
            Por página:
          </label>
          <select
            id="page-size-select"
            value={pageSize}
            onChange={(e) => handlePageSizeChange(Number(e.target.value) as PageSize)}
            className="text-xs px-2 py-1 border border-[var(--border)] rounded bg-[var(--surface-0)] text-[var(--ink)]
                       focus:border-[var(--brand-blue)] focus:ring-1 focus:ring-[var(--brand-blue)]/20 outline-none"
            data-testid="page-size-select"
          >
            {PAGE_SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Prev/Next + page indicator */}
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrev}
            disabled={currentPage <= 1}
            className="px-4 py-2 text-base font-medium border border-[var(--border)] rounded-button
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:bg-[var(--surface-1)] transition-colors"
            aria-label="Página anterior"
            aria-disabled={currentPage <= 1}
            data-testid="pagination-prev"
          >
            Anterior
          </button>
          <span
            className="text-sm text-[var(--ink-secondary)] tabular-nums"
            aria-current="page"
            data-testid="pagination-page-indicator"
          >
            {currentPage} de {totalPages}
          </span>
          <button
            onClick={handleNext}
            disabled={currentPage >= totalPages}
            className="px-4 py-2 text-base font-medium border border-[var(--border)] rounded-button
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:bg-[var(--surface-1)] transition-colors"
            aria-label="Próxima página"
            aria-disabled={currentPage >= totalPages}
            data-testid="pagination-next"
          >
            Próximo
          </button>
        </div>
      </div>
    </div>
  );
}
