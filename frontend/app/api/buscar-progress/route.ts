/**
 * SSE Proxy Route - /api/buscar-progress
 *
 * Proxies Server-Sent Events from the backend /buscar-progress/{search_id}
 * endpoint to the browser. This allows real-time progress updates during
 * PNCP search operations.
 *
 * CRIT-012: Added bodyTimeout: 0, AbortController, structured error handling.
 */

import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

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
    "Accept": "text/event-stream",
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

  try {
    // CRIT-012 AC4: Build fetch options with undici bodyTimeout: 0
    const fetchOptions: Record<string, unknown> = {
      headers,
      signal: controller.signal,
    };

    try {
      // @ts-expect-error — undici is available at runtime in Node.js but lacks type declarations
      const undiciModule = await import("undici");
      const UndiciAgent = undiciModule.Agent;
      if (UndiciAgent) {
        fetchOptions.dispatcher = new UndiciAgent({
          bodyTimeout: 0,
          headersTimeout: 30_000,
        });
      }
    } catch {
      // undici not available — proceed without custom dispatcher
    }

    const backendResponse = await fetch(
      `${backendUrl}/v1/buscar-progress/${encodeURIComponent(searchId)}`,
      fetchOptions as RequestInit
    );

    if (!backendResponse.ok) {
      return new Response("Backend error", { status: backendResponse.status });
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
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
  } catch (error) {
    const elapsed = Date.now() - startTime;
    const errorName = error instanceof Error ? error.name : "UnknownError";
    const errorMessage = error instanceof Error ? error.message : String(error);

    // CRIT-012 AC7: Structured logging for streaming errors
    console.error(
      "SSE proxy error:",
      JSON.stringify({
        error_type: errorName,
        search_id: searchId,
        elapsed_ms: elapsed,
        message: errorMessage,
      })
    );

    // CRIT-012 AC6: Explicit handling for BodyTimeoutError and TypeError: terminated
    if (
      errorName === "BodyTimeoutError" ||
      (errorName === "TypeError" && errorMessage === "terminated") ||
      errorMessage.includes("body timeout") ||
      errorMessage.includes("terminated")
    ) {
      return new Response(
        JSON.stringify({
          error: "SSE stream timeout",
          detail:
            "Backend stream was silent too long or connection was terminated",
          error_type: errorName,
          search_id: searchId,
          elapsed_ms: elapsed,
        }),
        {
          status: 504,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    // CRIT-012 AC5: AbortError from client disconnect — not a server error
    if (errorName === "AbortError") {
      return new Response("Client disconnected", { status: 499 });
    }

    return new Response("Failed to connect to backend", { status: 502 });
  }
}
