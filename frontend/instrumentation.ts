// STORY-211: Next.js instrumentation hook for Sentry server-side initialization
import * as Sentry from "@sentry/nextjs";

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  }

  if (process.env.NEXT_RUNTIME === "edge") {
    await import("./sentry.edge.config");
  }
}

// Capture server component and API route errors automatically
export const onRequestError = Sentry.captureRequestError;
