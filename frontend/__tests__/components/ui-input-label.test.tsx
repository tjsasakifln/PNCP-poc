/**
 * DEBT-012 FE-033: Input and Label UI component tests.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Input } from "../../components/ui/Input";
import { Label } from "../../components/ui/Label";

describe("Label", () => {
  it("renders children text", () => {
    render(<Label>Nome completo</Label>);
    expect(screen.getByText("Nome completo")).toBeInTheDocument();
  });

  it("renders with htmlFor association", () => {
    render(
      <>
        <Label htmlFor="test-input">Test Label</Label>
        <input id="test-input" />
      </>
    );
    const input = screen.getByLabelText("Test Label");
    expect(input).toBeInTheDocument();
    expect(input.tagName).toBe("INPUT");
  });

  it("renders required indicator via CSS after pseudo-element", () => {
    const { container } = render(<Label required>Email</Label>);
    const label = container.querySelector("label");
    expect(label?.className).toContain("after:content-");
    expect(label?.className).toContain("after:text-error");
  });

  it("does not render required indicator when not required", () => {
    const { container } = render(<Label>Email</Label>);
    const label = container.querySelector("label");
    expect(label?.className).not.toContain("after:content-");
  });

  it("applies default styling", () => {
    const { container } = render(<Label>Test</Label>);
    const label = container.querySelector("label");
    expect(label?.className).toContain("text-sm");
    expect(label?.className).toContain("font-medium");
    expect(label?.className).toContain("mb-1");
  });

  it("merges custom className", () => {
    const { container } = render(<Label className="text-lg">Test</Label>);
    const label = container.querySelector("label");
    expect(label?.className).toContain("text-lg");
  });
});

describe("Input", () => {
  it("renders a text input", () => {
    render(<Input id="test" type="text" placeholder="Enter text" />);
    const input = screen.getByPlaceholderText("Enter text");
    expect(input).toBeInTheDocument();
    expect(input.tagName).toBe("INPUT");
  });

  it("renders default state with proper classes", () => {
    render(<Input id="test" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("border-DEFAULT");
    expect(input.className).toContain("focus:border-brand-blue");
  });

  it("renders error state when error prop is set", () => {
    render(<Input id="test" error="Campo obrigatório" errorTestId="test-error" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("border-error");
    expect(input).toHaveAttribute("aria-invalid", "true");

    const errorMsg = screen.getByTestId("test-error");
    expect(errorMsg).toHaveTextContent("Campo obrigatório");
    expect(errorMsg).toHaveAttribute("role", "alert");
  });

  it("renders success state", () => {
    render(<Input id="test" state="success" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("border-success");
  });

  it("renders error message with custom testId", () => {
    render(<Input id="test" error="Erro" errorTestId="custom-error" />);
    expect(screen.getByTestId("custom-error")).toHaveTextContent("Erro");
  });

  it("renders helper text when no error", () => {
    render(<Input id="helper-test" helperText="Texto de ajuda" />);
    expect(screen.getByText("Texto de ajuda")).toBeInTheDocument();
  });

  it("hides helper text when error is present", () => {
    render(<Input id="helper-test" helperText="Ajuda" error="Erro" />);
    expect(screen.queryByText("Ajuda")).not.toBeInTheDocument();
    expect(screen.getByText("Erro")).toBeInTheDocument();
  });

  it("sets aria-describedby for error", () => {
    render(<Input id="field" error="Erro" />);
    const input = screen.getByRole("textbox");
    expect(input).toHaveAttribute("aria-describedby", "field-error");
  });

  it("sets aria-describedby for helper text", () => {
    render(<Input id="field" helperText="Ajuda" />);
    const input = screen.getByRole("textbox");
    expect(input).toHaveAttribute("aria-describedby", "field-description");
  });

  it("renders small size", () => {
    render(<Input id="test" inputSize="sm" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("h-8");
    expect(input.className).toContain("text-xs");
  });

  it("renders large size", () => {
    render(<Input id="test" inputSize="lg" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("h-12");
  });

  it("supports disabled state", () => {
    render(<Input id="test" disabled />);
    const input = screen.getByRole("textbox");
    expect(input).toBeDisabled();
    expect(input.className).toContain("disabled:opacity-50");
  });

  it("forwards ref", () => {
    const ref = React.createRef<HTMLInputElement>();
    render(<Input id="test" ref={ref} />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });
});
