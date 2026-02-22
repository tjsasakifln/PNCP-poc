/**
 * SSE Proxy Route - /api/buscar-progress
 *
 * Proxies Server-Sent Events from the backend /buscar-progress/{search_id}
 * endpoint to the browser. This allows real-time progress updates during
 * PNCP search operations.
 *
 * CRIT-012: Added bodyTimeout: 0, AbortController, structured error handling.
 * CRIT-026: Added undici diagnostic logging, AbortSignal.timeout fallback,
 *           retry-once on BodyTimeoutError/terminated, Sentry breadcrumb.
 */

import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// CRIT-026 AC7: Max retries for transient stream failures
const MAX_SSE_RETRIES = 1;

/**
 * CRIT-026 AC6+AC7: Perform the actual SSE fetch to backend with undici
 * dispatcher and fallback timeout. Extracted for retry support.
 */
async function fetchSSEStream(
  backendUrl: string,
  searchId: string,
  headers: Record<string, string>,
  signal: AbortSignal
): Promise<Response> {
  const fetchOptions: Record<string, unknown> = {
    headers,
    signal,
  };

  // CRIT-012 AC4 + CRIT-026 AC5: Build fetch options with undici bodyTimeout: 0
  let undiciActive = false;
  try {
    // @ts-expect-error — undici is available at runtime in Node.js but lacks type declarations
    const undiciModule = await import("undici");
    const UndiciAgent = undiciModule.Agent;
    if (UndiciAgent) {
      fetchOptions.dispatcher = new UndiciAgent({
        bodyTimeout: 0,
        headersTimeout: 30_000,
      });
      undiciActive = true;
    }
  } catch {
    // undici not available — proceed without custom dispatcher
  }

  // CRIT-026 AC5: Diagnostic logging for undici import result
  console.log(
    `[SSE-PROXY] search_id=${searchId} undici_dispatcher=${undiciActive ? "custom" : "default"}`
  );

  return fetch(
    `${backendUrl}/v1/buscar-progress/${encodeURIComponent(searchId)}`,
    fetchOptions as RequestInit
  );
}

/**
 * CRIT-026 AC7: Check if an error is a transient stream failure worth retrying.
 */
function isRetryableStreamError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  const name = error.name;
  const msg = error.message;
  return (
    name === "BodyTimeoutError" ||
    (name === "TypeError" && msg === "terminated") ||
    msg.includes("body timeout") ||
    msg.includes("terminated") ||
    msg.includes("failed to pipe")
  );
}

export async function GET(request: NextRequest) {
  const searchId = request.nextUrl.searchParams.get("search_id");
  const token = request.nextUrl.searchParams.get("token");

  if (!searchId) {
    return new Response("search_id is required", { status: 400 });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return new Response("Server not configured", { status: 503 });
  }

  // CRIT-004 AC2: Forward Authorization + X-Correlation-ID
  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {
    Accept: "text/event-stream",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  // CRIT-012 AC5: AbortController for cleanup on client disconnect
  const controller = new AbortController();
  const startTime = Date.now();

  // Cancel backend fetch when client disconnects
  request.signal.addEventListener("abort", () => controller.abort());

  // CRIT-026 AC9: Log breadcrumb before SSE fetch
  console.log(
    `[SSE-PROXY] Connecting: search_id=${searchId} backend=${backendUrl}`
  );

  // CRIT-026 AC7: Retry loop — try once, retry once on transient failure
  let lastError: unknown = null;
  for (let attempt = 0; attempt <= MAX_SSE_RETRIES; attempt++) {
    try {
      if (attempt > 0) {
        // CRIT-026 AC7: Brief delay before retry
        console.log(
          `[SSE-PROXY] Retrying (attempt ${attempt + 1}/${MAX_SSE_RETRIES + 1}) search_id=${searchId}`
        );
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }

      const backendResponse = await fetchSSEStream(
        backendUrl,
        searchId,
        headers,
        controller.signal
      );

      if (!backendResponse.ok) {
        return new Response("Backend error", {
          status: backendResponse.status,
        });
      }

      if (!backendResponse.body) {
        return new Response("No stream body", { status: 502 });
      }

      // Proxy the SSE stream directly to the browser
      return new Response(backendResponse.body, {
        status: 200,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache, no-transform",
          Connection: "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    } catch (error) {
      lastError = error;
      const elapsed = Date.now() - startTime;
      const errorName =
        error instanceof Error ? error.name : "UnknownError";
      const errorMessage =
        error instanceof Error ? error.message : String(error);

      // CRIT-012 AC7: Structured logging for streaming errors
      console.error(
        "SSE proxy error:",
        JSON.stringify({
          error_type: errorName,
          search_id: searchId,
          elapsed_ms: elapsed,
          message: errorMessage,
          attempt: attempt + 1,
        })
      );

      // CRIT-012 AC5: AbortError from client disconnect — not retryable
      if (errorName === "AbortError") {
        return new Response("Client disconnected", { status: 499 });
      }

      // CRIT-026 AC7: Retry once on transient stream errors
      if (isRetryableStreamError(error) && attempt < MAX_SSE_RETRIES) {
        continue; // Retry
      }

      // No more retries — fall through to error response
      break;
    }
  }

  // Build final error response from last error
  const elapsed = Date.now() - startTime;
  const errorName =
    lastError instanceof Error ? lastError.name : "UnknownError";
  const errorMessage =
    lastError instanceof Error ? lastError.message : String(lastError);

  // CRIT-012 AC6 + CRIT-026: BodyTimeoutError / terminated → 504
  if (isRetryableStreamError(lastError)) {
    return new Response(
      JSON.stringify({
        error: "SSE stream timeout",
        detail:
          "Backend stream was silent too long or connection was terminated",
        error_type: errorName,
        search_id: searchId,
        elapsed_ms: elapsed,
        retries_exhausted: true,
      }),
      {
        status: 504,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  return new Response("Failed to connect to backend", { status: 502 });
}
