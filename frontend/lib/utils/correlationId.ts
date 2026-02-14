/**
 * Correlation ID utilities for distributed tracing.
 *
 * STORY-226 Track 5 (AC24): Generates a per-session correlation ID and
 * provides it for inclusion in outgoing API requests. The correlation ID
 * is stored in sessionStorage so it persists across page navigations
 * within the same browser session but resets when the tab is closed.
 *
 * Usage:
 *   import { getCorrelationId } from '@/lib/utils/correlationId';
 *
 *   const headers = {
 *     'X-Request-ID': getCorrelationId(),
 *   };
 */

const STORAGE_KEY = 'smartlic_correlation_id';

/**
 * Get or create a correlation ID for the current browser session.
 *
 * On the first call per session, generates a new UUID v4 and stores it
 * in sessionStorage. Subsequent calls return the same ID.
 *
 * Falls back to generating a new UUID on every call if sessionStorage
 * is unavailable (e.g., SSR, private browsing restrictions).
 *
 * @returns A UUID string identifying this browser session.
 */
export function getCorrelationId(): string {
  // SSR guard — sessionStorage is only available in the browser
  if (typeof window === 'undefined') {
    return crypto.randomUUID();
  }

  try {
    const existing = sessionStorage.getItem(STORAGE_KEY);
    if (existing) {
      return existing;
    }

    const newId = crypto.randomUUID();
    sessionStorage.setItem(STORAGE_KEY, newId);
    return newId;
  } catch {
    // sessionStorage may throw in private/incognito mode on some browsers
    return crypto.randomUUID();
  }
}

/**
 * Log a correlation-tagged message to the browser console.
 *
 * Prefixes the message with the session correlation ID for easy
 * cross-referencing with backend logs.
 *
 * @param method - HTTP method (GET, POST, etc.)
 * @param url - Request URL
 * @param correlationId - The correlation ID sent with the request
 */
export function logCorrelatedRequest(
  method: string,
  url: string,
  correlationId: string
): void {
  console.log(
    `[SmartLic] ${method} ${url} [correlation_id=${correlationId}]`
  );
}
