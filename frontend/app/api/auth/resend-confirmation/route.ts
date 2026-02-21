/**
 * GTM-FIX-009: Proxy for POST /v1/auth/resend-confirmation
 * Resends signup confirmation email with 60s rate limiting.
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  // CRIT-004 AC4: Forward X-Correlation-ID for end-to-end tracing
  const correlationId = request.headers.get("X-Correlation-ID");

  try {
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/v1/auth/resend-confirmation`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(correlationId && { "X-Correlation-ID": correlationId }) },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json(
      { success: false, message: "Erro ao reenviar email." },
      { status: 500 }
    );
  }
}
