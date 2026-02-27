/**
 * In-memory IP rate limiter (per-process; sufficient for single-instance POC).
 *
 * Extracted from route files because Next.js 16 only allows valid route
 * exports (GET, POST, etc.) from route.ts files.
 */

export interface RateLimitEntry {
  count: number;
  resetAt: number;
}

export function createRateLimitStore() {
  const store = new Map<string, RateLimitEntry>();

  // Periodically clean expired entries (every 60 s)
  if (typeof globalThis !== "undefined") {
    const _cleanup = setInterval(() => {
      const now = Date.now();
      for (const [key, value] of store.entries()) {
        if (now >= value.resetAt) {
          store.delete(key);
        }
      }
    }, 60_000);
    if (_cleanup && typeof _cleanup === "object" && "unref" in _cleanup) {
      (_cleanup as NodeJS.Timeout).unref();
    }
  }

  return store;
}

export function checkRateLimit(
  store: Map<string, RateLimitEntry>,
  ip: string,
  limit: number,
  windowMs: number
): { allowed: boolean; retryAfter: number } {
  const now = Date.now();
  const entry = store.get(ip);

  if (!entry || now >= entry.resetAt) {
    store.set(ip, { count: 1, resetAt: now + windowMs });
    return { allowed: true, retryAfter: 0 };
  }

  if (entry.count >= limit) {
    const retryAfter = Math.ceil((entry.resetAt - now) / 1000);
    return { allowed: false, retryAfter: Math.max(1, retryAfter) };
  }

  entry.count++;
  return { allowed: true, retryAfter: 0 };
}

// Shared stores for login and signup (singleton per process)
export const loginRateLimitStore = createRateLimitStore();
export const signupRateLimitStore = createRateLimitStore();
