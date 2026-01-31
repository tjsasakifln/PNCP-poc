/**
 * React hook for managing saved searches
 *
 * Provides state management and operations for saved searches with
 * automatic localStorage synchronization.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  loadSavedSearches,
  saveSearch,
  deleteSavedSearch,
  updateSavedSearch,
  markSearchAsUsed,
  clearAllSavedSearches,
  isMaxCapacity,
  type SavedSearch,
} from '@/lib/savedSearches';

export interface UseSavedSearchesReturn {
  searches: SavedSearch[];
  loading: boolean;
  isMaxCapacity: boolean;
  saveNewSearch: (name: string, params: SavedSearch['searchParams']) => SavedSearch | null;
  deleteSearch: (id: string) => boolean;
  updateSearch: (id: string, updates: Partial<Pick<SavedSearch, 'name' | 'searchParams'>>) => SavedSearch | null;
  loadSearch: (id: string) => SavedSearch | null;
  clearAll: () => void;
  refresh: () => void;
}

/**
 * Hook for managing saved searches
 *
 * @example
 * const { searches, saveNewSearch, deleteSearch, loadSearch } = useSavedSearches();
 *
 * // Save a search
 * saveNewSearch("Uniformes SC/PR/RS", {
 *   ufs: ["SC", "PR", "RS"],
 *   dataInicial: "2026-01-22",
 *   dataFinal: "2026-01-29",
 *   searchMode: "setor",
 *   setorId: "vestuario"
 * });
 *
 * // Load a search
 * const search = loadSearch(searchId);
 * if (search) {
 *   // Apply search params to form
 * }
 */
export function useSavedSearches(): UseSavedSearchesReturn {
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [loading, setLoading] = useState(true);
  const [maxCapacity, setMaxCapacity] = useState(false);

  /**
   * Load searches from localStorage
   */
  const refresh = useCallback(() => {
    setLoading(true);
    const loaded = loadSavedSearches();
    setSearches(loaded);
    setMaxCapacity(isMaxCapacity());
    setLoading(false);
  }, []);

  // Load on mount
  useEffect(() => {
    refresh();
  }, [refresh]);

  /**
   * Save a new search
   */
  const saveNewSearch = useCallback((
    name: string,
    params: SavedSearch['searchParams']
  ): SavedSearch | null => {
    try {
      const newSearch = saveSearch(name, params);
      refresh();
      return newSearch;
    } catch (error) {
      console.error('Failed to save search:', error);
      // Return error message via exception (caught by caller)
      throw error;
    }
  }, [refresh]);

  /**
   * Delete a saved search
   */
  const deleteSearch = useCallback((id: string): boolean => {
    const success = deleteSavedSearch(id);
    if (success) {
      refresh();
    }
    return success;
  }, [refresh]);

  /**
   * Update a saved search
   */
  const updateSearch = useCallback((
    id: string,
    updates: Partial<Pick<SavedSearch, 'name' | 'searchParams'>>
  ): SavedSearch | null => {
    const updated = updateSavedSearch(id, updates);
    if (updated) {
      refresh();
    }
    return updated;
  }, [refresh]);

  /**
   * Load a search and mark it as used
   */
  const loadSearch = useCallback((id: string): SavedSearch | null => {
    const search = searches.find(s => s.id === id);
    if (search) {
      markSearchAsUsed(id);
      refresh();
    }
    return search || null;
  }, [searches, refresh]);

  /**
   * Clear all saved searches
   */
  const clearAll = useCallback(() => {
    clearAllSavedSearches();
    refresh();
  }, [refresh]);

  return {
    searches,
    loading,
    isMaxCapacity: maxCapacity,
    saveNewSearch,
    deleteSearch,
    updateSearch,
    loadSearch,
    clearAll,
    refresh,
  };
}
