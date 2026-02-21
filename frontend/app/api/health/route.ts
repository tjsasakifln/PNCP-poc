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
 */

// AC7: Rate limit telemetry events to max 1 per minute
let lastTelemetryTimestamp = 0;
const TELEMETRY_MIN_INTERVAL_MS = 60_000;

export async function GET() {
  const backendUrl = process.env.BACKEND_URL;

  if (!backendUrl) {
    return NextResponse.json(
      { status: "healthy", backend: "not configured" },
      { status: 200 }
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

    // AC8: Descriptive log
    console.warn(
      `[HealthCheck] Backend probe failed: GET ${probeUrl} → unreachable (${latencyMs}ms) — ${errorMessage}`
    );

    // AC7: Emit rate-limited telemetry event
    emitHealthTelemetry("unreachable", 0, latencyMs, probeUrl);

    return NextResponse.json(
      { status: "healthy", backend: "unreachable", latency_ms: latencyMs },
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
