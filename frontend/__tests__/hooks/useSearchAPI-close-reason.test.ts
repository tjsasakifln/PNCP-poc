/**
 * STORY-422 (EPIC-INCIDENT-2026-04-10): Static guards for the close_reason
 * instrumentation added to useSearchAPI and useSearchExecutionImpl.
 *
 * Rather than spinning up the full React tree (which requires Supabase, auth,
 * SSE, analytics, quota, and toast providers), we assert the presence of the
 * close_reason markers in the production source. This is the same pattern
 * used by STORY-280's billing tests — it catches regressions at the
 * source-code level without pulling a fragile mock surface into CI.
 */
import * as fs from "node:fs";
import * as path from "node:path";

const ROOT = path.resolve(__dirname, "..", "..");

function readSource(rel: string): string {
  return fs.readFileSync(path.join(ROOT, rel), "utf-8");
}

describe("STORY-422: abort reason instrumentation", () => {
  test("useSearchAPI tags timeout aborts with DOMException('TIMEOUT')", () => {
    const src = readSource("app/buscar/hooks/execution/useSearchAPI.ts");
    expect(src).toMatch(/abortController\.abort\(\s*timeoutReason\s*\)/);
    expect(src).toMatch(/new DOMException\(\s*"TIMEOUT"/);
    expect(src).toMatch(/STORY-422/);
  });

  test("useSearchAPI derives closeReason from signal.reason in catch", () => {
    const src = readSource("app/buscar/hooks/execution/useSearchAPI.ts");
    expect(src).toMatch(/signalReason/);
    expect(src).toMatch(/close_reason/);
    expect(src).toMatch(/USER_CANCELLED/);
    expect(src).toMatch(/NAVIGATION/);
  });

  test("useSearchAPI exposes cancelSearch in the hook return type", () => {
    const src = readSource("app/buscar/hooks/execution/useSearchAPI.ts");
    expect(src).toMatch(/cancelSearch:\s*\(\)\s*=>\s*void/);
    expect(src).toMatch(/const cancelSearch = useCallback/);
    expect(src).toMatch(/new DOMException\(\s*"USER_CANCELLED"/);
  });

  test("useSearchExecutionImpl.cancelSearch marks abort with USER_CANCELLED", () => {
    const src = readSource("app/buscar/hooks/execution/useSearchExecutionImpl.ts");
    // Verify the explicit reason is used
    expect(src).toMatch(/new DOMException\(\s*"USER_CANCELLED"/);
    expect(src).toMatch(/STORY-422/);
  });

  test("useSearchAPI emits Sentry breadcrumb with close_reason tag", () => {
    const src = readSource("app/buscar/hooks/execution/useSearchAPI.ts");
    expect(src).toMatch(/addBreadcrumb/);
    expect(src).toMatch(/setTag\(\s*"close_reason"/);
  });

  test("USER_CANCELLED / NAVIGATION path exits silently without retry", () => {
    const src = readSource("app/buscar/hooks/execution/useSearchAPI.ts");
    // Ensure the early return is present before the timeout recovery branch
    expect(src).toMatch(
      /closeReason === "USER_CANCELLED"[\s\S]{0,160}return;/
    );
  });
});
