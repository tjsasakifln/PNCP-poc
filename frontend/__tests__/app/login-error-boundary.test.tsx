/**
 * STORY-421 (EPIC-INCIDENT-2026-04-10): Unit tests for /login error.tsx
 *
 * Covers:
 *  - Renders user-friendly fallback UI for generic errors.
 *  - Detects RSC/InvariantError and switches button to hard-reload flow.
 *  - Reports to Sentry with `page: 'login'` tag.
 *  - Offers safe escape hatches (home link, signup link).
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

const captureExceptionMock = jest.fn();

jest.mock("@sentry/nextjs", () => ({
  __esModule: true,
  captureException: (...args: unknown[]) => captureExceptionMock(...args),
}));

import LoginError from "@/app/login/error";

const originalConsoleError = console.error;
const originalLocation = window.location;

beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

describe("STORY-421 /login error boundary", () => {
  const mockReset = jest.fn();

  beforeEach(() => {
    mockReset.mockClear();
    captureExceptionMock.mockClear();
    (console.error as jest.Mock).mockClear();
    // Provide a mockable location for reload assertions
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...originalLocation, reload: jest.fn() },
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: originalLocation,
    });
  });

  // AC4: error boundary renders a friendly fallback
  it("renders user-friendly fallback UI for generic errors", () => {
    const err = new Error("Random runtime failure");
    render(<LoginError error={err} reset={mockReset} />);

    expect(
      screen.getByRole("heading", { level: 1, name: /Problema ao carregar a página de login/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Ocorreu um erro inesperado/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Tentar novamente/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Voltar ao início/i })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Criar conta gratuita/i })
    ).toBeInTheDocument();
  });

  // AC4: Sentry capture with page tag
  it("reports to Sentry with page=login and error_type tag", () => {
    const err = new Error("Random runtime failure");
    render(<LoginError error={err} reset={mockReset} />);

    expect(captureExceptionMock).toHaveBeenCalledTimes(1);
    const [reportedError, options] = captureExceptionMock.mock.calls[0] as [
      Error,
      { tags: Record<string, string>; extra: Record<string, unknown> }
    ];
    expect(reportedError).toBe(err);
    expect(options.tags.page).toBe("login");
    expect(options.tags.error_type).toBe("runtime_error");
    expect(options.extra.rsc_invariant).toBe(false);
  });

  // AC2+AC4: RSC invariant detection
  it("flags RSC invariant errors with error_type=rsc_invariant", () => {
    const err = new Error(
      "InvariantError: Expected RSC response, got text/plain. This is a bug in Next.js."
    );
    render(<LoginError error={err} reset={mockReset} />);

    const [, options] = captureExceptionMock.mock.calls[0] as [
      Error,
      { tags: Record<string, string>; extra: Record<string, unknown> }
    ];
    expect(options.tags.error_type).toBe("rsc_invariant");
    expect(options.extra.rsc_invariant).toBe(true);

    expect(
      screen.getByText(/inconsistência temporária ao carregar a página/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Atualizar página/i })
    ).toBeInTheDocument();
  });

  // AC3: reset path for regular errors
  it("calls reset() on primary button click for generic errors", () => {
    const err = new Error("Random runtime failure");
    render(<LoginError error={err} reset={mockReset} />);

    fireEvent.click(screen.getByRole("button", { name: /Tentar novamente/i }));
    expect(mockReset).toHaveBeenCalledTimes(1);
    expect(window.location.reload).not.toHaveBeenCalled();
  });

  // AC3 + AC4: hard reload path for RSC invariant
  it("forces hard reload on primary button click for RSC invariant errors", () => {
    const err = new Error("InvariantError: Expected RSC response, got text/plain.");
    render(<LoginError error={err} reset={mockReset} />);

    fireEvent.click(screen.getByRole("button", { name: /Atualizar página/i }));
    expect(window.location.reload).toHaveBeenCalledTimes(1);
    // reset() must NOT be called because the same segment would re-throw
    expect(mockReset).not.toHaveBeenCalled();
  });

  // AC4: digest surfacing
  it("renders diagnostic digest when available", () => {
    const err = Object.assign(new Error("boom"), { digest: "abc-digest-123" });
    render(<LoginError error={err} reset={mockReset} />);

    expect(screen.getByText(/abc-digest-123/)).toBeInTheDocument();
  });
});
