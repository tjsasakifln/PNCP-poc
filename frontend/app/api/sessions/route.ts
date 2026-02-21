import { NextRequest, NextResponse } from "next/server";
import { getRefreshedToken } from "../../../lib/serverAuth";

export async function GET(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { message: "Servidor nao configurado" },
      { status: 503 }
    );
  }

  // STORY-253 AC7: Prefer server-side refreshed token, fall back to header
  const refreshedToken = await getRefreshedToken();
  const authHeader = refreshedToken
    ? `Bearer ${refreshedToken}`
    : request.headers.get("authorization");

  if (!authHeader) {
    return NextResponse.json(
      { message: "Autenticacao necessaria" },
      { status: 401 }
    );
  }

  // Forward query parameters
  const { searchParams } = new URL(request.url);
  const queryString = searchParams.toString();

  // CRIT-004 AC4: Forward X-Correlation-ID for end-to-end tracing
  const correlationId = request.headers.get("X-Correlation-ID");

  try {
    const response = await fetch(`${backendUrl}/v1/sessions${queryString ? `?${queryString}` : ""}`, {
      headers: {
        "Authorization": authHeader,
        "Content-Type": "application/json",
        ...(correlationId && { "X-Correlation-ID": correlationId }),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { message: error.detail || "Erro ao carregar historico" },
        { status: response.status }
      );
    }

    const data = await response.json().catch(() => null);
    if (!data) {
      return NextResponse.json(
        { message: "Resposta inesperada do servidor" },
        { status: 502 }
      );
    }
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching sessions:", error);
    return NextResponse.json(
      { message: "Erro ao conectar com servidor" },
      { status: 503 }
    );
  }
}
