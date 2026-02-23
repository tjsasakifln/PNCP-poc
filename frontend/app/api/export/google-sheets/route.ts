/**
 * UX-349 AC7: Google Sheets export API proxy.
 *
 * POST /api/export/google-sheets → POST BACKEND_URL/api/export/google-sheets
 *
 * Previously returned 404 because no proxy route existed.
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json(
        { detail: "Autenticação necessária. Faça login para continuar." },
        { status: 401 },
      );
    }

    const body = await request.json();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Authorization: authHeader,
    };

    const correlationId = request.headers.get("X-Correlation-ID");
    if (correlationId) {
      headers["X-Correlation-ID"] = correlationId;
    }

    const res = await fetch(`${BACKEND_URL}/api/export/google-sheets`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");

    if (!isJson) {
      // Backend returned HTML or non-JSON (e.g., error page)
      const text = await res.text();
      console.error(`[google-sheets-proxy] Non-JSON response (${res.status}): ${text.slice(0, 200)}`);
      return NextResponse.json(
        { detail: "Erro ao exportar para Google Sheets. Tente novamente." },
        { status: res.status >= 400 ? res.status : 502 },
      );
    }

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    console.error("Google Sheets export proxy error:", error);
    return NextResponse.json(
      { detail: "Erro de conexão ao exportar para Google Sheets." },
      { status: 502 },
    );
  }
}
