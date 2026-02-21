import { NextResponse } from "next/server";

/**
 * Liveness health check — always returns 200 if the frontend process is up.
 *
 * Backend connectivity is reported as informational metadata but does NOT
 * block the healthcheck. This prevents Railway deployment failures caused
 * by the backend starting slower than the frontend.
 *
 * CRIT-008 AC7-AC8: Structured telemetry + descriptive logging.
 * CRIT-010 AC8: Checks backend `ready` field to distinguish "starting" from "healthy".
 * CRIT-006 AC4-AC7: Classify connection errors (DNS vs timeout) and set backend_url_valid flag.
 */

// AC7: Rate limit telemetry events to max 1 per minute
let lastTelemetryTimestamp = 0;
const TELEMETRY_MIN_INTERVAL_MS = 60_000;

/**
 * CRIT-006 AC5-AC6: Classify connection errors to distinguish misconfiguration from temporary failures.
 */
function classifyConnectionError(error: unknown): {
  backend_url_valid: boolean;
  severity: "CRITICAL" | "WARNING";
  errorType: string;
} {
  const msg = error instanceof Error ? error.message : String(error);

  // DNS resolution failure — almost certainly misconfiguration
  if (msg.includes("ENOTFOUND") || msg.includes("getaddrinfo") || msg.includes("DNS")) {
    return { backend_url_valid: false, severity: "CRITICAL", errorType: "dns_resolution_failed" };
  }

  // Connection refused — host exists but port wrong or service down
  if (msg.includes("ECONNREFUSED") || msg.includes("connect ECONNREFUSED")) {
    return { backend_url_valid: false, severity: "WARNING", errorType: "connection_refused" };
  }

  // Timeout — service exists but slow (temporary)
  if (msg.includes("AbortError") || msg.includes("timeout") || msg.includes("ETIMEDOUT")) {
    return { backend_url_valid: true, severity: "WARNING", errorType: "timeout" };
  }

  // Other errors — assume temporary
  return { backend_url_valid: true, severity: "WARNING", errorType: "unknown" };
}

export async function GET() {
  const backendUrl = process.env.BACKEND_URL;

  if (!backendUrl) {
    console.error("[HEALTH] CRITICAL: BACKEND_URL not configured");
    return NextResponse.json(
      { status: "misconfigured", backend: "not configured", error: "BACKEND_URL missing" },
      { status: 503 }
    );
  }

  const startTime = Date.now();
  const probeUrl = `${backendUrl}/health`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(probeUrl, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });

    clearTimeout(timeoutId);
    const latencyMs = Date.now() - startTime;

    if (!response.ok) {
      // AC8: Descriptive log with URL, status, latency
      const statusNote = response.status === 404
        ? " (endpoint may not exist or backend may be restarting)"
        : "";
      console.warn(
        `[HealthCheck] Backend probe failed: GET ${probeUrl} → ${response.status} (${latencyMs}ms)${statusNote}`
      );

      // AC7: Emit rate-limited telemetry event
      emitHealthTelemetry("unhealthy", response.status, latencyMs, probeUrl);

      return NextResponse.json(
        { status: "healthy", backend: "unhealthy", latency_ms: latencyMs },
        { status: 200 }
      );
    }

    // CRIT-010 AC8: Parse ready field — backend may be up but not yet ready
    const body = await response.json();
    const backendStatus = body.ready === false ? "starting" : "healthy";

    return NextResponse.json(
      { status: "healthy", backend: backendStatus, latency_ms: latencyMs },
      { status: 200 }
    );
  } catch (error) {
    const latencyMs = Date.now() - startTime;
    const errorMessage = error instanceof Error ? error.message : "unknown error";
    const { backend_url_valid, severity, errorType } = classifyConnectionError(error);

    // CRIT-006 AC4: Log severity based on error type
    const logMsg = `[HEALTH] ${severity}: BACKEND_URL '${backendUrl}' unreachable — ${errorType}: ${errorMessage}`;
    if (severity === "CRITICAL") {
      console.error(logMsg);
    } else {
      console.warn(logMsg);
    }

    // AC7: Emit rate-limited telemetry event
    emitHealthTelemetry("unreachable", 0, latencyMs, probeUrl);

    return NextResponse.json(
      {
        status: "healthy",
        backend: "unreachable",
        backend_url_valid,
        latency_ms: latencyMs,
        ...(backend_url_valid === false && { warning: `BACKEND_URL may be misconfigured: ${errorType}` }),
      },
      { status: 200 }
    );
  }
}

/** AC7: Rate-limited telemetry emission (max 1/min) */
function emitHealthTelemetry(
  backendStatus: string,
  httpStatus: number,
  latencyMs: number,
  url: string,
) {
  const now = Date.now();
  if (now - lastTelemetryTimestamp < TELEMETRY_MIN_INTERVAL_MS) return;
  lastTelemetryTimestamp = now;

  // Emit to console as structured event (picked up by log aggregators)
  console.warn(JSON.stringify({
    event: "backend_health_check_failed",
    status: backendStatus,
    http_status: httpStatus,
    latency_ms: latencyMs,
    backend_url: url,
    timestamp: new Date(now).toISOString(),
  }));
}
