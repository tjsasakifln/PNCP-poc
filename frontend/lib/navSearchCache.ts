/**
 * Navigation Search Cache
 *
 * Persists search results across intra-app navigation (e.g. /buscar → /dashboard → /buscar).
 * Uses sessionStorage so it's isolated per browser tab (no cross-tab conflicts).
 * TTL: 30 minutes. Does NOT auto-clear on restore (unlike the auth-flow cache).
 *
 * Distinct from `searchStatePersistence.ts` which is one-time-use for auth redirects.
 *
 * @see docs/stories/UX-432-resultados-perdidos-navegacao.md
 */

import type { SearchFormState } from './searchStatePersistence';

export type { SearchFormState };

const NAV_CACHE_KEY = 'smartlic_nav_search_state';
const TTL_MS = 1_800_000; // 30 minutes
const MAX_RESULTS = 100;  // guard against 5 MB sessionStorage limit

export interface NavSearchMeta {
  sectorName: string;
  ufsLabel: string; // e.g. "SC, RS, SP"
}

export interface NavSearchCacheEntry {
  result: unknown;        // BuscaResult (licitacoes trimmed to MAX_RESULTS)
  formState: SearchFormState;
  meta: NavSearchMeta;
  timestamp: number;
  expiresAt: number;
}

/**
 * Persist current search results for navigation recovery.
 * Trims licitacoes to MAX_RESULTS to stay within sessionStorage limits.
 * Returns true on success, false on QuotaExceededError or other failure.
 */
export function saveNavSearch(
  result: unknown,
  formState: SearchFormState,
  meta: NavSearchMeta,
): boolean {
  try {
    // Trim result payload to avoid 5 MB limit (AC: Riscos)
    const safeResult = trimResult(result);

    const entry: NavSearchCacheEntry = {
      result: safeResult,
      formState,
      meta,
      timestamp: Date.now(),
      expiresAt: Date.now() + TTL_MS,
    };

    sessionStorage.setItem(NAV_CACHE_KEY, JSON.stringify(entry));
    return true;
  } catch {
    // QuotaExceededError or similar — fail silently, don't break the app
    return false;
  }
}

/**
 * Restore persisted results after navigation back to /buscar.
 * Does NOT auto-clear — data remains available for subsequent restores within TTL.
 * Returns null if nothing saved, TTL expired, or data is corrupted (AC4).
 */
export function restoreNavSearch(): NavSearchCacheEntry | null {
  try {
    const saved = sessionStorage.getItem(NAV_CACHE_KEY);
    if (!saved) return null;

    const entry: NavSearchCacheEntry = JSON.parse(saved);

    // AC4: TTL expired → clear and return null
    if (Date.now() > entry.expiresAt) {
      clearNavSearch();
      return null;
    }

    return entry;
  } catch {
    // AC4: corrupted JSON → clear and return null (no error shown to user)
    clearNavSearch();
    return null;
  }
}

/**
 * Explicitly clear the navigation cache.
 * Called on "Nova busca" click or when the user wants fresh results.
 */
export function clearNavSearch(): void {
  try {
    sessionStorage.removeItem(NAV_CACHE_KEY);
  } catch {
    // Ignore — best-effort cleanup
  }
}

/**
 * Check if valid (non-expired) navigation cache exists without consuming it.
 */
export function hasNavSearch(): boolean {
  try {
    const saved = sessionStorage.getItem(NAV_CACHE_KEY);
    if (!saved) return false;
    const entry: NavSearchCacheEntry = JSON.parse(saved);
    return Date.now() <= entry.expiresAt;
  } catch {
    return false;
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────

function trimResult(result: unknown): unknown {
  if (!result || typeof result !== 'object') return result;

  const r = result as Record<string, unknown>;
  if (!Array.isArray(r.licitacoes)) return result;

  if (r.licitacoes.length <= MAX_RESULTS) return result;

  return {
    ...r,
    licitacoes: r.licitacoes.slice(0, MAX_RESULTS),
  };
}
