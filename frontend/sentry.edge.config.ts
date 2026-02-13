import * as Sentry from "@sentry/nextjs";

// STORY-211 AC6: Edge runtime Sentry initialization
const dsn = process.env.SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    tracesSampleRate: 0.1,
    environment: process.env.ENVIRONMENT || process.env.NODE_ENV,
  });
}
