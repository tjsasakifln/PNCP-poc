/**
 * SYS-008: Shared proxy route factory.
 *
 * Eliminates boilerplate across 50+ API proxy routes by handling:
 * - BACKEND_URL env var check
 * - Auth header extraction & validation
 * - X-Correlation-ID forwarding (CRIT-004 AC4)
 * - Error sanitization (CRIT-017)
 * - Token refresh via serverAuth (STORY-253 AC7)
 * - Query parameter forwarding
 * - JSON body forwarding
 */

import { NextRequest, NextResponse } from "next/server";
import { sanitizeProxyError, sanitizeNetworkError } from "./proxy-error-handler";
import { getRefreshedToken } from "./serverAuth";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface ProxyRouteConfig {
  /**
   * Backend path, e.g. "/v1/plans".
   * Can be a function that receives the request for dynamic paths.
   */
  backendPath: string | ((request: NextRequest) => string);

  /** HTTP methods to expose. Defaults to ["GET"]. */
  methods?: HttpMethod[];

  /** Require Authorization header. Defaults to true. */
  requireAuth?: boolean;

  /**
   * Use server-side token refresh (getRefreshedToken) before falling back
   * to the Authorization header. Defaults to false.
   */
  allowRefresh?: boolean;

  /** Fallback error message shown when backend returns a non-JSON error. */
  errorMessage?: string;

  /** Custom 401 message. Defaults to "Autenticacao necessaria". */
  authRequiredMessage?: string;

  /** Custom 503 message when BACKEND_URL is missing. Defaults to "Servidor nao configurado". */
  backendMissingMessage?: string;

  /** Forward query parameters from the incoming request. Defaults to true. */
  forwardQuery?: boolean;

  /**
   * Query parameters to strip before forwarding (e.g. ["endpoint", "_path"]).
   */
  stripQueryParams?: string[];

  /** Next.js fetch cache option (e.g. { revalidate: 300 }). Only for GET. */
  fetchCache?: NextFetchRequestConfig;

  /** Log prefix for console.error messages. Derived from backendPath if omitted. */
  logPrefix?: string;
}

/** Next.js `next` option inside fetch (e.g. `{ revalidate: 300 }`). */
interface NextFetchRequestConfig {
  revalidate?: number | false;
}

