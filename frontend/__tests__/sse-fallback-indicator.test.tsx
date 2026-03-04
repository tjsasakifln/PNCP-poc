/**
 * STORY-359 AC5: SSE Fallback Indicator Tests
 *
 * Tests the lifecycle:
 * - SSE fail → indicator appears
 * - SSE reconnect → indicator disappears
 * - AC3: indicator is gray/blue, NOT red
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { EnhancedLoadingProgress } from "../components/EnhancedLoadingProgress";

describe("STORY-359: SSE Fallback Indicator", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  describe("AC1: Indicator appears when SSE falls back to simulation", () => {
    it("should show fallback indicator when sseDisconnected=true", () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={true}
        />
      );

      const indicator = screen.getByTestId("sse-fallback-indicator");
      expect(indicator).toBeInTheDocument();
      expect(
        screen.getByText(
          /Progresso estimado \(conexão em tempo real indisponível\)/
        )
      ).toBeInTheDocument();
    });

    it("should show tooltip with detailed explanation", () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={true}
        />
      );

      const tooltipElement = screen.getByTitle(
        /A conexão em tempo real não está disponível/
      );
      expect(tooltipElement).toBeInTheDocument();
    });

    it("should show info icon (SVG) in fallback indicator", () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={true}
        />
      );

      const indicator = screen.getByTestId("sse-fallback-indicator");
      const svg = indicator.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });
  });

  describe("AC2: Indicator disappears when SSE reconnects", () => {
    it("should show real-time indicator when SSE is active", () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={false}
          sseEvent={{ stage: "fetching", progress: 30, message: "Analisando...", detail: {} }}
        />
      );

      expect(screen.queryByTestId("sse-fallback-indicator")).not.toBeInTheDocument();
      expect(screen.getByTestId("sse-realtime-indicator")).toBeInTheDocument();
      expect(screen.getByText("Progresso em tempo real")).toBeInTheDocument();
    });

    it("should transition from fallback to real-time when SSE reconnects", () => {
      const { rerender } = render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={true}
        />
      );

      // Fallback indicator visible
      expect(screen.getByTestId("sse-fallback-indicator")).toBeInTheDocument();
      expect(screen.queryByTestId("sse-realtime-indicator")).not.toBeInTheDocument();

      // SSE reconnects
      rerender(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={false}
          sseEvent={{ stage: "fetching", progress: 45, message: "Analisando...", detail: {} }}
        />
      );

      // Fallback indicator gone, real-time indicator shown
      expect(screen.queryByTestId("sse-fallback-indicator")).not.toBeInTheDocument();
      expect(screen.getByTestId("sse-realtime-indicator")).toBeInTheDocument();
    });

    it("should show no indicator when SSE not connected and no event yet", () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={false}
        />
      );

      expect(screen.queryByTestId("sse-fallback-indicator")).not.toBeInTheDocument();
      expect(screen.queryByTestId("sse-realtime-indicator")).not.toBeInTheDocument();
    });
  });

  describe("AC3: Non-blocking UX — gray/blue, not red", () => {
    it("should use slate/gray color for fallback indicator icon, NOT red", () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={true}
        />
      );

      const indicator = screen.getByTestId("sse-fallback-indicator");
      const svg = indicator.querySelector("svg");
      expect(svg).toBeInTheDocument();

      // Should have slate/gray classes, NOT red
      const svgClasses = svg?.getAttribute("class") || "";
      expect(svgClasses).toMatch(/slate/);
      expect(svgClasses).not.toMatch(/red/);
      expect(svgClasses).not.toMatch(/error/);
    });

    it("should use muted text color (text-ink-muted), NOT alert colors", () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={true}
        />
      );

      const indicator = screen.getByTestId("sse-fallback-indicator");
      expect(indicator.className).toMatch(/text-\[10px\]/);
      expect(indicator.className).toMatch(/text-ink-muted/);
      // Should NOT have alert/error/warning classes
      expect(indicator.className).not.toMatch(/bg-red/);
      expect(indicator.className).not.toMatch(/bg-amber/);
      expect(indicator.className).not.toMatch(/border/);
    });

    it("should NOT have a banner-like appearance (no background, no border)", () => {
      render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={true}
        />
      );

      const indicator = screen.getByTestId("sse-fallback-indicator");
      // Discrete indicator: no bg-*, no border, no p-3 padding (unlike old banner)
      expect(indicator.className).not.toMatch(/bg-blue/);
      expect(indicator.className).not.toMatch(/rounded-lg/);
      expect(indicator.className).not.toMatch(/p-3/);
    });
  });

  describe("AC5: Full lifecycle — SSE fail → indicator → reconnect → gone", () => {
    it("should follow complete lifecycle: no indicator → fallback → reconnect → real-time", () => {
      const { rerender } = render(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={false}
        />
      );

      // Phase 1: No SSE yet — no indicator
      expect(screen.queryByTestId("sse-fallback-indicator")).not.toBeInTheDocument();
      expect(screen.queryByTestId("sse-realtime-indicator")).not.toBeInTheDocument();

      // Phase 2: SSE connects — real-time indicator
      rerender(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={false}
          sseEvent={{ stage: "connecting", progress: 5, message: "Conectando...", detail: {} }}
        />
      );
      expect(screen.getByTestId("sse-realtime-indicator")).toBeInTheDocument();

      // Phase 3: SSE fails — fallback indicator
      rerender(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={true}
          sseEvent={null}
        />
      );
      expect(screen.getByTestId("sse-fallback-indicator")).toBeInTheDocument();
      expect(screen.queryByTestId("sse-realtime-indicator")).not.toBeInTheDocument();
      expect(
        screen.getByText(/Progresso estimado/)
      ).toBeInTheDocument();

      // Phase 4: SSE reconnects — real-time indicator restored
      rerender(
        <EnhancedLoadingProgress
          currentStep={1}
          estimatedTime={60}
          stateCount={3}
          sseDisconnected={false}
          sseEvent={{ stage: "fetching", progress: 35, message: "Buscando dados", detail: {} }}
        />
      );
      expect(screen.queryByTestId("sse-fallback-indicator")).not.toBeInTheDocument();
      expect(screen.getByTestId("sse-realtime-indicator")).toBeInTheDocument();
      expect(screen.getByText("Progresso em tempo real")).toBeInTheDocument();
    });
  });
});
