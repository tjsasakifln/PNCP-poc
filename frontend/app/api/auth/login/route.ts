/**
 * GTM-GO-002 AC4: Rate-limited login proxy.
 *
 * IP-based rate limiting: 5 attempts per 5 minutes.
 * Proxies to Supabase Auth /auth/v1/token?grant_type=password.
 */
import { NextRequest, NextResponse } from "next/server";
import { checkRateLimit, loginRateLimitStore } from "@/lib/rate-limiter";

const AUTH_LIMIT = Number(process.env.AUTH_RATE_LIMIT_PER_5MIN ?? 5);
const AUTH_WINDOW_MS = 5 * 60 * 1000; // 5 minutes

function getClientIp(request: NextRequest): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    request.headers.get("x-real-ip") ||
    "unknown"
  );
}

// ---------------------------------------------------------------------------
// POST handler
// ---------------------------------------------------------------------------
export async function POST(request: NextRequest) {
  const ip = getClientIp(request);
  const { allowed, retryAfter } = checkRateLimit(loginRateLimitStore, ip, AUTH_LIMIT, AUTH_WINDOW_MS);

  if (!allowed) {
    return NextResponse.json(
      {
        detail:
          "Muitas tentativas de login. Aguarde antes de tentar novamente.",
        retry_after_seconds: retryAfter,
      },
      {
        status: 429,
        headers: { "Retry-After": String(retryAfter) },
      }
    );
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    return NextResponse.json(
      { error: "Serviço de autenticação indisponível." },
      { status: 503 }
    );
  }

  try {
    const body = await request.json();
    const correlationId = request.headers.get("X-Correlation-ID");

    const response = await fetch(
      `${supabaseUrl}/auth/v1/token?grant_type=password`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          apikey: supabaseAnonKey,
          ...(correlationId && { "X-Correlation-ID": correlationId }),
        },
        body: JSON.stringify(body),
      }
    );

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json(
      { error: "Erro ao processar login." },
      { status: 500 }
    );
  }
}
