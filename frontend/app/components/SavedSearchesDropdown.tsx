"use client";

import { useState } from 'react';
import { useSavedSearches, type UseSavedSearchesReturn } from '../../hooks/useSavedSearches';
import type { SavedSearch } from '../../lib/savedSearches';

interface SavedSearchesDropdownProps {
  onLoadSearch: (search: SavedSearch) => void;
  onAnalyticsEvent?: (eventName: string, properties?: Record<string, any>) => void;
}

/**
 * Dropdown component for managing and loading saved searches
 *
 * Features:
 * - Display up to 10 saved searches
 * - Sort by most recently used
 * - Delete individual searches
 * - Clear all searches
 * - Visual feedback for empty state
 * - Analytics tracking
 */
export function SavedSearchesDropdown({
  onLoadSearch,
  onAnalyticsEvent,
}: SavedSearchesDropdownProps) {
  const {
    searches,
    loading,
    deleteSearch,
    loadSearch,
    clearAll,
  } = useSavedSearches();

  const [isOpen, setIsOpen] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const handleLoadSearch = (id: string) => {
    const search = loadSearch(id);
    if (search) {
      onLoadSearch(search);
      setIsOpen(false);

      // Track analytics
      onAnalyticsEvent?.('saved_search_loaded', {
        search_id: id,
        search_name: search.name,
        search_mode: search.searchParams.searchMode,
        ufs: search.searchParams.ufs,
        uf_count: search.searchParams.ufs.length,
        days_since_created: Math.floor(
          (Date.now() - new Date(search.createdAt).getTime()) / (1000 * 60 * 60 * 24)
        ),
      });
    }
  };

  const handleDeleteSearch = (id: string, name: string) => {
    if (deleteConfirmId === id) {
      // Confirmed - delete
      const success = deleteSearch(id);
      setDeleteConfirmId(null);

      if (success) {
        // Track analytics
        onAnalyticsEvent?.('saved_search_deleted', {
          search_id: id,
          search_name: name,
          remaining_searches: searches.length - 1,
        });
      }
    } else {
      // First click - show confirmation
      setDeleteConfirmId(id);
      // Auto-cancel after 3 seconds
      setTimeout(() => setDeleteConfirmId(null), 3000);
    }
  };

  const formatDate = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'agora';
    if (diffMins < 60) return `há ${diffMins} min`;
    if (diffHours < 24) return `há ${diffHours}h`;
    if (diffDays === 1) return 'ontem';
    if (diffDays < 7) return `há ${diffDays} dias`;

    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  };

  const getSearchLabel = (search: SavedSearch): string => {
    const { searchMode, setorId, termosBusca } = search.searchParams;
    if (searchMode === 'termos' && termosBusca) {
      return `"${termosBusca}"`;
    }
    return setorId || 'Busca personalizada';
  };

  if (loading) {
    return null; // Don't show anything while loading
  }

  return (
    <div className="relative">
      {/* Dropdown Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        type="button"
        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-ink-secondary
                   hover:text-ink hover:bg-surface-1 rounded-button transition-colors
                   border border-strong"
        aria-label="Buscas salvas"
        aria-expanded={isOpen}
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="hidden sm:inline">Buscas Salvas</span>
        {searches.length > 0 && (
          <span className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5
                         text-xs font-semibold text-white bg-brand-navy rounded-full">
            {searches.length}
          </span>
        )}
        <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
             fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Content */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />

          {/* Dropdown Panel */}
          <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-surface-0 border border-strong
                          rounded-card shadow-lg z-20 max-h-[400px] overflow-y-auto">
            {searches.length === 0 ? (
              // Empty State
              <div className="p-6 text-center">
                <svg className="mx-auto w-12 h-12 text-ink-faint mb-3" fill="none"
                     viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p className="text-sm text-ink-muted">Nenhuma busca salva</p>
                <p className="text-xs text-ink-faint mt-1">
                  Suas buscas aparecerão aqui após realizar uma pesquisa
                </p>
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-strong">
                  <span className="text-sm font-semibold text-ink">
                    Buscas Recentes ({searches.length}/10)
                  </span>
                  {searches.length > 0 && (
                    <button
                      onClick={() => {
                        if (window.confirm('Deseja excluir todas as buscas salvas?')) {
                          clearAll();
                          setIsOpen(false);
                        }
                      }}
                      className="text-xs text-ink-muted hover:text-error transition-colors"
                      type="button"
                    >
                      Limpar todas
                    </button>
                  )}
                </div>

                {/* Search List */}
                <div className="py-2">
                  {searches.map((search) => (
                    <div
                      key={search.id}
                      className="px-4 py-3 hover:bg-surface-1 transition-colors border-b border-strong last:border-b-0"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <button
                          onClick={() => handleLoadSearch(search.id)}
                          className="flex-1 text-left group"
                          type="button"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium text-ink group-hover:text-brand-blue transition-colors">
                              {search.name}
                            </span>
                          </div>

                          <div className="text-xs text-ink-muted space-y-0.5">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{getSearchLabel(search)}</span>
                              <span>•</span>
                              <span>{search.searchParams.ufs.join(', ')}</span>
                            </div>
                            <div className="flex items-center gap-2 text-ink-faint">
                              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              <span>{formatDate(search.lastUsedAt)}</span>
                            </div>
                          </div>
                        </button>

                        {/* Delete Button */}
                        <button
                          onClick={() => handleDeleteSearch(search.id, search.name)}
                          className={`flex-shrink-0 p-1.5 rounded transition-colors ${
                            deleteConfirmId === search.id
                              ? 'bg-error text-white'
                              : 'text-ink-muted hover:text-error hover:bg-error-subtle'
                          }`}
                          type="button"
                          aria-label={deleteConfirmId === search.id ? 'Confirmar exclusão' : 'Excluir busca'}
                          title={deleteConfirmId === search.id ? 'Clique novamente para confirmar' : 'Excluir'}
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
