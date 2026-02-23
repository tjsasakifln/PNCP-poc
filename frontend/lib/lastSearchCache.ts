/**
 * GTM-UX-004 AC5-AC7: Last Search Cache
 *
 * Persists the most recent search result in localStorage so the
 * "Ver ultima busca" button in SourcesUnavailable can restore it
 * when all sources are down.
 */

const LAST_SEARCH_KEY = "smartlic_last_search";
const LAST_SEARCH_TTL = 24 * 60 * 60 * 1000; // 24 hours

export interface LastSearchData {
  result: unknown; // BuscaResult
  timestamp: number;
}

/** Save the most recent successful search result to localStorage */
export function saveLastSearch(result: unknown): void {
  if (typeof window === "undefined") return;
  try {
    const data: LastSearchData = { result, timestamp: Date.now() };
    localStorage.setItem(LAST_SEARCH_KEY, JSON.stringify(data));
  } catch {
    // localStorage might be full — silently ignore
  }
}

/** Load the last search result (returns null if missing or expired) */
export function getLastSearch(): LastSearchData | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(LAST_SEARCH_KEY);
    if (!raw) return null;
    const data: LastSearchData = JSON.parse(raw);
    if (Date.now() - data.timestamp > LAST_SEARCH_TTL) {
      localStorage.removeItem(LAST_SEARCH_KEY);
      return null;
    }
    return data;
  } catch {
    return null;
  }
}

/** Check if a last search exists without consuming it */
export function checkHasLastSearch(): boolean {
  return getLastSearch() !== null;
}
