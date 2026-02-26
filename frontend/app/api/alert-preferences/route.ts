import { NextRequest, NextResponse } from "next/server";
import { sanitizeProxyError, sanitizeNetworkError } from "../../../lib/proxy-error-handler";

const getBackendUrl = () => process.env.BACKEND_URL;

export async function GET(request: NextRequest) {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    return NextResponse.json({ message: "Servidor nao configurado" }, { status: 503 });
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ message: "Autenticacao necessaria" }, { status: 401 });
  }

  try {
    const response = await fetch(`${backendUrl}/v1/profile/alert-preferences`, {
      headers: { Authorization: authHeader, "Content-Type": "application/json" },
    });

    if (!response.ok) {
      const body = await response.text();
      const sanitized = sanitizeProxyError(response.status, body, response.headers.get("content-type"));
      if (sanitized) return sanitized;
      try {
        const data = JSON.parse(body);
        return NextResponse.json(
          { message: data.detail || "Erro ao obter preferencias" },
          { status: response.status },
        );
      } catch {
        return NextResponse.json({ message: "Erro temporario" }, { status: response.status });
      }
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching alert preferences:", error instanceof Error ? error.message : error);
    return sanitizeNetworkError(error);
  }
}

export async function PUT(request: NextRequest) {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    return NextResponse.json({ message: "Servidor nao configurado" }, { status: 503 });
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ message: "Autenticacao necessaria" }, { status: 401 });
  }

  try {
    const body = await request.json();
    const response = await fetch(`${backendUrl}/v1/profile/alert-preferences`, {
      method: "PUT",
      headers: { Authorization: authHeader, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const responseBody = await response.text();
      const sanitized = sanitizeProxyError(response.status, responseBody, response.headers.get("content-type"));
      if (sanitized) return sanitized;
      try {
        const data = JSON.parse(responseBody);
        return NextResponse.json(
          { message: data.detail || "Erro ao salvar preferencias" },
          { status: response.status },
        );
      } catch {
        return NextResponse.json({ message: "Erro temporario" }, { status: response.status });
      }
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error saving alert preferences:", error instanceof Error ? error.message : error);
    return sanitizeNetworkError(error);
  }
}
