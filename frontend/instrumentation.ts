// STORY-211: Next.js instrumentation hook for Sentry server-side initialization
import * as Sentry from "@sentry/nextjs";

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  }

  if (process.env.NEXT_RUNTIME === "edge") {
    await import("./sentry.edge.config");
  }

  // CRIT-006 AC8: Validate BACKEND_URL on startup
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    console.error(
      "[STARTUP] CRITICAL: BACKEND_URL not configured — " +
      "frontend cannot proxy API requests to backend. " +
      "All /api/buscar requests will fail with 503."
    );
  } else {
    try {
      new URL(backendUrl); // Validate URL format
      console.log(`[STARTUP] BACKEND_URL validated: ${backendUrl}`);
    } catch {
      console.error(
        `[STARTUP] CRITICAL: BACKEND_URL is not a valid URL: '${backendUrl}'. ` +
        `All /api/buscar requests will fail.`
      );
    }
  }
}

// Capture server component and API route errors automatically
export const onRequestError = Sentry.captureRequestError;
