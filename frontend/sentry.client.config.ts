import * as Sentry from "@sentry/nextjs";

// STORY-211 AC6: Client-side Sentry initialization
// AC18: Graceful no-op when DSN is not configured
const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    tracesSampleRate: 0.1,
    environment: process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV,

    // GTM-STAB-006 AC6: Reduce SSE proxy noise in Sentry
    beforeSend(event) {
      const message = event.exception?.values?.[0]?.value || "";
      // Expected SSE pipe errors during long searches — downgrade to warning
      if (
        message.includes("failed to pipe") ||
        message.includes("BodyTimeoutError") ||
        (message.includes("TypeError") && message.includes("terminated"))
      ) {
        event.level = "warning";
        event.tags = { ...event.tags, sse_pipe_error: "true" };
        // Drop if > 110s elapsed (expected timeout, not actionable)
        const elapsed = event.tags?.elapsed_ms;
        if (typeof elapsed === "number" && elapsed > 110000) {
          return null;
        }
      }
      return event;
    },
  });
}
