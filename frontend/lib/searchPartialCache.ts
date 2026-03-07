/**
 * STAB-006 AC4: localStorage partial search persistence.
 *
 * Saves partial search results as they arrive via SSE (uf_complete, partial_results)
 * so that if the connection drops or times out, users can recover partial data.
 *
 * - Key format: `search_partial_${searchId}`
 * - TTL: 30 minutes
 * - Cleared after successful complete search
 * - Recovered on SSE disconnect or timeout
 */

import { safeSetItem } from "./storage";

const PARTIAL_PREFIX = "search_partial_";
const PARTIAL_TTL_MS = 30 * 60 * 1000; // 30 minutes

export interface PartialSearchData {
  /** Partial result data accumulated from SSE events */
  partialResult: unknown;
  /** Search ID */
  searchId: string;
  /** UFs that completed so far */
  ufsCompleted: string[];
  /** Total UFs requested */
  totalUfs: number;
  /** Timestamp of last update */
  updatedAt: number;
  /** Timestamp of creation */
  createdAt: number;
}

/**
 * Save partial search data to localStorage.
 * Called on each SSE `uf_complete` or `partial_results` event.
 */
export function savePartialSearch(
  searchId: string,
  partialResult: unknown,
  ufsCompleted: string[],
  totalUfs: number
): void {
  if (typeof window === "undefined") return;
  try {
    const key = `${PARTIAL_PREFIX}${searchId}`;
    const existing = _readPartial(key);
    const data: PartialSearchData = {
      partialResult,
      searchId,
      ufsCompleted,
      totalUfs,
      updatedAt: Date.now(),
      createdAt: existing?.createdAt ?? Date.now(),
    };
    safeSetItem(key, JSON.stringify(data));
  } catch {
    // localStorage full or unavailable — silently ignore
  }
}

/**
 * Recover partial search data from localStorage.
 * Returns null if not found or expired (>30 min TTL).
 */
export function recoverPartialSearch(searchId: string): PartialSearchData | null {
  if (typeof window === "undefined") return null;
  const key = `${PARTIAL_PREFIX}${searchId}`;
  return _readPartial(key);
}

/**
 * Clear partial search data after a successful complete search.
 */
export function clearPartialSearch(searchId: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(`${PARTIAL_PREFIX}${searchId}`);
  } catch {
    // silently ignore
  }
}

/**
 * Clean up all expired partial search entries.
 * Call periodically (e.g., on mount) to prevent localStorage bloat.
 */
export function cleanupExpiredPartials(): void {
  if (typeof window === "undefined") return;
  try {
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(PARTIAL_PREFIX)) {
        const raw = localStorage.getItem(key);
        if (raw) {
          try {
            const data: PartialSearchData = JSON.parse(raw);
            if (Date.now() - data.updatedAt > PARTIAL_TTL_MS) {
              keysToRemove.push(key);
            }
          } catch {
            keysToRemove.push(key);
          }
        }
      }
    }
    keysToRemove.forEach((k) => localStorage.removeItem(k));
  } catch {
    // silently ignore
  }
}

/** Internal helper to read and validate a partial entry */
function _readPartial(key: string): PartialSearchData | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const data: PartialSearchData = JSON.parse(raw);
    if (Date.now() - data.updatedAt > PARTIAL_TTL_MS) {
      localStorage.removeItem(key);
      return null;
    }
    return data;
  } catch {
    return null;
  }
}
