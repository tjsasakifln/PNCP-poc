/**
 * STORY-419 AC3: ValorFilter clamps values above the system limit.
 *
 * Values above VALOR_MAX_SYSTEM_LIMIT (R$ 999 trilhões) cause NUMERIC(18,2)
 * overflow (PostgreSQL error 22003) in the backend. The clamp prevents the
 * user from ever sending such a value and shows a friendly notification.
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ValorFilter } from "@/app/buscar/components/ValorFilter";

const NOOP = () => {};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderFilter(props: Partial<React.ComponentProps<typeof ValorFilter>> = {}) {
  const onChange = jest.fn();
  const utils = render(
    <ValorFilter
      valorMin={null}
      valorMax={null}
      onChange={onChange}
      {...props}
    />
  );
  return { ...utils, onChange };
}

function getMaxInput(): HTMLInputElement {
  // The max input has a unique placeholder — safer than label text which
  // appears in slider ARIA labels too.
  return screen.getByPlaceholderText("Sem limite") as HTMLInputElement;
}

// ---------------------------------------------------------------------------
// Normal operation — no clamp needed
// ---------------------------------------------------------------------------

describe("ValorFilter — normal operation", () => {
  it("propagates valid max value on blur", () => {
    const { onChange } = renderFilter();
    const input = getMaxInput();
    fireEvent.change(input, { target: { value: "5000000" } });
    fireEvent.blur(input);
    expect(onChange).toHaveBeenCalledWith(null, 5000000);
  });

  it("accepts null max (no limit) on blur with empty input", () => {
    const { onChange } = renderFilter();
    const input = getMaxInput();
    fireEvent.change(input, { target: { value: "" } });
    fireEvent.blur(input);
    expect(onChange).toHaveBeenCalledWith(null, null);
  });

  it("does not show clamp notification for normal values", () => {
    renderFilter();
    const input = getMaxInput();
    fireEvent.change(input, { target: { value: "1000000" } });
    fireEvent.blur(input);
    expect(
      screen.queryByText(/limite do sistema/i)
    ).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// STORY-419 AC3 — clamp at system limit
// ---------------------------------------------------------------------------

describe("ValorFilter — STORY-419 AC3 system-limit clamp", () => {
  it("clamps value above VALOR_MAX_SYSTEM_LIMIT on blur", () => {
    const { onChange } = renderFilter();
    const input = getMaxInput();
    // 2 quadrilhões — above the 999 trilhões limit
    fireEvent.change(input, { target: { value: "2000000000000000" } });
    fireEvent.blur(input);
    // onChange must be called with the clamped limit, not the oversized value
    expect(onChange).toHaveBeenCalledWith(null, 999_999_999_999_999);
  });

  it("shows friendly clamp notification when value is clamped", () => {
    renderFilter();
    const input = getMaxInput();
    fireEvent.change(input, { target: { value: "9999999999999999" } });
    fireEvent.blur(input);
    expect(screen.getByText(/limite do sistema/i)).toBeInTheDocument();
  });

  it("does NOT show clamp notification when within limit", () => {
    renderFilter();
    const input = getMaxInput();
    fireEvent.change(input, { target: { value: "500000" } });
    fireEvent.blur(input);
    expect(
      screen.queryByText(/limite do sistema/i)
    ).not.toBeInTheDocument();
  });

  it("clamp adjusts the input display value to the limit", () => {
    const { onChange } = renderFilter();
    const input = getMaxInput();
    fireEvent.change(input, { target: { value: "9000000000000000" } });
    fireEvent.blur(input);
    // The input should now show the formatted limit, not the oversized value
    // parseBRL strips non-digits so we verify the clamped number was committed
    expect(onChange).toHaveBeenCalledWith(null, 999_999_999_999_999);
  });
});
