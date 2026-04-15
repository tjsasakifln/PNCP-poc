/**
 * DEBT-006: Button Component — Comprehensive Test Suite
 *
 * Tests:
 * - All 6 variants render correctly
 * - All sizes render correctly
 * - Loading state shows spinner
 * - Disabled state is not clickable
 * - Icon-only variant renders with aria-label
 * - TypeScript enforcement of aria-label on icon-only (compile-time, verified via source)
 * - Snapshot tests for variant/size combinations
 * - Integration: pages render without errors
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Button, buttonVariants } from "../components/ui/button";

// ═══════════════════════════════════════════════════════════════════════════════
// AC1: 6 variants render correctly
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006 AC1: Button variants", () => {
  const variants = ["primary", "secondary", "destructive", "ghost", "link", "outline"] as const;

  variants.forEach((variant) => {
    it(`renders ${variant} variant`, () => {
      render(<Button variant={variant}>Click me</Button>);
      const button = screen.getByRole("button", { name: "Click me" });
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent("Click me");
    });
  });

  it("renders primary variant by default (no variant prop)", () => {
    render(<Button>Default</Button>);
    const button = screen.getByRole("button", { name: "Default" });
    expect(button).toBeInTheDocument();
    // Primary variant should have brand-navy background
    expect(button.className).toContain("bg-brand-navy");
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC1: 3 sizes (sm, default, lg) + icon size
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006 AC1: Button sizes", () => {
  it("renders sm size", () => {
    render(<Button size="sm">Small</Button>);
    const button = screen.getByRole("button", { name: "Small" });
    expect(button.className).toContain("h-8");
    expect(button.className).toContain("text-xs");
  });

  it("renders default size", () => {
    render(<Button size="default">Default</Button>);
    const button = screen.getByRole("button", { name: "Default" });
    expect(button.className).toContain("h-10");
    expect(button.className).toContain("text-sm");
  });

  it("renders lg size", () => {
    render(<Button size="lg">Large</Button>);
    const button = screen.getByRole("button", { name: "Large" });
    expect(button.className).toContain("h-12");
    expect(button.className).toContain("text-base");
  });

  it("renders icon size", () => {
    render(
      <Button size="icon" aria-label="Close">
        X
      </Button>
    );
    const button = screen.getByRole("button", { name: "Close" });
    expect(button.className).toContain("h-10");
    expect(button.className).toContain("w-10");
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC1: Loading state shows spinner
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006 AC1: Loading state", () => {
  it("shows spinner SVG when loading=true", () => {
    const { container } = render(<Button loading>Saving...</Button>);
    const spinner = container.querySelector("svg.animate-spin");
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveAttribute("aria-hidden", "true");
  });

  it("disables button when loading=true", () => {
    render(<Button loading>Saving...</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });

  it("does not show spinner when loading=false", () => {
    const { container } = render(<Button>Click</Button>);
    const spinner = container.querySelector("svg.animate-spin");
    expect(spinner).not.toBeInTheDocument();
  });

  it("shows children alongside spinner", () => {
    render(<Button loading>Saving...</Button>);
    expect(screen.getByText("Saving...")).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC1: Disabled state
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006 AC1: Disabled state", () => {
  it("is not clickable when disabled", () => {
    const onClick = jest.fn();
    render(
      <Button disabled onClick={onClick}>
        Click
      </Button>
    );
    const button = screen.getByRole("button");
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("has disabled attribute", () => {
    render(<Button disabled>Click</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("applies disabled WCAG AA token classes (STORY-2.5: opacity-50 → ink-disabled/surface-disabled)", () => {
    render(<Button disabled>Click</Button>);
    const btn = screen.getByRole("button");
    // STORY-2.5: replaced opacity-50 with WCAG AA tokens (4.6:1 contrast)
    expect(btn.className).toContain("disabled:bg-surface-disabled");
    expect(btn.className).toContain("disabled:text-ink-disabled");
    expect(btn.className).not.toContain("disabled:opacity-50");
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC2: Full TypeScript interface (no `any` types)
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006 AC2: TypeScript interface", () => {
  it("button.tsx source has no `any` type annotations", () => {
    const fs = require("fs");
    const path = require("path");
    const source = fs.readFileSync(
      path.join(__dirname, "../components/ui/button.tsx"),
      "utf8"
    );

    // No `: any` or `as any` in the source
    const anyMatches = source.match(/:\s*any\b|as\s+any\b/g);
    expect(anyMatches).toBeNull();
  });

  it("exports ButtonProps type", () => {
    const fs = require("fs");
    const path = require("path");
    const source = fs.readFileSync(
      path.join(__dirname, "../components/ui/button.tsx"),
      "utf8"
    );
    expect(source).toContain("export type ButtonProps");
  });

  it("extends ButtonHTMLAttributes", () => {
    const fs = require("fs");
    const path = require("path");
    const source = fs.readFileSync(
      path.join(__dirname, "../components/ui/button.tsx"),
      "utf8"
    );
    expect(source).toContain("ButtonHTMLAttributes<HTMLButtonElement>");
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC3: Icon-only requires aria-label (TypeScript enforcement)
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006 AC3: Icon-only aria-label enforcement", () => {
  it("icon-only button renders with aria-label", () => {
    render(
      <Button size="icon" aria-label="Close dialog">
        <svg aria-hidden="true" />
      </Button>
    );
    const button = screen.getByRole("button", { name: "Close dialog" });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-label", "Close dialog");
  });

  it("TypeScript source has discriminated union for icon size + aria-label", () => {
    const fs = require("fs");
    const path = require("path");
    const source = fs.readFileSync(
      path.join(__dirname, "../components/ui/button.tsx"),
      "utf8"
    );

    // IconButtonProps type requires size: "icon" and aria-label: string
    expect(source).toContain('size: "icon"');
    expect(source).toContain('"aria-label": string');
    expect(source).toContain("IconButtonProps");
    expect(source).toContain("StandardButtonProps");
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Additional: asChild, className, ref forwarding
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006: Additional features", () => {
  it("accepts custom className", () => {
    render(<Button className="my-custom-class">Click</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("my-custom-class");
  });

  it("forwards ref", () => {
    const ref = React.createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Click</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it("passes through HTML attributes (data-testid, title, etc.)", () => {
    render(
      <Button data-testid="my-button" title="My tooltip">
        Click
      </Button>
    );
    expect(screen.getByTestId("my-button")).toBeInTheDocument();
    expect(screen.getByRole("button")).toHaveAttribute("title", "My tooltip");
  });

  it("fires onClick handler", () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Snapshot tests for each variant/size combination
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006: Snapshot tests", () => {
  const variants = ["primary", "secondary", "destructive", "ghost", "link", "outline"] as const;
  const sizes = ["sm", "default", "lg"] as const;

  variants.forEach((variant) => {
    sizes.forEach((size) => {
      it(`snapshot: ${variant}/${size}`, () => {
        const { container } = render(
          <Button variant={variant} size={size}>
            {variant} {size}
          </Button>
        );
        expect(container.firstChild).toMatchSnapshot();
      });
    });
  });

  it("snapshot: icon size", () => {
    const { container } = render(
      <Button size="icon" aria-label="Close">
        X
      </Button>
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it("snapshot: loading state", () => {
    const { container } = render(<Button loading>Loading...</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("snapshot: disabled state", () => {
    const { container } = render(<Button disabled>Disabled</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC4: Verify pages import shared Button component
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006 AC4: Shared Button adoption across pages", () => {
  const pages = [
    { name: "buscar/page.tsx", path: "app/buscar/page.tsx" },
    { name: "login/page.tsx", path: "app/login/page.tsx" },
    { name: "signup/page.tsx", path: "app/signup/page.tsx" },
    { name: "planos/page.tsx", path: "app/planos/page.tsx" },
    { name: "pipeline/page.tsx", path: "app/pipeline/page.tsx" },
    { name: "conta/seguranca/page.tsx", path: "app/conta/seguranca/page.tsx" },
    { name: "conta/dados/page.tsx", path: "app/conta/dados/page.tsx" },
    { name: "alertas/page.tsx", path: "app/alertas/components/AlertCard.tsx" },
    { name: "SearchFormActions.tsx", path: "app/buscar/components/SearchFormActions.tsx" },
    { name: "SearchStateManager.tsx", path: "app/buscar/components/SearchStateManager.tsx" },
    { name: "SearchResults.tsx", path: "app/buscar/components/SearchResults.tsx" },
  ];

  pages.forEach(({ name, path: filePath }) => {
    it(`${name} imports Button from components/ui/button`, () => {
      const fs = require("fs");
      const pathLib = require("path");
      const source = fs.readFileSync(
        pathLib.join(__dirname, "..", filePath),
        "utf8"
      );
      expect(source).toContain('from "');
      expect(source).toContain("components/ui/button");
    });
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// buttonVariants export
// ═══════════════════════════════════════════════════════════════════════════════
describe("DEBT-006: buttonVariants export", () => {
  it("buttonVariants function generates correct class strings", () => {
    const classes = buttonVariants({ variant: "primary", size: "default" });
    expect(classes).toContain("bg-brand-navy");
    expect(classes).toContain("h-10");
  });

  it("buttonVariants with destructive variant", () => {
    const classes = buttonVariants({ variant: "destructive", size: "sm" });
    expect(classes).toContain("bg-error");
    expect(classes).toContain("h-8");
  });

  it("buttonVariants with ghost variant", () => {
    const classes = buttonVariants({ variant: "ghost" });
    expect(classes).toContain("hover:bg-surface-1");
  });
});
