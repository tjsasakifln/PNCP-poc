/**
 * STORY-5.12 (TD-FE-015): Skeleton primitive unit tests.
 */

import { render } from "@testing-library/react";
import { Skeleton } from "@/components/skeletons/Skeleton";

describe("Skeleton primitive", () => {
  it("renders a single pulsing block by default", () => {
    const { container } = render(<Skeleton />);
    const el = container.firstChild as HTMLElement;
    expect(el).toBeInTheDocument();
    expect(el.className).toContain("animate-pulse");
    expect(el.getAttribute("aria-hidden")).toBe("true");
  });

  it("renders N children when count > 1", () => {
    const { container } = render(<Skeleton variant="list" count={5} />);
    // Wrapper + 5 children
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.children.length).toBe(5);
  });

  it("uses variant-specific classes", () => {
    const { container: card } = render(<Skeleton variant="card" />);
    expect((card.firstChild as HTMLElement).className).toContain("rounded-card");

    const { container: avatar } = render(<Skeleton variant="avatar" />);
    expect((avatar.firstChild as HTMLElement).className).toContain("rounded-full");
  });

  it("merges custom className", () => {
    const { container } = render(<Skeleton className="my-custom-class" />);
    expect((container.firstChild as HTMLElement).className).toContain(
      "my-custom-class"
    );
  });

  it("marks decorative (aria-hidden) so assistive tech skips it", () => {
    const { container } = render(<Skeleton variant="text" count={3} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.getAttribute("aria-hidden")).toBe("true");
  });
});
