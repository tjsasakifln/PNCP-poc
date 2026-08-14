import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { LeadCapture } from "@/components/LeadCapture";

describe("LeadCapture receipt", () => {
  it("shows a receipt id without echoing the email", async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, receipt_id: "rec-123" }),
    });
    global.fetch = fetchMock as unknown as typeof fetch;

    window.history.replaceState(
      {},
      "",
      "/licitacoes/saude?utm_source=google&utm_medium=organic",
    );
    Object.defineProperty(document, "referrer", {
      configurable: true,
      value: "https://www.google.com/search?q=licitacoes+saude",
    });

    render(
      <LeadCapture
        source="licitacoes-setor"
        setor="saude"
        ctaId="cta.tender.go_nogo"
        routeFamily="tender"
        entityPublicId="saude"
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("seu@email.com"), {
      target: { value: "pessoa@empresa.com" },
    });
    fireEvent.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(screen.getByTestId("lead-receipt-id")).toHaveTextContent("rec-123");
    });
    expect(screen.queryByText("pessoa@empresa.com")).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/lead-capture",
      expect.objectContaining({ method: "POST" }),
    );
    const body = JSON.parse((fetchMock.mock.calls[0][1] as { body: string }).body);
    expect(body.email).toBe("pessoa@empresa.com");
    expect(body.source).toBe("licitacoes-setor");
    expect(body.cta_id).toBe("cta.tender.go_nogo");
    expect(body.route_family).toBe("tender");
    expect(body.entity_public_id).toBe("saude");
    expect(body.landing_url).toContain("/licitacoes/saude");
    expect(body.utm_source).toBe("google");
    expect(body.utm_medium).toBe("organic");
    expect(body.referrer).toContain("google.com");
    expect(body.correlation_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
    expect(body.landing_url).not.toMatch(/pessoa@empresa|telefone|mensagem/i);
  });
});
