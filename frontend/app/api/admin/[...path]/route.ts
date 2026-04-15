import { NextRequest, NextResponse } from "next/server";
import { sanitizeProxyError, sanitizeNetworkError } from "../../../../lib/proxy-error-handler";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleAdminRequest(request, path, "GET");
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleAdminRequest(request, path, "POST");
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleAdminRequest(request, path, "PUT");
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleAdminRequest(request, path, "PATCH");
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleAdminRequest(request, path, "DELETE");
}

async function handleAdminRequest(
  request: NextRequest,
  pathSegments: string[],
  method: string
) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { message: "Servidor nao configurado" },
      { status: 503 }
    );
  }

  // Forward auth header to backend
  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json(
      { message: "Autenticacao necessaria" },
      { status: 401 }
    );
  }

  // Construct backend path
  const backendPath = `/admin/${pathSegments.join("/")}`;

  // Forward query parameters
  const { searchParams } = new URL(request.url);
  const queryString = searchParams.toString();

  // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {
    "Authorization": authHeader,
    "Content-Type": "application/json",
  };
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const fetchOptions: RequestInit = {
      method,
      headers,
    };

    // Add body for POST/PUT/PATCH requests
    if (method === "POST" || method === "PUT" || method === "PATCH") {
      const body = await request.json().catch(() => null);
      if (body) {
        fetchOptions.body = JSON.stringify(body);
      }
    }

    const response = await fetch(
      `${backendUrl}/v1${backendPath}${queryString ? `?${queryString}` : ""}`,
      fetchOptions
    );

    // CRIT-017: Read body as text first, sanitize infrastructure errors
    const body = await response.text();

    if (!response.ok) {
      const sanitized = sanitizeProxyError(response.status, body, response.headers.get("content-type"));
      if (sanitized) return sanitized;

      try {
        const error = JSON.parse(body);
        return NextResponse.json(
          { detail: error.detail || "Erro na operacao admin" },
          { status: response.status }
        );
      } catch {
        return NextResponse.json(
          { detail: "Erro na operacao admin" },
          { status: response.status }
        );
      }
    }

    try {
      const data = JSON.parse(body);
      return NextResponse.json(data);
    } catch {
      return NextResponse.json({});
    }
  } catch (error) {
    console.error(`Error in admin ${method} request:`, error);
    return sanitizeNetworkError(error);
  }
}
