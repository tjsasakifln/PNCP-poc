import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { LeadCapture } from "@/components/LeadCapture";

describe("LeadCapture receipt", () => {
  it("shows a receipt id without echoing the email", async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, receipt_id: "rec-123" }),
    });
    global.fetch = fetchMock as unknown as typeof fetch;

    render(<LeadCapture source="cnpj" />);
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
    expect(body.source).toBe("cnpj");
  });
});
