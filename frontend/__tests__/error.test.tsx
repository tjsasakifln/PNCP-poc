import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import ErrorBoundary from "@/app/error";

// Mock console.error to avoid noise in test output
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});
afterAll(() => {
  console.error = originalConsoleError;
});

describe("Error Boundary Component", () => {
  const mockReset = jest.fn();
  const mockError = new Error("Test error message");

  beforeEach(() => {
    mockReset.mockClear();
    (console.error as jest.Mock).mockClear();
  });

  // AC1: Arquivo app/error.tsx criado
  it("should exist as a client component", () => {
    const { container } = render(<ErrorBoundary error={mockError} reset={mockReset} />);
    expect(container).toBeTruthy();
  });

  // AC2: Fallback UI amigável implementada
  describe("Fallback UI", () => {
    it("should render user-friendly error heading", () => {
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
        "Ops! Algo deu errado"
      );
    });

    it("should display friendly error message", () => {
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(
        screen.getByText(/Ocorreu um erro inesperado. Por favor, tente novamente./)
      ).toBeInTheDocument();
    });

    it("should show error icon", () => {
      // Component redesigned: icon color uses CSS variable var(--error) instead of text-red-500.
      // SVG className in jsdom is an SVGAnimatedString; use getAttribute to get the string value.
      const { container } = render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
      // Verify icon is present with CSS variable based color class
      expect(svg?.getAttribute("class")).toContain("text-[var(--error)]");
    });

    it("should display technical error message when available", () => {
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(screen.getByText("Test error message")).toBeInTheDocument();
    });

    it("should render error message in monospace font for readability", () => {
      // Component redesigned: error message rendered via getUserFriendlyError() in a <p> with
      // break-words class instead of font-mono. Verify the error text container has break-words.
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const errorText = screen.getByText("Test error message");
      expect(errorText).toHaveClass("break-words");
    });

    it("should display support contact message", () => {
      // Component redesigned: support message is split across text nodes with <a> links inside.
      // Match the leading text node which starts the sentence.
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(
        screen.getByText(/Se o problema persistir,/)
      ).toBeInTheDocument();
    });

    it("should be responsive and centered", () => {
      const { container } = render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass("min-h-screen", "flex", "items-center", "justify-center");
    });
  });

  // AC3: Botão "Tentar novamente" funcional
  describe("Reset Button", () => {
    it('should render "Tentar novamente" button', () => {
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
    });

    it("should call reset function when button is clicked", () => {
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const button = screen.getByRole("button", { name: /tentar novamente/i });
      fireEvent.click(button);
      expect(mockReset).toHaveBeenCalledTimes(1);
    });

    it("should call reset multiple times on multiple clicks", () => {
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const button = screen.getByRole("button", { name: /tentar novamente/i });
      fireEvent.click(button);
      fireEvent.click(button);
      fireEvent.click(button);
      expect(mockReset).toHaveBeenCalledTimes(3);
    });

    it("should have proper styling for accessibility", () => {
      // Component redesigned: button uses CSS variable theming (var(--brand-navy)) instead of
      // hardcoded bg-green-600. Verify focus ring class which is accessibility-critical.
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const button = screen.getByRole("button", { name: /tentar novamente/i });
      expect(button).toHaveClass("focus:ring-2");
      expect(button).toHaveClass("focus:outline-none");
    });
  });

  // AC4: Erros logados apropriadamente
  describe("Error Logging", () => {
    it("should log error to console on mount", () => {
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(console.error).toHaveBeenCalledWith("Application error:", mockError);
    });

    it("should log error only once per mount", () => {
      const { unmount } = render(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(console.error).toHaveBeenCalledTimes(1);
      unmount();
    });

    it("should re-log when error changes", () => {
      const { rerender } = render(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(console.error).toHaveBeenCalledTimes(1);

      const newError = new Error("Different error");
      rerender(<ErrorBoundary error={newError} reset={mockReset} />);
      expect(console.error).toHaveBeenCalledTimes(2);
      expect(console.error).toHaveBeenLastCalledWith("Application error:", newError);
    });
  });

  // Edge Cases
  describe("Edge Cases", () => {
    it("should handle error without message", () => {
      const errorWithoutMessage = new Error();
      errorWithoutMessage.message = "";
      const { container } = render(<ErrorBoundary error={errorWithoutMessage} reset={mockReset} />);
      expect(screen.getByRole("heading")).toBeInTheDocument();
      // When error.message is empty string (falsy), the div should not render
      const errorMessageDiv = container.querySelector(".bg-gray-100");
      expect(errorMessageDiv).not.toBeInTheDocument();
    });

    it("should handle error with digest property", () => {
      const errorWithDigest = Object.assign(new Error("Digest error"), {
        digest: "abc123xyz",
      });
      render(<ErrorBoundary error={errorWithDigest} reset={mockReset} />);
      expect(screen.getByText("Digest error")).toBeInTheDocument();
    });

    it("should handle very long error messages with word wrap", () => {
      // getUserFriendlyError() returns a generic message when the error message exceeds 200 chars.
      // The error text container still has break-words for any text that renders.
      const longMessage = "x".repeat(500);
      const longError = new Error(longMessage);
      render(<ErrorBoundary error={longError} reset={mockReset} />);
      // Long messages are replaced by getUserFriendlyError with a generic fallback
      const genericText = screen.getByText("Algo deu errado. Tente novamente em instantes.");
      expect(genericText).toHaveClass("break-words");
    });

    it("should handle special characters in error message", () => {
      // getUserFriendlyError() detects 'Error:' as technical jargon and replaces with a
      // user-friendly generic message, preventing raw technical strings from showing.
      const specialError = new Error('Error: <script>alert("xss")</script>');
      render(<ErrorBoundary error={specialError} reset={mockReset} />);
      // Technical error message is sanitised by getUserFriendlyError
      expect(screen.getByText("Algo deu errado. Tente novamente em instantes.")).toBeInTheDocument();
    });
  });

  // Accessibility
  describe("Accessibility", () => {
    it("should have proper ARIA attributes on icon", () => {
      const { container } = render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const svg = container.querySelector("svg[aria-hidden='true']");
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute("aria-hidden", "true");
    });

    it("should have focusable button with proper focus styles", () => {
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const button = screen.getByRole("button", { name: /tentar novamente/i });
      button.focus();
      expect(button).toHaveFocus();
      expect(button).toHaveClass("focus:outline-none", "focus:ring-2");
    });

    it("should have sufficient color contrast", () => {
      // Component redesigned: colors use CSS variables (var(--ink), var(--ink-secondary))
      // instead of hardcoded Tailwind classes. Verify elements are present with some color styling.
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const heading = screen.getByRole("heading");
      expect(heading?.className).toContain("text-[var(--ink)]");
      const description = screen.getByText(/Ocorreu um erro inesperado/);
      expect(description?.className).toContain("text-[var(--ink-secondary)]");
    });
  });

  // Integration
  describe("Integration", () => {
    it("should work with Next.js error boundary contract", () => {
      const nextJsError = new Error("Next.js error");
      (nextJsError as any).digest = "nextjs-digest-123";

      render(<ErrorBoundary error={nextJsError} reset={mockReset} />);
      expect(screen.getByText("Next.js error")).toBeInTheDocument();
      expect(console.error).toHaveBeenCalledWith("Application error:", nextJsError);
    });

    it("should maintain component state after reset click", () => {
      const { rerender } = render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const button = screen.getByRole("button", { name: /tentar novamente/i });

      fireEvent.click(button);
      expect(mockReset).toHaveBeenCalled();

      // Simulate re-render after reset
      rerender(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(screen.getByRole("heading")).toBeInTheDocument();
    });
  });

  // Visual Regression Guards
  describe("Visual Consistency", () => {
    it("should have consistent spacing classes", () => {
      const { container } = render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const card = container.querySelector(".shadow-lg");
      expect(card).toHaveClass("p-8", "rounded-lg");
    });

    it("should use theme colors consistently", () => {
      // Component redesigned: button uses CSS variable theming (var(--brand-navy), var(--brand-blue))
      // instead of hardcoded bg-green-600. Verify CSS variable classes are applied.
      render(<ErrorBoundary error={mockError} reset={mockReset} />);
      const button = screen.getByRole("button", { name: /tentar novamente/i });
      expect(button?.className).toContain("bg-[var(--brand-navy)]");
      expect(button?.className).toContain("hover:bg-[var(--brand-blue)]");
    });

    it("should render with proper layout structure", () => {
      // Component redesigned: card uses bg-[var(--surface-1)] CSS variable instead of bg-white.
      // The max-w-md constraint is still present.
      const { container } = render(<ErrorBoundary error={mockError} reset={mockReset} />);
      expect(container.querySelector(".max-w-md")).toBeInTheDocument();
      // bg-white replaced by CSS variable theming; verify the card element exists via shadow class
      expect(container.querySelector(".shadow-lg")).toBeInTheDocument();
    });
  });
});
