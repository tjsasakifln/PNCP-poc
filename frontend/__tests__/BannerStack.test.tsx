/**
 * DEBT-204 Track 3: BannerStack unit tests
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BannerStack, BannerItem } from "../app/buscar/components/BannerStack";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeItem(
  id: string,
  type: BannerItem["type"],
  label: string,
  priority?: number
): BannerItem {
  return {
    id,
    type,
    content: <div data-testid={`content-${id}`}>{label}</div>,
    priority,
  };
}

// ---------------------------------------------------------------------------
// Basic rendering
// ---------------------------------------------------------------------------

describe("BannerStack — basic rendering", () => {
  it("renders nothing when banners array is empty", () => {
    const { container } = render(<BannerStack banners={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders a single banner without expand toggle", () => {
    const banners = [makeItem("b1", "info", "Info message")];
    render(<BannerStack banners={banners} />);
    expect(screen.getByText("Info message")).toBeInTheDocument();
    expect(screen.queryByTestId("banner-stack-toggle")).toBeNull();
  });

  it("renders exactly maxVisible (2) banners by default when given more", () => {
    const banners = [
      makeItem("b1", "info", "Info 1"),
      makeItem("b2", "info", "Info 2"),
      makeItem("b3", "info", "Info 3"),
    ];
    render(<BannerStack banners={banners} />);

    // Top 2 visible
    expect(screen.getByText("Info 1")).toBeInTheDocument();
    expect(screen.getByText("Info 2")).toBeInTheDocument();

    // 3rd is in the overflow section (rendered but hidden via CSS)
    // It should exist in the DOM but the overflow region should have aria-hidden=true
    const overflow = screen.getByTestId("banner-stack-overflow");
    expect(overflow).toHaveAttribute("aria-hidden", "true");
  });

  it("respects custom maxVisible prop", () => {
    const banners = [
      makeItem("b1", "info", "Info 1"),
      makeItem("b2", "info", "Info 2"),
      makeItem("b3", "info", "Info 3"),
      makeItem("b4", "info", "Info 4"),
    ];
    render(<BannerStack banners={banners} maxVisible={3} />);

    // With maxVisible=3, toggle shows only 1 extra
    const toggle = screen.getByTestId("banner-stack-toggle");
    expect(toggle).toHaveTextContent("+1");
  });
});

// ---------------------------------------------------------------------------
// Priority ordering: error > warning > info > success
// ---------------------------------------------------------------------------

describe("BannerStack — severity priority ordering", () => {
  it("shows error banners before warning before info before success", () => {
    const banners = [
      makeItem("s1", "success", "Success msg"),
      makeItem("i1", "info", "Info msg"),
      makeItem("w1", "warning", "Warning msg"),
      makeItem("e1", "error", "Error msg"),
    ];
    render(<BannerStack banners={banners} />);

    // With maxVisible=2, top 2 should be error + warning
    expect(screen.getByTestId("content-e1")).toBeInTheDocument();
    expect(screen.getByTestId("content-w1")).toBeInTheDocument();

    // info and success are in overflow (hidden)
    const overflow = screen.getByTestId("banner-stack-overflow");
    expect(overflow).toHaveAttribute("aria-hidden", "true");
    expect(overflow).toContainElement(screen.getByTestId("content-i1"));
    expect(overflow).toContainElement(screen.getByTestId("content-s1"));
  });

  it("orders same-severity banners by priority value (higher first)", () => {
    const banners = [
      makeItem("low", "warning", "Low priority warning", 0),
      makeItem("high", "warning", "High priority warning", 10),
      makeItem("mid", "warning", "Mid priority warning", 5),
    ];
    render(<BannerStack banners={banners} maxVisible={1} />);

    // Only the highest-priority warning should be in the top slot
    // The overflow region should be aria-hidden and contain the other two
    expect(screen.getByTestId("content-high")).toBeInTheDocument();
    const overflow = screen.getByTestId("banner-stack-overflow");
    expect(overflow).toContainElement(screen.getByTestId("content-mid"));
    expect(overflow).toContainElement(screen.getByTestId("content-low"));
  });
});

// ---------------------------------------------------------------------------
// Expand / collapse
// ---------------------------------------------------------------------------

describe("BannerStack — expand/collapse", () => {
  it("shows expand toggle when there are more banners than maxVisible", () => {
    const banners = [
      makeItem("b1", "info", "Info 1"),
      makeItem("b2", "info", "Info 2"),
      makeItem("b3", "info", "Info 3"),
    ];
    render(<BannerStack banners={banners} />);

    const toggle = screen.getByTestId("banner-stack-toggle");
    expect(toggle).toBeInTheDocument();
    expect(toggle).toHaveTextContent("Ver mais alertas (+1)");
  });

  it("does NOT show expand toggle when banners <= maxVisible", () => {
    const banners = [
      makeItem("b1", "info", "Info 1"),
      makeItem("b2", "info", "Info 2"),
    ];
    render(<BannerStack banners={banners} />);
    expect(screen.queryByTestId("banner-stack-toggle")).toBeNull();
  });

  it("expands overflow section on toggle click", () => {
    const banners = [
      makeItem("b1", "error", "Error msg"),
      makeItem("b2", "warning", "Warning msg"),
      makeItem("b3", "info", "Info msg"),
    ];
    render(<BannerStack banners={banners} />);

    const toggle = screen.getByTestId("banner-stack-toggle");
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(toggle);

    expect(toggle).toHaveAttribute("aria-expanded", "true");
    const overflow = screen.getByTestId("banner-stack-overflow");
    expect(overflow).toHaveAttribute("aria-hidden", "false");
  });

  it("collapses overflow section on second toggle click", () => {
    const banners = [
      makeItem("b1", "error", "Error msg"),
      makeItem("b2", "warning", "Warning msg"),
      makeItem("b3", "info", "Info msg"),
    ];
    render(<BannerStack banners={banners} />);

    const toggle = screen.getByTestId("banner-stack-toggle");

    // Expand
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");

    // Collapse
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    const overflow = screen.getByTestId("banner-stack-overflow");
    expect(overflow).toHaveAttribute("aria-hidden", "true");
  });

  it('toggle label changes to "Ocultar alertas" when expanded', () => {
    const banners = [
      makeItem("b1", "info", "Info 1"),
      makeItem("b2", "info", "Info 2"),
      makeItem("b3", "info", "Info 3"),
    ];
    render(<BannerStack banners={banners} />);

    const toggle = screen.getByTestId("banner-stack-toggle");
    fireEvent.click(toggle);
    expect(toggle).toHaveTextContent("Ocultar alertas");
  });
});

// ---------------------------------------------------------------------------
// Accessibility: aria-live
// ---------------------------------------------------------------------------

describe("BannerStack — aria-live on visible banners", () => {
  it("sets aria-live=assertive on error banners", () => {
    const banners = [makeItem("e1", "error", "Error msg")];
    render(<BannerStack banners={banners} />);

    const wrapper = screen.getByTestId("banner-item-e1");
    expect(wrapper).toHaveAttribute("aria-live", "assertive");
  });

  it("sets aria-live=polite on warning banners", () => {
    const banners = [makeItem("w1", "warning", "Warning msg")];
    render(<BannerStack banners={banners} />);

    const wrapper = screen.getByTestId("banner-item-w1");
    expect(wrapper).toHaveAttribute("aria-live", "polite");
  });

  it("sets aria-live=polite on info banners", () => {
    const banners = [makeItem("i1", "info", "Info msg")];
    render(<BannerStack banners={banners} />);

    const wrapper = screen.getByTestId("banner-item-i1");
    expect(wrapper).toHaveAttribute("aria-live", "polite");
  });

  it("sets aria-live=polite on success banners", () => {
    const banners = [makeItem("s1", "success", "Success msg")];
    render(<BannerStack banners={banners} />);

    const wrapper = screen.getByTestId("banner-item-s1");
    expect(wrapper).toHaveAttribute("aria-live", "polite");
  });

  it("visible banners have aria-live present", () => {
    const banners = [
      makeItem("e1", "error", "Error msg"),
      makeItem("w1", "warning", "Warning msg"),
    ];
    render(<BannerStack banners={banners} />);

    expect(screen.getByTestId("banner-item-e1")).toHaveAttribute("aria-live");
    expect(screen.getByTestId("banner-item-w1")).toHaveAttribute("aria-live");
  });
});

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------

describe("BannerStack — edge cases", () => {
  it("shows +N count matching the number of hidden banners", () => {
    const banners = [
      makeItem("b1", "error", "Error"),
      makeItem("b2", "warning", "Warning"),
      makeItem("b3", "info", "Info 1"),
      makeItem("b4", "info", "Info 2"),
      makeItem("b5", "success", "Success"),
    ];
    render(<BannerStack banners={banners} />);

    const toggle = screen.getByTestId("banner-stack-toggle");
    // 5 banners, maxVisible=2 → 3 hidden
    expect(toggle).toHaveTextContent("+3");
  });

  it("renders with custom className on container", () => {
    const banners = [makeItem("b1", "info", "Info")];
    render(<BannerStack banners={banners} className="mt-4 custom-class" />);
    const container = screen.getByTestId("banner-stack");
    expect(container).toHaveClass("custom-class");
  });

  it("renders with custom data-testid", () => {
    const banners = [makeItem("b1", "info", "Info")];
    render(<BannerStack banners={banners} data-testid="my-banner-stack" />);
    expect(screen.getByTestId("my-banner-stack")).toBeInTheDocument();
  });
});
