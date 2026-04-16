/**
 * TD-FE-030: Toast mobile positioning
 *
 * Validates that the Sonner Toaster is configured with:
 * - position="bottom-center"
 * - max-width: 90vw on mobile (via toastOptions.classNames)
 * - offset: { bottom: 80 } to clear BottomNav (h-16 = 64px + 16px margin)
 */

// Read the layout source to validate Toaster configuration
import fs from "fs";
import path from "path";

describe("Toast mobile positioning (TD-FE-030)", () => {
  let layoutSource: string;

  beforeAll(() => {
    const layoutPath = path.resolve(
      __dirname,
      "../../app/layout.tsx"
    );
    layoutSource = fs.readFileSync(layoutPath, "utf-8");
  });

  it("should configure Toaster with bottom-center position", () => {
    expect(layoutSource).toContain('position="bottom-center"');
  });

  it("should configure Toaster with max-w-[90vw] for mobile", () => {
    expect(layoutSource).toContain("max-w-[90vw]");
  });

  it("should configure Toaster with sm:max-w-md for desktop", () => {
    expect(layoutSource).toContain("sm:max-w-md");
  });

  it("should configure Toaster with mobileOffset to clear BottomNav", () => {
    // BottomNav is h-16 (64px) + 16px margin = 80px offset (mobile-only)
    expect(layoutSource).toContain("bottom: 80");
  });

  it("should use mobileOffset (not offset) so desktop layout is unaffected", () => {
    // mobileOffset={{ bottom: 80 }} — only affects mobile viewport
    expect(layoutSource).toMatch(/mobileOffset=\{\{[^}]*bottom:\s*80/);
  });
});
