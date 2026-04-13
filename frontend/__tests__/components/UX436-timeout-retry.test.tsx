/**
 * UX-436: Adaptive retry on timeout
 *
 * Tests all 5 ACs:
 * AC1: Shows which UFs completed vs. failed
 * AC2: Primary button retries only completed UFs
 * AC3: Secondary button retries all UFs (current behavior demoted)
 * AC4: With retryExhausted and no completed UFs, suggests top-2 by count
 * AC5: No "Tente com menos estados" instruction text anywhere
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { SearchStateManager } from "../../app/buscar/components/SearchStateManager";
import type { SearchStateManagerProps } from "../../app/buscar/components/SearchStateManager";
import type { UfStatus } from "../../hooks/useSearchSSE";

// ── Helpers ──────────────────────────────────────────────────────────────────

const baseTimeoutError = {
  message: "A busca demorou demais para responder.",
  rawMessage: "timeout: request exceeded limit",
  errorCode: "TIMEOUT" as const,
  searchId: "test-search-id",
  correlationId: null,
  requestId: null,
  httpStatus: 504,
  timestamp: "2026-04-13T10:00:00Z",
};

function makeSnapshot(entries: Record<string, UfStatus>): Map<string, UfStatus> {
  return new Map(Object.entries(entries));
}

function renderSSM(overrides: Partial<SearchStateManagerProps>) {
  const defaults: SearchStateManagerProps = {
    phase: "failed",
    error: null,
    quotaError: null,
    retryCountdown: null,
    retryMessage: null,
    retryExhausted: false,
    onRetry: jest.fn(),
    onRetryNow: jest.fn(),
    onCancelRetry: jest.fn(),
    onCancel: jest.fn(),
    loading: false,
    hasPartialResults: false,
  };
  return render(<SearchStateManager {...defaults} {...overrides} />);
}

// ── AC5: No forbidden instruction text ───────────────────────────────────────

describe("AC5 — no forbidden instruction text", () => {
  it("does not render 'Tente com menos estados' for timeout errors", () => {
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      ufsSelecionadas: new Set(["SP", "PR", "SC", "RS"]),
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 42 },
        PR: { status: "success", count: 18 },
        SC: { status: "failed" },
        RS: { status: "failed" },
      }),
    });
    expect(screen.queryByText(/tente com menos estados/i)).toBeNull();
    expect(screen.queryByText(/quer tentar novamente com menos estados/i)).toBeNull();
  });

  it("does not render 'Tente com menos estados' without snapshot", () => {
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      ufsSelecionadas: new Set(["SP", "PR", "SC"]),
      onRetryWithUfs: jest.fn(),
    });
    expect(screen.queryByText(/tente com menos estados/i)).toBeNull();
  });
});

// ── AC1: Contextual message ────────────────────────────────────────────────

describe("AC1 — contextual UF message", () => {
  it("shows 'SP, PR tiveram resultados — SC, RS não responderam'", () => {
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 42 },
        PR: { status: "success", count: 18 },
        SC: { status: "failed" },
        RS: { status: "failed" },
      }),
    });
    const msg = screen.getByTestId("uf-context-message");
    expect(msg.textContent).toContain("SP, PR");
    expect(msg.textContent).toContain("tiveram resultados");
    expect(msg.textContent).toContain("SC, RS");
    expect(msg.textContent).toContain("não responderam");
  });

  it("shows singular form when only 1 UF completed", () => {
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 10 },
        PR: { status: "failed" },
      }),
    });
    const msg = screen.getByTestId("uf-context-message");
    expect(msg.textContent).toContain("SP teve resultados");
    expect(msg.textContent).toContain("PR não respondeu");
  });

  it("shows message when all UFs completed (no failed)", () => {
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 50 },
        PR: { status: "recovered", count: 20 },
      }),
    });
    const msg = screen.getByTestId("uf-context-message");
    expect(msg.textContent).toContain("SP, PR tiveram resultados");
  });

  it("also shows message in offline-exhausted panel", () => {
    renderSSM({
      phase: "offline",
      error: { ...baseTimeoutError, errorCode: "TIMEOUT" },
      retryExhausted: true,
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 30 },
        RS: { status: "failed" },
      }),
    });
    const msg = screen.getByTestId("uf-context-message");
    expect(msg.textContent).toContain("SP teve resultados");
    expect(msg.textContent).toContain("RS não respondeu");
  });
});

// ── AC2: Primary button retries completed UFs ─────────────────────────────

describe("AC2 — primary button retries completed UFs", () => {
  it("shows 'Buscar apenas SP e PR' button when SP and PR completed", () => {
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 42 },
        PR: { status: "success", count: 18 },
        SC: { status: "failed" },
        RS: { status: "failed" },
      }),
    });
    expect(screen.getByTestId("retry-completed-ufs-button")).toBeTruthy();
    expect(screen.getByTestId("retry-completed-ufs-button").textContent).toContain("SP");
    expect(screen.getByTestId("retry-completed-ufs-button").textContent).toContain("PR");
  });

  it("calls onRetryWithUfs with completed UFs when primary button clicked", () => {
    const onRetryWithUfs = jest.fn();
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      onRetryWithUfs,
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 42 },
        PR: { status: "success", count: 18 },
        SC: { status: "failed" },
        RS: { status: "failed" },
      }),
    });
    fireEvent.click(screen.getByTestId("retry-completed-ufs-button"));
    expect(onRetryWithUfs).toHaveBeenCalledWith(
      expect.arrayContaining(["SP", "PR"])
    );
    // Should not include failed UFs
    const calledWith = onRetryWithUfs.mock.calls[0][0] as string[];
    expect(calledWith).not.toContain("SC");
    expect(calledWith).not.toContain("RS");
  });

  it("includes partial/recovered UFs in primary button", () => {
    const onRetryWithUfs = jest.fn();
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      onRetryWithUfs,
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "partial", count: 5 },
        PR: { status: "recovered", count: 3 },
        SC: { status: "failed" },
      }),
    });
    fireEvent.click(screen.getByTestId("retry-completed-ufs-button"));
    const calledWith = onRetryWithUfs.mock.calls[0][0] as string[];
    expect(calledWith).toContain("SP");
    expect(calledWith).toContain("PR");
  });
});

// ── AC3: Secondary button retries all UFs ────────────────────────────────

describe("AC3 — secondary button retries all UFs (current behavior demoted)", () => {
  it("shows 'Tentar com todas as UFs novamente' button", () => {
    const onRetry = jest.fn();
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      onRetry,
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 10 },
        PR: { status: "failed" },
      }),
    });
    const btn = screen.getByTestId("retry-all-ufs-button");
    expect(btn).toBeTruthy();
    expect(btn.textContent).toContain("todas as UFs");
  });

  it("calls onRetry (not onRetryWithUfs) when secondary button clicked", () => {
    const onRetry = jest.fn();
    const onRetryWithUfs = jest.fn();
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      onRetry,
      onRetryWithUfs,
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 10 },
        PR: { status: "failed" },
      }),
    });
    fireEvent.click(screen.getByTestId("retry-all-ufs-button"));
    expect(onRetry).toHaveBeenCalledTimes(1);
    expect(onRetryWithUfs).not.toHaveBeenCalled();
  });
});

// ── AC4: After retry exhausted with no completions → suggest top 2 by count ──

describe("AC4 — suggest top-2 UFs by count when retryExhausted and nothing completed", () => {
  it("suggests top-2 UFs by result count when retryExhausted and no UF succeeded", () => {
    const onRetryWithUfs = jest.fn();
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      retryExhausted: true,
      onRetryWithUfs,
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "pending", count: 50 },
        RJ: { status: "pending", count: 30 },
        MG: { status: "pending", count: 10 },
        RS: { status: "pending", count: 5 },
      }),
    });
    // Should show adaptive retry with top-2 (SP, RJ)
    expect(screen.getByTestId("uf-reduction-suggestion")).toBeTruthy();
    const primaryBtn = screen.getByTestId("retry-completed-ufs-button");
    expect(primaryBtn.textContent).toContain("SP");
    expect(primaryBtn.textContent).toContain("RJ");
    // Should not show MG or RS
    expect(primaryBtn.textContent).not.toContain("MG");
    expect(primaryBtn.textContent).not.toContain("RS");
  });

  it("calls onRetryWithUfs with top-2 UFs by count", () => {
    const onRetryWithUfs = jest.fn();
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      retryExhausted: true,
      onRetryWithUfs,
      ufStatusesSnapshot: makeSnapshot({
        SC: { status: "failed", count: 100 },
        PR: { status: "failed", count: 80 },
        SP: { status: "failed", count: 20 },
      }),
    });
    fireEvent.click(screen.getByTestId("retry-completed-ufs-button"));
    expect(onRetryWithUfs).toHaveBeenCalledWith(
      expect.arrayContaining(["SC", "PR"])
    );
    const calledWith = onRetryWithUfs.mock.calls[0][0] as string[];
    expect(calledWith.length).toBe(2);
  });

  it("does NOT show adaptive retry when retryExhausted is false and no UF completed", () => {
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      retryExhausted: false,
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "pending", count: 0 },
        PR: { status: "pending", count: 0 },
      }),
    });
    // No adaptive panel — no completed UFs and retryExhausted is false
    expect(screen.queryByTestId("uf-reduction-suggestion")).toBeNull();
  });
});

// ── Edge cases ────────────────────────────────────────────────────────────

describe("edge cases", () => {
  it("does not render adaptive panel when snapshot is empty", () => {
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: new Map(),
    });
    expect(screen.queryByTestId("uf-reduction-suggestion")).toBeNull();
  });

  it("does not render adaptive panel when error is not a timeout", () => {
    renderSSM({
      phase: "failed",
      error: {
        ...baseTimeoutError,
        errorCode: "NETWORK_ERROR",
        httpStatus: 500,
        rawMessage: "connection refused",
      },
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 10 },
      }),
    });
    expect(screen.queryByTestId("uf-reduction-suggestion")).toBeNull();
  });

  it("does not render adaptive panel when onRetryWithUfs is not provided", () => {
    renderSSM({
      phase: "failed",
      error: baseTimeoutError,
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 10 },
        PR: { status: "failed" },
      }),
      // no onRetryWithUfs
    });
    expect(screen.queryByTestId("uf-reduction-suggestion")).toBeNull();
  });

  it("detects timeout via httpStatus 504 even without errorCode", () => {
    renderSSM({
      phase: "failed",
      error: {
        ...baseTimeoutError,
        errorCode: null,
        httpStatus: 504,
      },
      onRetryWithUfs: jest.fn(),
      ufStatusesSnapshot: makeSnapshot({
        SP: { status: "success", count: 5 },
        PR: { status: "failed" },
      }),
    });
    expect(screen.getByTestId("uf-reduction-suggestion")).toBeTruthy();
  });

  it("renders normal 'Tentar novamente' button when no adaptive retry (non-timeout)", () => {
    renderSSM({
      phase: "failed",
      error: {
        ...baseTimeoutError,
        errorCode: "SERVER_ERROR",
        httpStatus: 500,
        rawMessage: "internal server error",
      },
    });
    expect(screen.getByTestId("failed-retry-button")).toBeTruthy();
    expect(screen.queryByTestId("retry-completed-ufs-button")).toBeNull();
  });
});
