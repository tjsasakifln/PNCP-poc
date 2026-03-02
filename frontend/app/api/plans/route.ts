import { NextRequest, NextResponse } from "next/server";
import { sanitizeNetworkError } from "../../../lib/proxy-error-handler";

/**
 * STORY-360 AC2: Plans pricing proxy.
 * Public endpoint (no auth required) — plan pricing is public info.
 * Proxies to backend GET /v1/plans which returns billing period pricing.
 */
export async function GET(request: NextRequest) {
  try {
    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      console.error("BACKEND_URL environment variable is not configured");
      return NextResponse.json(
        { message: "Servidor nao configurado." },
        { status: 503 }
      );
    }

    const response = await fetch(`${backendUrl}/v1/plans`, {
      headers: { "Content-Type": "application/json" },
      next: { revalidate: 300 }, // Cache for 5 minutes
    });

    if (!response.ok) {
      return NextResponse.json(
        { message: "Erro ao buscar planos." },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching plans:", error instanceof Error ? error.message : error);
    return sanitizeNetworkError(error);
  }
}
