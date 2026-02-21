import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { SearchErrorBoundary } from "@/app/buscar/components/SearchErrorBoundary";

// Component that throws an error on render
const ThrowError = ({ shouldThrow = true }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error("Test error message");
  }
  return <div>No error</div>;
};

// Mock console.error to avoid cluttering test output
beforeEach(() => {
  jest.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  (console.error as jest.Mock).mockRestore();
});

describe("SearchErrorBoundary", () => {
  // CRIT-002 AC8: Renders fallback UI when child throws during render
  it("should render fallback UI when child component throws error", () => {
    render(
      <SearchErrorBoundary>
        <ThrowError />
      </SearchErrorBoundary>
    );

    expect(screen.getByText("Algo deu errado ao exibir os resultados")).toBeInTheDocument();
    expect(screen.getByText(/Um erro inesperado ocorreu/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Tentar novamente/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Nova busca/ })).toBeInTheDocument();
  });

  it("should show error message in details section", () => {
    render(
      <SearchErrorBoundary>
        <ThrowError />
      </SearchErrorBoundary>
    );

    // Expand details
    const details = screen.getByText("Detalhes técnicos");
    fireEvent.click(details);

    // Check error message is shown
    expect(screen.getByText("Test error message")).toBeInTheDocument();
  });

  it("should retry when 'Tentar novamente' button is clicked", () => {
    const { rerender } = render(
      <SearchErrorBoundary>
        <ThrowError />
      </SearchErrorBoundary>
    );

    expect(screen.getByText("Algo deu errado ao exibir os resultados")).toBeInTheDocument();

    // Click retry button
    fireEvent.click(screen.getByRole("button", { name: /Tentar novamente/ }));

    // Error boundary should reset state and re-render children
    // Since ThrowError still throws, it will show error again
    expect(screen.getByText("Algo deu errado ao exibir os resultados")).toBeInTheDocument();
  });

  // CRIT-002 AC9: Calls onReset when "Nova busca" button is clicked
  it("should call onReset when 'Nova busca' button is clicked", () => {
    const mockOnReset = jest.fn();

    render(
      <SearchErrorBoundary onReset={mockOnReset}>
        <ThrowError />
      </SearchErrorBoundary>
    );

    // Click reset button
    fireEvent.click(screen.getByRole("button", { name: /Nova busca/ }));

    expect(mockOnReset).toHaveBeenCalledTimes(1);
  });

  it("should render children when no error occurs", () => {
    render(
      <SearchErrorBoundary>
        <ThrowError shouldThrow={false} />
      </SearchErrorBoundary>
    );

    expect(screen.getByText("No error")).toBeInTheDocument();
    expect(screen.queryByText("Algo deu errado ao exibir os resultados")).not.toBeInTheDocument();
  });

  it("should show error icon", () => {
    const { container } = render(
      <SearchErrorBoundary>
        <ThrowError />
      </SearchErrorBoundary>
    );

    // Check for SVG icon (warning triangle) by class
    const icon = container.querySelector("svg.h-6.w-6");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass("text-red-600");
  });

  it("should handle errors without message", () => {
    const ThrowNoMessage = () => {
      throw new Error();
    };

    render(
      <SearchErrorBoundary>
        <ThrowNoMessage />
      </SearchErrorBoundary>
    );

    // Expand details
    fireEvent.click(screen.getByText("Detalhes técnicos"));

    // Should show "Erro desconhecido" fallback
    expect(screen.getByText("Erro desconhecido")).toBeInTheDocument();
  });

  // CRIT-002 AC10: Dark mode support
  it("should have dark mode classes", () => {
    const { container } = render(
      <SearchErrorBoundary>
        <ThrowError />
      </SearchErrorBoundary>
    );

    const errorCard = container.querySelector(".dark\\:bg-red-950\\/20");
    expect(errorCard).toBeInTheDocument();
  });
});
