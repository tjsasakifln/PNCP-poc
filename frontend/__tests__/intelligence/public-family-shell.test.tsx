import { render, screen } from "@testing-library/react";
import { PublicFamilyShell } from "@/app/components/intelligence/PublicFamilyShell";

describe("PublicFamilyShell", () => {
  it("renders provenance, graph and contextual CTA", () => {
    render(<PublicFamilyShell family="company" entityPublicId="00000000000191" />);
    expect(screen.getByTestId("provenance-bar")).toBeInTheDocument();
    expect(screen.getByTestId("entity-graph-nav")).toBeInTheDocument();
    expect(screen.getByTestId("family-cta")).toHaveAttribute(
      "data-cta-id",
      "cta.company.carteira",
    );
  });

  it("does not treat empty as a factual zero", () => {
    render(<PublicFamilyShell family="tender" state="empty" />);
    expect(screen.getByTestId("data-state-banner")).toHaveAttribute("data-state", "empty");
    expect(screen.getByText(/não significa que o fato não exista/i)).toBeInTheDocument();
  });
});