/** The map of exported handlers that Next.js expects from a route file. */
type RouteHandlers = {
  [K in HttpMethod]?: (request: NextRequest) => Promise<NextResponse>;
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getBackendUrl(): string | undefined {
  return process.env.BACKEND_URL;
}

function resolveLogPrefix(config: ProxyRouteConfig): string {
  if (config.logPrefix) return config.logPrefix;
  const path =
    typeof config.backendPath === "string" ? config.backendPath : "proxy";
  // "/v1/trial-status" → "trial-status"
  return path.replace(/^\/v1\//, "").replace(/\//g, "-") || "proxy";
}

/**
 * Build forwarding headers: Authorization + X-Correlation-ID + Content-Type.
 */
function buildHeaders(
  authHeader: string | null,
  correlationId: string | null,
  includeContentType: boolean,
): Record<string, string> {
  const headers: Record<string, string> = {};
  if (authHeader) {
    headers["Authorization"] = authHeader;
  }
  if (includeContentType) {
    headers["Content-Type"] = "application/json";
  }
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }
  return headers;
}

/**
 * Resolve the full backend URL including query string forwarding.
 */
function resolveUrl(
  backendUrl: string,
  backendPath: string,
  request: NextRequest,
  forwardQuery: boolean,
  stripParams: string[],
): string {
  if (!forwardQuery) return `${backendUrl}${backendPath}`;

  // Guard against missing/undefined request.url (e.g. in test mocks)
  if (!request.url) return `${backendUrl}${backendPath}`;

  const incoming = new URL(request.url);
  const outgoing = new URLSearchParams();

  incoming.searchParams.forEach((value, key) => {
    if (!stripParams.includes(key)) {
      outgoing.set(key, value);
    }
  });

  const qs = outgoing.toString();
  return qs ? `${backendUrl}${backendPath}?${qs}` : `${backendUrl}${backendPath}`;
}

/**
 * Safely process a backend response:
 * 1. Read body as text
 * 2. Run through CRIT-017 sanitizer
 * 3. Parse JSON and return
 */
async function safeProxyResponse(
  response: Response,
  fallbackMessage: string,
): Promise<NextResponse> {
  const body = await response.text();

  // CRIT-017: Sanitize infrastructure errors
  const sanitized = sanitizeProxyError(
    response.status,
    body,
    response.headers.get("content-type"),
  );
  if (sanitized) return sanitized;

  try {
    const data = JSON.parse(body);
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json(
      { message: fallbackMessage },
      { status: response.status },
    );
  }
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/**
 * Creates Next.js route handlers (GET, POST, PUT, PATCH, DELETE) from a
 * declarative config object, eliminating the boilerplate that all proxy
 * routes share.
 *
 * Usage:
 * ```ts
 * // frontend/app/api/plans/route.ts
 * export const { GET } = createProxyRoute({
 *   backendPath: "/v1/plans",
 *   requireAuth: false,
 *   fetchCache: { revalidate: 300 },
 * });
 * ```
 */
export function createProxyRoute(config: ProxyRouteConfig): RouteHandlers {
  const {
    methods = ["GET"],
    requireAuth = true,
    allowRefresh = false,
    errorMessage = "Erro temporário de comunicação",
    authRequiredMessage = "Autenticação necessária",
    backendMissingMessage = "Servidor não configurado",
    forwardQuery = true,
    stripQueryParams = [],
    fetchCache,
  } = config;

  const logPrefix = resolveLogPrefix(config);

  function createHandler(method: HttpMethod) {
    return async function handler(request: NextRequest): Promise<NextResponse> {
      // 1. Check BACKEND_URL
      const backendUrl = getBackendUrl();
      if (!backendUrl) {
        console.error("BACKEND_URL environment variable is not configured");
        return NextResponse.json(
          { message: backendMissingMessage },
          { status: 503 },
        );
      }

      // 2. Auth
      let authHeader: string | null = null;

      if (requireAuth) {
        if (allowRefresh) {
          const refreshedToken = await getRefreshedToken();
          authHeader = refreshedToken
            ? `Bearer ${refreshedToken}`
            : request.headers.get("authorization");
        } else {
          authHeader = request.headers.get("authorization");
        }

        if (!authHeader) {
          return NextResponse.json(
            { message: authRequiredMessage },
            { status: 401 },
          );
        }
      } else {
        // Still forward auth if present (some public endpoints optionally use it)
        authHeader = request.headers.get("authorization");
      }

      // 3. Correlation ID
      const correlationId = request.headers.get("X-Correlation-ID");

      // 4. Resolve backend path
      const backendPath =
        typeof config.backendPath === "function"
          ? config.backendPath(request)
          : config.backendPath;

      const url = resolveUrl(
        backendUrl,
        backendPath,
        request,
        forwardQuery,
        stripQueryParams,
      );

      // 5. Build headers
      const needsContentType = method !== "GET" && method !== "DELETE";
      const headers = buildHeaders(authHeader, correlationId, needsContentType);

      // 6. Build fetch options
      const fetchOpts: RequestInit & { next?: NextFetchRequestConfig } = {
        method,
        headers,
      };

      // Body for non-GET/DELETE
      if (method !== "GET" && method !== "DELETE") {
        try {
          const body = await request.json();
          fetchOpts.body = JSON.stringify(body);
        } catch {
          // No body or invalid JSON — continue without body
        }
      }

      // Cache option (GET only)
      if (method === "GET" && fetchCache) {
        fetchOpts.next = fetchCache;
      }

      // 7. Fetch
      try {
        const response = await fetch(url, fetchOpts);
        return safeProxyResponse(response, errorMessage);
      } catch (error) {
        console.error(
          `[${logPrefix}] Network error:`,
          error instanceof Error ? error.message : error,
        );
        return sanitizeNetworkError(error);
      }
    };
  }

  // Build the handler map
  const handlers: RouteHandlers = {};
  for (const method of methods) {
    handlers[method] = createHandler(method);
  }
  return handlers;
}
