/**
 * GTM-GO-002 AC5: Rate-limited signup proxy.
 *
 * IP-based rate limiting: 3 registrations per 10 minutes.
 * Proxies to Supabase Auth /auth/v1/signup.
 */
import { NextRequest, NextResponse } from "next/server";
import { checkRateLimit, signupRateLimitStore } from "@/lib/rate-limiter";

// ---------------------------------------------------------------------------
// STORY-258 AC2: Disposable email domain blocklist (top 100 for proxy layer)
// Full list validated on backend as defense-in-depth (AC3)
// ---------------------------------------------------------------------------
const DISPOSABLE_DOMAINS = new Set([
  "tempmail.com", "guerrillamail.com", "guerrillamail.net", "guerrillamail.org",
  "mailinator.com", "mailinator.net", "yopmail.com", "yopmail.fr", "yopmail.net",
  "throwaway.email", "throwawaymail.com", "dispostable.com", "sharklasers.com",
  "trashmail.com", "trashmail.net", "trashmail.org", "trashmail.me", "trashmail.de",
  "tempail.com", "temp-mail.org", "temp-mail.io", "tempmailaddress.com",
  "10minutemail.com", "10minutemail.net", "20minutemail.com",
  "mailnesia.com", "mailnull.com", "mailsac.com", "maildrop.cc",
  "getairmail.com", "getnada.com", "nada.email",
  "discard.email", "discardmail.com", "discardmail.de",
  "fakeinbox.com", "fakemail.fr", "fakemail.net",
  "mohmal.com", "emailondeck.com", "emailnator.com",
  "harakirimail.com", "mailcatch.com", "spamgourmet.com",
  "mytemp.email", "mytrashmail.com", "mailexpire.com", "tempinbox.com",
  "tempr.email", "spam4.me", "guerrillamail.info",
  "tempmail.eu", "tempmail.it", "tempomail.fr",
  "temporarioemail.com.br", "emailtemporario.com.br", "tempmail.com.br",
  "emailfalso.com.br", "emaildescartavel.com.br", "lixomail.com.br",
  "temporario.email", "emailteste.com.br", "descartavel.com.br",
  "crazymailing.com", "deadaddress.com", "devnullmail.com",
  "dodgit.com", "sneakemail.com", "spambox.info",
  "trashdevil.com", "trashemail.de", "trashymail.com",
  "wegwerfemail.de", "wegwerfmail.de", "meltmail.com",
  "mintemail.com", "spamfree24.com", "throwawayemailaddress.com",
  "guerrillamail.de", "guerrillamail.biz", "grr.la",
  "mailinator2.com", "mailinator.org", "yopmail.gq",
  "trashmail.io", "trashmail.at", "trashmail.ws",
  "temp-mail.de", "tempmailaddress.com", "tempmailo.com",
  "10minutemail.org", "20minutemail.it",
  "maildrop.gq", "maildrop.ml",
  "fakemail.net", "mohmal.im", "mohmal.in",
  "spamgourmet.net", "spamgourmet.org",
  "tmpmail.net", "tmpmail.org", "tmpmail.com",
  "guerrillamail.se", "guerrillamail.eu",
]);

const SIGNUP_LIMIT = Number(process.env.SIGNUP_RATE_LIMIT_PER_10MIN ?? 3);
const SIGNUP_WINDOW_MS = 10 * 60 * 1000; // 10 minutes

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
  const { allowed, retryAfter } = checkRateLimit(
    signupRateLimitStore,
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

    // STORY-258 AC2: Block disposable email domains at proxy layer
    const email = (body?.email || "").toLowerCase().trim();
    if (email) {
      const domain = email.split("@")[1] || "";
      if (DISPOSABLE_DOMAINS.has(domain)) {
        console.log(`AUDIT: Signup blocked — disposable domain: ${domain} (ip=${ip})`);
        return NextResponse.json(
          { detail: "Este provedor de email não é aceito. Use um email corporativo ou pessoal (Gmail, Outlook, etc.)" },
          { status: 422 }
        );
      }
    }

    // STORY-258 AC9: Phone uniqueness check before proxying to Supabase
    const phoneWhatsapp = body?.options?.data?.phone_whatsapp || body?.data?.phone_whatsapp || body?.phone_whatsapp || "";
    if (phoneWhatsapp) {
      const backendUrl = process.env.BACKEND_URL;
      if (backendUrl) {
        try {
          const phoneCheckRes = await fetch(
            `${backendUrl}/v1/auth/check-phone?phone=${encodeURIComponent(phoneWhatsapp)}`,
            { headers: { "X-Correlation-ID": correlationId || "" } }
          );
          if (phoneCheckRes.ok) {
            const phoneCheckData = await phoneCheckRes.json();
            if (phoneCheckData.available === false) {
              console.log(`AUDIT: Signup blocked — duplicate phone (ip=${ip})`);
              return NextResponse.json(
                {
                  detail:
                    "Este telefone já está associado a outra conta. Use outro número ou entre em contato com suporte.",
                },
                { status: 409 }
              );
            }
          }
        } catch (phoneCheckErr) {
          // Non-blocking — log warning and continue with signup
          console.warn("[signup] Phone uniqueness check failed (non-blocking):", phoneCheckErr instanceof Error ? phoneCheckErr.message : phoneCheckErr);
        }
      }
    }

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
