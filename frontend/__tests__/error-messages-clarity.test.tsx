/**
 * CRIT-082 AC11: Error message clarity tests.
 *
 * Verifies:
 * - getRetryMessage(502/503) returns "O servidor está se atualizando."
 * - SearchErrorBanner shows countdown number alongside retry message
 * - Exhausted message is "Não foi possível conectar ao servidor."
 * - Other codes keep their existing messages
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { getRetryMessage } from "../lib/error-messages";
import { SearchErrorBanner } from "../app/buscar/components/SearchErrorBanner";
import type { HumanizedError } from "../lib/error-messages";

// Mock next/link as a simple anchor
jest.mock("next/link", () => {
  const Link = ({ children, href, ...rest }: { children: React.ReactNode; href: string }) => (
    <a href={href} {...rest}>{children}</a>
  );
  Link.displayName = "Link";
  return Link;
});

// ---------------------------------------------------------------------------
// getRetryMessage
// ---------------------------------------------------------------------------

describe("CRIT-082 AC11: getRetryMessage clarity", () => {
  it("502 returns 'O servidor está se atualizando.'", () => {
    expect(getRetryMessage(502)).toBe("O servidor está se atualizando.");
  });

  it("503 returns 'O servidor está se atualizando.'", () => {
    expect(getRetryMessage(503)).toBe("O servidor está se atualizando.");
  });

  it("504 keeps timeout message unchanged", () => {
    const msg = getRetryMessage(504);
    expect(msg).toContain("demorando");
  });

  it("network error message mentions conexão", () => {
    const msg = getRetryMessage(null, "fetch failed");
    expect(msg.toLowerCase()).toMatch(/conex/);
  });

  it("generic fallback still tries automatically", () => {
    const msg = getRetryMessage(null, "some random error");
    expect(msg.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// SearchErrorBanner — countdown display (AC4)
// ---------------------------------------------------------------------------

const baseHumanizedError: HumanizedError = {
  message: "Nossos servidores estão se atualizando.",
  actionLabel: "Tentar novamente",
  tone: "blue",
  suggestReduceScope: false,
};

describe("CRIT-082 AC4: SearchErrorBanner countdown display", () => {
  it("shows retry message with countdown seconds when retryCountdown is set", () => {
    render(
      <SearchErrorBanner
        humanizedError={baseHumanizedError}
        retryCountdown={10}
        retryMessage="O servidor está se atualizando."
        retryExhausted={false}
        onRetry={jest.fn()}
      />
    );

    expect(screen.getByText(/O servidor está se atualizando\. \(10s\)/)).toBeInTheDocument();
  });

  it("does not show countdown paragraph when retryCountdown is null", () => {
    render(
      <SearchErrorBanner
        humanizedError={baseHumanizedError}
        retryCountdown={null}
        retryMessage={null}
        retryExhausted={false}
        onRetry={jest.fn()}
      />
    );

    expect(screen.queryByText(/\(.*s\)/)).not.toBeInTheDocument();
  });

  it("shows countdown = 1s correctly", () => {
    render(
      <SearchErrorBanner
        humanizedError={baseHumanizedError}
        retryCountdown={1}
        retryMessage="O servidor está se atualizando."
        retryExhausted={false}
        onRetry={jest.fn()}
      />
    );

    expect(screen.getByText(/\(1s\)/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// SearchErrorBanner — exhausted message (AC5)
// ---------------------------------------------------------------------------

describe("CRIT-082 AC5: SearchErrorBanner exhausted message", () => {
  it("shows correct exhausted message with proper encoding", () => {
    render(
      <SearchErrorBanner
        humanizedError={baseHumanizedError}
        retryCountdown={null}
        retryMessage={null}
        retryExhausted={true}
        onRetry={jest.fn()}
      />
    );

    expect(
      screen.getByText("Não foi possível conectar ao servidor. Tente novamente em alguns minutos.")
    ).toBeInTheDocument();
  });

  it("does not show old 'Nao conseguimos' message", () => {
    render(
      <SearchErrorBanner
        humanizedError={baseHumanizedError}
        retryCountdown={null}
        retryMessage={null}
        retryExhausted={true}
        onRetry={jest.fn()}
      />
    );

    expect(screen.queryByText(/Nao conseguimos/)).not.toBeInTheDocument();
  });

  it("does not show exhausted message when retryExhausted is false", () => {
    render(
      <SearchErrorBanner
        humanizedError={baseHumanizedError}
        retryCountdown={null}
        retryMessage={null}
        retryExhausted={false}
        onRetry={jest.fn()}
      />
    );

    expect(
      screen.queryByText(/Não foi possível conectar ao servidor/)
    ).not.toBeInTheDocument();
  });
});
