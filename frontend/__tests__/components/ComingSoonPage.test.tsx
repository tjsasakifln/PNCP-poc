/**
 * DEBT-FE-012: ComingSoonPage component tests
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ComingSoonPage } from "../../components/ComingSoonPage";

describe("ComingSoonPage (DEBT-FE-012)", () => {
  it("renders with title and description", () => {
    render(
      <ComingSoonPage
        title="Alertas por E-mail"
        description="Receba notificacoes automaticas."
      />
    );
    expect(screen.getByTestId("coming-soon-page")).toBeInTheDocument();
    expect(screen.getByText("Em breve")).toBeInTheDocument();
    expect(screen.getByText("Alertas por E-mail")).toBeInTheDocument();
    expect(screen.getByText("Receba notificacoes automaticas.")).toBeInTheDocument();
  });

  it("shows launch estimate when provided", () => {
    render(
      <ComingSoonPage
        title="Test Feature"
        description="Test description"
        launchEstimate="Abril 2026"
      />
    );
    expect(screen.getByText(/Previsao: Abril 2026/)).toBeInTheDocument();
  });

  it("does not show launch estimate when not provided", () => {
    render(
      <ComingSoonPage
        title="Test Feature"
        description="Test description"
      />
    );
    expect(screen.queryByText(/Previsao:/)).not.toBeInTheDocument();
  });

  it("shows notify button", () => {
    render(
      <ComingSoonPage
        title="Test Feature"
        description="Test description"
      />
    );
    expect(screen.getByTestId("coming-soon-notify-btn")).toBeInTheDocument();
    expect(screen.getByText("Avise-me quando lancar")).toBeInTheDocument();
  });

  it("toggles to notified state on click", () => {
    const onNotify = jest.fn();
    render(
      <ComingSoonPage
        title="Test Feature"
        description="Test description"
        onNotifyRequest={onNotify}
      />
    );

    fireEvent.click(screen.getByTestId("coming-soon-notify-btn"));

    expect(onNotify).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("coming-soon-notified")).toBeInTheDocument();
    expect(
      screen.getByText("Voce sera notificado quando estiver disponivel")
    ).toBeInTheDocument();
    // Button should be gone
    expect(screen.queryByTestId("coming-soon-notify-btn")).not.toBeInTheDocument();
  });

  it("works without onNotifyRequest callback", () => {
    render(
      <ComingSoonPage
        title="Test Feature"
        description="Test description"
      />
    );

    // Should not throw
    fireEvent.click(screen.getByTestId("coming-soon-notify-btn"));
    expect(screen.getByTestId("coming-soon-notified")).toBeInTheDocument();
  });
});
