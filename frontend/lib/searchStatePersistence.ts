/**
 * Search State Persistence Utility
 *
 * Handles temporary state preservation during authentication flow.
 * Uses sessionStorage to survive navigation within same tab.
 * Auto-expires after 1 hour to prevent stale data.
 *
 * @see docs/ux-analysis/state-persistence-recommendations.md
 */

const STORAGE_KEY = 'smartlic_pending_search_state';
const TTL_MS = 3600000; // 1 hour

export interface SearchFormState {
  ufs: string[];
  startDate: string;
  endDate: string;
  setor?: string;
  municipios?: string[];
  includeKeywords?: string[];
  excludeKeywords?: string[];
}

export interface PersistedSearchState {
  result: any; // BuscaResult type
  downloadId: string;
  formState: SearchFormState;
  timestamp: number;
  expiresAt: number;
}

/**
 * Save search state before navigating to auth
 */
export function saveSearchState(
  result: any,
  downloadId: string,
  formState: SearchFormState
): boolean {
  try {
    const state: PersistedSearchState = {
      result,
      downloadId,
      formState,
      timestamp: Date.now(),
      expiresAt: Date.now() + TTL_MS,
    };

    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));

    // Track analytics
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'search_state_saved_for_auth', {
        download_id: downloadId,
        has_results: !!result,
      });
    }

    return true;
  } catch (error) {
    console.error('[searchStatePersistence] Failed to save state:', error);

    // Track failure
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'search_state_save_failed', {
        error: error instanceof Error ? error.message : 'unknown',
      });
    }

    return false;
  }
}

/**
 * Restore search state after auth redirect
 */
export function restoreSearchState(): PersistedSearchState | null {
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY);

    if (!saved) {
      return null;
    }

    const state: PersistedSearchState = JSON.parse(saved);

    // Check expiration
    if (Date.now() > state.expiresAt) {
      console.warn('[searchStatePersistence] Saved state expired, clearing...');
      clearSearchState();

      // Track expiration
      if (typeof window !== 'undefined' && (window as any).gtag) {
        (window as any).gtag('event', 'search_state_expired', {
          age_ms: Date.now() - state.timestamp,
        });
      }

      return null;
    }

    // Track successful restore
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'search_state_restored', {
        download_id: state.downloadId,
        age_ms: Date.now() - state.timestamp,
      });
    }

    // Clear after successful restore (one-time use)
    clearSearchState();

    return state;
  } catch (error) {
    console.error('[searchStatePersistence] Failed to restore state:', error);
    clearSearchState();

    // Track failure
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'search_state_restore_failed', {
        error: error instanceof Error ? error.message : 'unknown',
      });
    }

    return null;
  }
}

/**
 * Clear saved search state
 */
export function clearSearchState(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('[searchStatePersistence] Failed to clear state:', error);
  }
}

/**
 * Check if there's a saved search state (without consuming it)
 */
export function hasSavedSearchState(): boolean {
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (!saved) return false;

    const state: PersistedSearchState = JSON.parse(saved);
    return Date.now() <= state.expiresAt;
  } catch {
    return false;
  }
}
