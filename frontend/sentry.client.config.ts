import * as Sentry from "@sentry/nextjs";

// STORY-211 AC6: Client-side Sentry initialization
// AC18: Graceful no-op when DSN is not configured
const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    tracesSampleRate: 0.1,
    environment: process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV,
  });
}
