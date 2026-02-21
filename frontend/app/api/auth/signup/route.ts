/**
 * GTM-GO-002 AC5: Rate-limited signup proxy.
 *
 * IP-based rate limiting: 3 registrations per 10 minutes.
 * Proxies to Supabase Auth /auth/v1/signup.
 */
import { NextRequest, NextResponse } from "next/server";

// ---------------------------------------------------------------------------
// In-memory IP rate limiter
// ---------------------------------------------------------------------------
interface RateLimitEntry {
  count: number;
  resetAt: number;
}

const rateLimitStore = new Map<string, RateLimitEntry>();

const SIGNUP_LIMIT = Number(process.env.SIGNUP_RATE_LIMIT_PER_10MIN ?? 3);
const SIGNUP_WINDOW_MS = 10 * 60 * 1000; // 10 minutes

function getClientIp(request: NextRequest): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    request.headers.get("x-real-ip") ||
    "unknown"
  );
}

function checkRateLimit(
  ip: string,
  limit: number,
  windowMs: number
): { allowed: boolean; retryAfter: number } {
  const now = Date.now();
  const entry = rateLimitStore.get(ip);

  if (!entry || now >= entry.resetAt) {
    rateLimitStore.set(ip, { count: 1, resetAt: now + windowMs });
    return { allowed: true, retryAfter: 0 };
  }

  if (entry.count >= limit) {
    const retryAfter = Math.ceil((entry.resetAt - now) / 1000);
    return { allowed: false, retryAfter: Math.max(1, retryAfter) };
  }

  entry.count++;
  return { allowed: true, retryAfter: 0 };
}

// Periodically clean expired entries (every 60 s)
if (typeof globalThis !== "undefined") {
  const _cleanup = setInterval(() => {
    const now = Date.now();
    for (const [key, value] of rateLimitStore.entries()) {
      if (now >= value.resetAt) {
        rateLimitStore.delete(key);
      }
    }
  }, 60_000);
  if (_cleanup && typeof _cleanup === "object" && "unref" in _cleanup) {
    (_cleanup as NodeJS.Timeout).unref();
  }
}

// ---------------------------------------------------------------------------
// POST handler
// ---------------------------------------------------------------------------
export async function POST(request: NextRequest) {
  const ip = getClientIp(request);
  const { allowed, retryAfter } = checkRateLimit(
    ip,
    SIGNUP_LIMIT,
    SIGNUP_WINDOW_MS
  );

  if (!allowed) {
    return NextResponse.json(
      {
        detail:
          "Muitas tentativas de registro. Aguarde antes de tentar novamente.",
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

    const response = await fetch(`${supabaseUrl}/auth/v1/signup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: supabaseAnonKey,
        ...(correlationId && { "X-Correlation-ID": correlationId }),
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json(
      { error: "Erro ao processar registro." },
      { status: 500 }
    );
  }
}

// Export rate limit store for testing
export { rateLimitStore };
