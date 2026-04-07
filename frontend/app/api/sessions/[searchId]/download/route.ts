/**
 * Grace period download proxy — GET /v1/sessions/:searchId/download
 * Zero-Churn P2 §2.2: Stream Excel file for previously completed searches.
 * Bypasses quota — only serves already-generated data within 30-day retention window.
 */
import { NextRequest, NextResponse } from "next/server";
import { getRefreshedToken } from "../../../../../lib/serverAuth";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ searchId: string }> },
) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    console.error("[sessions-download] BACKEND_URL not configured");
    return NextResponse.json({ message: "Servidor nao configurado" }, { status: 503 });
  }

  const token = await getRefreshedToken();
  const authHeader = token
    ? `Bearer ${token}`
    : request.headers.get("authorization");

  if (!authHeader) {
    return NextResponse.json({ message: "Autenticacao necessaria" }, { status: 401 });
  }

  const { searchId } = await params;

  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = { Authorization: authHeader };
  if (correlationId) headers["X-Correlation-ID"] = correlationId;

  try {
    const res = await fetch(
      `${backendUrl}/v1/sessions/${searchId}/download`,
      { method: "GET", headers },
    );

    if (!res.ok) {
      let detail = "Erro ao baixar arquivo";
      try {
        const err = await res.json();
        detail = err.detail || err.message || detail;
      } catch {
        // ignore parse error
      }
      return NextResponse.json({ detail }, { status: res.status });
    }

    const blob = await res.arrayBuffer();
    const contentDisposition =
      res.headers.get("Content-Disposition") ||
      `attachment; filename="smartlic-${searchId.slice(0, 8)}.xlsx"`;

    return new NextResponse(blob, {
      status: 200,
      headers: {
        "Content-Type":
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": contentDisposition,
      },
    });
  } catch (error) {
    console.error(
      "[sessions-download] Network error:",
      error instanceof Error ? error.message : error,
    );
    return NextResponse.json(
      { detail: "Erro de rede ao baixar arquivo" },
      { status: 502 },
    );
  }
}
