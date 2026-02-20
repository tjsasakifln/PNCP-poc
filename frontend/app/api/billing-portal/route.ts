import { NextRequest, NextResponse } from "next/server";
import { getRefreshedToken } from "../../../lib/serverAuth";

export async function POST(request: NextRequest) {
  try {
    // Get auth token (prefer server-side refreshed, fall back to header)
    const refreshedToken = await getRefreshedToken();
    const authHeader = refreshedToken
      ? `Bearer ${refreshedToken}`
      : request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json(
        { message: "Autenticacao necessaria. Faca login para continuar." },
        { status: 401 }
      );
    }

    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      console.error("BACKEND_URL environment variable is not configured");
      return NextResponse.json(
        { message: "Servidor nao configurado. Contate o suporte." },
        { status: 503 }
      );
    }

    // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
    const correlationId = request.headers.get("X-Correlation-ID");
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Authorization: authHeader,
    };
    if (correlationId) {
      headers["X-Correlation-ID"] = correlationId;
    }

    // Call backend billing portal endpoint
    const response = await fetch(`${backendUrl}/v1/billing-portal`, {
      method: "POST",
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { message: error.detail || "Erro ao criar sessão do portal" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error creating billing portal session:", error);
    return NextResponse.json(
      { message: "Erro interno do servidor" },
      { status: 500 }
    );
  }
}
