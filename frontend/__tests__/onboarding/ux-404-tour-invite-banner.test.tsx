/**
 * UX-404: Tour de resultados bloqueia visualização — reposicionar trigger
 *
 * Tests:
 * - AC1: Tour de resultados NÃO inicia automaticamente
 * - AC2: Banner aparece quando isResultsTourCompleted() retorna false
 * - AC3: Banner desaparece após 10s
 * - AC3b: Banner desaparece no scroll
 * - AC4: Clicar "Iniciar tour" chama startResultsTour()
 * - AC5: Banner não aparece quando tour já completado
 */

import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { TourInviteBanner } from "../../app/buscar/components/SearchResults";

describe("UX-404: Tour invite banner", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  // AC1: Tour does NOT auto-start — the startTour callback is never called without user click
  it("AC1: results tour does NOT auto-start automatically", () => {
    const startTour = jest.fn();
    render(<TourInviteBanner isCompleted={() => false} onStartTour={startTour} />);

    act(() => { jest.advanceTimersByTime(5000); });
    expect(startTour).not.toHaveBeenCalled();
  });

  // AC2: Banner appears when tour not completed
  it("AC2: banner appears when isCompleted returns false", () => {
    render(<TourInviteBanner isCompleted={() => false} onStartTour={jest.fn()} />);

    expect(screen.getByTestId("tour-invite-banner")).toBeInTheDocument();
    expect(screen.getByText(/Primeira vez vendo resultados/)).toBeInTheDocument();
    expect(screen.getByTestId("tour-invite-start")).toHaveTextContent("Iniciar tour");
  });

  // AC3: Banner disappears after 10s
  it("AC3: banner disappears after 10 seconds", () => {
    render(<TourInviteBanner isCompleted={() => false} onStartTour={jest.fn()} />);

    expect(screen.getByTestId("tour-invite-banner")).toBeInTheDocument();

    act(() => { jest.advanceTimersByTime(10_000); });

    expect(screen.queryByTestId("tour-invite-banner")).not.toBeInTheDocument();
  });

  // AC3b: Banner disappears on scroll
  it("AC3: banner disappears when user scrolls", () => {
    render(<TourInviteBanner isCompleted={() => false} onStartTour={jest.fn()} />);

    expect(screen.getByTestId("tour-invite-banner")).toBeInTheDocument();

    act(() => { fireEvent.scroll(window); });

    expect(screen.queryByTestId("tour-invite-banner")).not.toBeInTheDocument();
  });

  // AC4: Clicking "Iniciar tour" calls startResultsTour
  it("AC4: clicking 'Iniciar tour' calls onStartTour", () => {
    const startTour = jest.fn();
    render(<TourInviteBanner isCompleted={() => false} onStartTour={startTour} />);

    fireEvent.click(screen.getByTestId("tour-invite-start"));

    expect(startTour).toHaveBeenCalledTimes(1);
    // Banner should disappear after clicking
    expect(screen.queryByTestId("tour-invite-banner")).not.toBeInTheDocument();
  });

  // AC5: Banner does NOT appear when tour already completed
  it("AC5: banner does not appear when tour already completed", () => {
    render(<TourInviteBanner isCompleted={() => true} onStartTour={jest.fn()} />);

    expect(screen.queryByTestId("tour-invite-banner")).not.toBeInTheDocument();
  });

  // Additional: Close button dismisses banner
  it("close button dismisses banner", () => {
    render(<TourInviteBanner isCompleted={() => false} onStartTour={jest.fn()} />);

    expect(screen.getByTestId("tour-invite-banner")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("tour-invite-close"));

    expect(screen.queryByTestId("tour-invite-banner")).not.toBeInTheDocument();
  });

  // Additional: Banner does not appear when isCompleted not provided
  it("banner does not appear when isCompleted not provided", () => {
    render(<TourInviteBanner />);

    expect(screen.queryByTestId("tour-invite-banner")).not.toBeInTheDocument();
  });
});
