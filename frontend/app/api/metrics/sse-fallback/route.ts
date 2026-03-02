/**
 * STORY-359 AC4: SSE fallback telemetry proxy.
 * POST /api/metrics/sse-fallback → backend POST /v1/metrics/sse-fallback
 *
 * Fire-and-forget from frontend when SSE falls back to simulated progress.
 * No auth required — just increments a Prometheus counter.
 */

import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST() {
  try {
    await fetch(`${BACKEND_URL}/v1/metrics/sse-fallback`, {
      method: "POST",
      signal: AbortSignal.timeout(5000),
    });
    return new NextResponse(null, { status: 204 });
  } catch {
    // Fire-and-forget: don't fail the client if backend is unreachable
    return new NextResponse(null, { status: 204 });
  }
}
