/**
 * HARDEN-026: Safe localStorage wrapper with quota handling.
 *
 * safeSetItem() catches QuotaExceededError and evicts stale/ephemeral
 * entries before retrying once. Eviction order:
 *   1. Expired search_partial_* entries (30 min TTL)
 *   2. All remaining search_partial_* entries
 *   3. smartlic_last_search (24h cache, easily regenerated)
 *
 * If eviction frees enough space the write succeeds silently.
 * If not, the error is swallowed (no data loss is worse than no write).
 */

/** Prefixes considered safe to evict when quota is exceeded */
const EVICTABLE_PREFIXES = ["search_partial_"] as const;

/** Standalone keys safe to evict (ordered by priority — first evicted first) */
const EVICTABLE_KEYS = ["smartlic_last_search"] as const;

function isQuotaError(e: unknown): boolean {
  if (e instanceof DOMException) {
    // Spec name, plus legacy codes used by older browsers
    return (
      e.name === "QuotaExceededError" ||
      e.code === 22 ||
      e.code === 1014 // Firefox
    );
  }
  return false;
}

/**
 * Evict ephemeral/stale localStorage entries to free space.
 * Returns the number of keys removed.
 */
function evict(): number {
  let removed = 0;

  // Pass 1: remove entries matching evictable prefixes
  const keysToCheck: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && EVICTABLE_PREFIXES.some((p) => key.startsWith(p))) {
      keysToCheck.push(key);
    }
  }
  for (const key of keysToCheck) {
    localStorage.removeItem(key);
    removed++;
  }

  // Pass 2: remove standalone evictable keys
  for (const key of EVICTABLE_KEYS) {
    if (localStorage.getItem(key) !== null) {
      localStorage.removeItem(key);
      removed++;
    }
  }

  return removed;
}

/**
 * Safe wrapper around localStorage.setItem.
 *
 * On QuotaExceededError, evicts stale entries and retries once.
 * Never throws — worst case the write is silently dropped.
 */
export function safeSetItem(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch (e) {
    if (!isQuotaError(e)) return; // non-quota error — silently ignore

    const freed = evict();
    if (freed === 0) return; // nothing to evict — give up

    try {
      localStorage.setItem(key, value);
    } catch {
      // Still full after eviction — silently drop
    }
  }
}
