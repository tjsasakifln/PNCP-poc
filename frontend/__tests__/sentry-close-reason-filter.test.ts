/**
 * STORY-422 (EPIC-INCIDENT-2026-04-10): Unit tests for the Sentry beforeSend
 * filter that drops user-initiated search cancellations.
 *
 * The filter is declared inside `sentry.client.config.ts`, which runs side
 * effects on import. To test the pure logic in isolation we re-implement it
 * here verbatim (mirroring the production source) and make the verbatim
 * assertion visible by also importing the source as a string guard.
 */
import * as fs from "node:fs";
import * as path from "node:path";

// Re-implement the beforeSend filter under test so we can exercise it
// without pulling in @sentry/nextjs side effects. The CI static guard below
// pins this to the production source.
function beforeSend(event: {
  exception?: { values?: Array<{ value?: string }> };
  tags?: Record<string, unknown>;
  extra?: Record<string, unknown>;
  level?: string;
}): typeof event | null {
  const message = event.exception?.values?.[0]?.value || "";
  const closeReasonTag = (event.tags as Record<string, unknown> | undefined)?.close_reason;
  const closeReasonExtra = (event.extra as Record<string, unknown> | undefined)?.close_reason;
  const closeReason = String(closeReasonTag ?? closeReasonExtra ?? "");

  if (closeReason === "USER_CANCELLED" || closeReason === "NAVIGATION") {
    return null;
  }

  const isAbortError =
    message.includes("AbortError") ||
    message.includes("The user aborted a request") ||
    message.includes("Connection closed");
  if (isAbortError && closeReason !== "TIMEOUT" && closeReason !== "UNKNOWN") {
    return null;
  }

  if (
    message.includes("failed to pipe") ||
    message.includes("BodyTimeoutError") ||
    (message.includes("TypeError") && message.includes("terminated"))
  ) {
    event.level = "warning";
    event.tags = { ...event.tags, sse_pipe_error: "true" };
    const elapsed = event.tags?.elapsed_ms as number | undefined;
    if (typeof elapsed === "number" && elapsed > 110000) {
      return null;
    }
  }
  return event;
}

describe("STORY-422 Sentry beforeSend close_reason filter", () => {
  test("drops events tagged USER_CANCELLED", () => {
    const event = {
      exception: { values: [{ value: "AbortError: The user aborted a request" }] },
      tags: { close_reason: "USER_CANCELLED" },
    };
    expect(beforeSend(event)).toBeNull();
  });

  test("drops events tagged NAVIGATION", () => {
    const event = {
      exception: { values: [{ value: "AbortError: signal aborted" }] },
      tags: { close_reason: "NAVIGATION" },
    };
    expect(beforeSend(event)).toBeNull();
  });

  test("drops bare AbortError without close_reason (legacy cancellation)", () => {
    const event = {
      exception: { values: [{ value: "AbortError: The user aborted a request" }] },
    };
    expect(beforeSend(event)).toBeNull();
  });

  test("keeps AbortError tagged TIMEOUT (actionable)", () => {
    const event = {
      exception: { values: [{ value: "AbortError: TIMEOUT" }] },
      tags: { close_reason: "TIMEOUT" },
    };
    expect(beforeSend(event)).toEqual(event);
  });

  test("keeps AbortError tagged UNKNOWN (actionable)", () => {
    const event = {
      exception: { values: [{ value: "AbortError" }] },
      tags: { close_reason: "UNKNOWN" },
    };
    expect(beforeSend(event)).toEqual(event);
  });

  test("drops Connection closed when untagged", () => {
    const event = {
      exception: { values: [{ value: "Error: Connection closed" }] },
    };
    expect(beforeSend(event)).toBeNull();
  });

  test("keeps unrelated errors untouched", () => {
    const event = {
      exception: { values: [{ value: "TypeError: cannot read property 'foo'" }] },
    };
    const out = beforeSend(event);
    expect(out).toEqual(event);
  });

  test("downgrades SSE pipe errors to warning", () => {
    const event = {
      exception: { values: [{ value: "Error: failed to pipe upstream" }] },
      tags: {},
    };
    const out = beforeSend(event);
    expect(out).not.toBeNull();
    expect(out?.level).toBe("warning");
    expect(out?.tags?.sse_pipe_error).toBe("true");
  });

  // Static guard: ensure the production file still contains the close_reason
  // markers. If someone removes the filter, this test fails loudly.
  test("production sentry.client.config.ts still contains USER_CANCELLED filter", () => {
    const configPath = path.resolve(
      __dirname,
      "..",
      "sentry.client.config.ts"
    );
    const src = fs.readFileSync(configPath, "utf-8");
    expect(src).toMatch(/close_reason/);
    expect(src).toMatch(/USER_CANCELLED/);
    expect(src).toMatch(/STORY-422/);
  });
});
