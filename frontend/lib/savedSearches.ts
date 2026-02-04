/**
 * localStorage utilities for Saved Searches feature
 *
 * Provides type-safe functions to persist, load, update, and delete saved searches
 * from browser localStorage.
 *
 * Storage key: "descomplicita_saved_searches"
 * Max saved searches: 10
 */

import { v4 as uuidv4 } from 'uuid';

const STORAGE_KEY = 'descomplicita_saved_searches';
const MAX_SAVED_SEARCHES = 10;

export interface SavedSearch {
  id: string; // UUID v4
  name: string; // User-defined name
  searchParams: {
    ufs: string[];
    dataInicial: string;
    dataFinal: string;
    searchMode: "setor" | "termos";
    setorId?: string;
    termosBusca?: string;
  };
  createdAt: string; // ISO timestamp
  lastUsedAt: string; // ISO timestamp
}

/**
 * Load all saved searches from localStorage
 *
 * @returns Array of saved searches, sorted by most recently used
 */
export function loadSavedSearches(): SavedSearch[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];

    const searches = JSON.parse(stored) as SavedSearch[];

    // Sort by most recently used
    return searches.sort((a, b) =>
      new Date(b.lastUsedAt).getTime() - new Date(a.lastUsedAt).getTime()
    );
  } catch (error) {
    console.error('Failed to load saved searches:', error);
    return [];
  }
}

/**
 * Save a new search to localStorage
 *
 * @param search - Search parameters and metadata
 * @returns The saved search with generated ID and timestamps
 * @throws Error if localStorage quota exceeded
 */
export function saveSearch(
  name: string,
  searchParams: SavedSearch['searchParams']
): SavedSearch {
  // Validate name is not empty
  if (!name || !name.trim()) {
    throw new Error('Nome da busca é obrigatório');
  }

  const newSearch: SavedSearch = {
    id: uuidv4(),
    name: name.trim(),
    searchParams,
    createdAt: new Date().toISOString(),
    lastUsedAt: new Date().toISOString(),
  };

  const existingSearches = loadSavedSearches();

  // Check if we're at max capacity
  if (existingSearches.length >= MAX_SAVED_SEARCHES) {
    throw new Error(`Máximo de ${MAX_SAVED_SEARCHES} buscas salvas atingido. Exclua uma busca para adicionar outra.`);
  }

  const updatedSearches = [newSearch, ...existingSearches];

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedSearches));
    return newSearch;
  } catch (e) {
    if (e instanceof Error && e.name === 'QuotaExceededError') {
      throw new Error('Limite de armazenamento excedido. Exclua algumas buscas salvas.');
    }
    throw e;
  }
}

/**
 * Update an existing saved search
 *
 * @param id - Search ID to update
 * @param updates - Partial search data to update
 * @returns Updated search or null if not found
 */
export function updateSavedSearch(
  id: string,
  updates: Partial<Pick<SavedSearch, 'name' | 'searchParams'>>
): SavedSearch | null {
  const searches = loadSavedSearches();
  const index = searches.findIndex(s => s.id === id);

  if (index === -1) return null;

  const updated = {
    ...searches[index],
    ...updates,
    lastUsedAt: new Date().toISOString(),
  };

  searches[index] = updated;

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(searches));
    return updated;
  } catch (error) {
    console.error('Failed to update saved search:', error);
    return null;
  }
}

/**
 * Delete a saved search
 *
 * @param id - Search ID to delete
 * @returns true if deleted, false if not found
 */
export function deleteSavedSearch(id: string): boolean {
  const searches = loadSavedSearches();
  const filtered = searches.filter(s => s.id !== id);

  if (filtered.length === searches.length) {
    return false; // Not found
  }

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    return true;
  } catch (error) {
    console.error('Failed to delete saved search:', error);
    return false;
  }
}

/**
 * Update lastUsedAt timestamp for a saved search
 *
 * @param id - Search ID to update
 * @returns Updated search or null if not found
 */
export function markSearchAsUsed(id: string): SavedSearch | null {
  return updateSavedSearch(id, {});
}

/**
 * Clear all saved searches
 */
export function clearAllSavedSearches(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear saved searches:', error);
  }
}

/**
 * Get count of saved searches
 */
export function getSavedSearchCount(): number {
  return loadSavedSearches().length;
}

/**
 * Check if max capacity reached
 */
export function isMaxCapacity(): boolean {
  return getSavedSearchCount() >= MAX_SAVED_SEARCHES;
}

/**
 * Alias for isMaxCapacity (for backwards compatibility)
 */
export const isMaxCapacityReached = isMaxCapacity;
