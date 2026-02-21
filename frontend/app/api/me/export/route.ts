import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return NextResponse.json(
      { message: "Servidor nao configurado" },
      { status: 503 }
    );
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json(
      { message: "Autenticacao necessaria" },
      { status: 401 }
    );
  }

  // CRIT-004 AC4: Forward X-Correlation-ID for end-to-end tracing
  const correlationId = request.headers.get("X-Correlation-ID");

  try {
    const response = await fetch(`${backendUrl}/v1/me/export`, {
      headers: {
        "Authorization": authHeader,
        ...(correlationId && { "X-Correlation-ID": correlationId }),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { message: error.detail || "Erro ao exportar dados" },
        { status: response.status }
      );
    }

    // Forward the JSON file response with content-disposition header
    const contentDisposition = response.headers.get("content-disposition");
    const body = await response.text();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (contentDisposition) {
      headers["Content-Disposition"] = contentDisposition;
    }

    return new NextResponse(body, { status: 200, headers });
  } catch (error) {
    console.error("Error exporting user data:", error);
    return NextResponse.json(
      { message: "Erro ao conectar com servidor" },
      { status: 503 }
    );
  }
}
