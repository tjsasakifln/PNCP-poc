import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { writeFile } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";
import { getRefreshedToken } from "../../../lib/serverAuth";

// CRIT-002 AC3: Contextual error messages based on HTTP status code
function getContextualErrorMessage(status: number, detail?: string): string {
  if (typeof detail === "string" && detail.length > 0) return detail;
  switch (status) {
    case 429: return "Muitas consultas simultâneas. Aguarde alguns segundos e tente novamente.";
    case 500: return "Ocorreu um erro interno. Tente novamente em alguns segundos.";
    case 502: return "O servidor está reiniciando. Aguarde ~30 segundos e tente novamente.";
    case 503: return "O servidor está temporariamente indisponível. Tente novamente em 1 minuto.";
    default: return "Erro inesperado. Tente novamente ou reduza o número de UFs selecionadas.";
  }
}

export async function POST(request: NextRequest) {
  try {
    // STORY-253 AC7: Prefer server-side refreshed token, fall back to header
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

    const body = await request.json();
    const {
      ufs,
      data_inicial,
      data_final,
      setor_id,
      termos_busca,
      search_id,
      // New filter parameters
      status,
      modalidades,
      valor_minimo,
      valor_maximo,
      esferas,
      municipios,
      ordenacao,
    } = body;

    // Validações
    if (!ufs || !Array.isArray(ufs) || ufs.length === 0) {
      return NextResponse.json(
        { message: "Selecione pelo menos um estado" },
        { status: 400 }
      );
    }

    if (!data_inicial || !data_final) {
      return NextResponse.json(
        { message: "Período obrigatório" },
        { status: 400 }
      );
    }

    // Chamar backend Python
    // BACKEND_URL must be set via environment variable - no localhost fallback
    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      console.error("BACKEND_URL environment variable is not configured");
      return NextResponse.json(
        { message: "Servidor nao configurado. Contate o suporte." },
        { status: 503 }
      );
    }

    // Forward auth header to backend (already validated above)
    // CRIT-004 AC1: Forward X-Correlation-ID from browser + generate X-Request-ID
    const correlationId = request.headers.get("X-Correlation-ID");
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "Authorization": authHeader,
      "X-Request-ID": randomUUID(),
    };
    if (correlationId) {
      headers["X-Correlation-ID"] = correlationId;
    }

    const MAX_RETRIES = 2;
    const RETRY_DELAYS = [0, 3000]; // ms delay before each attempt
    // Only retry 503 (rate limit) — 502 means backend already retried PNCP internally
    const RETRYABLE_STATUSES = [503];

    let response: Response | null = null;
    let lastError: { detail?: any; status: number } | null = null;

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      if (attempt > 0) {
        console.warn(`[buscar] Retry attempt ${attempt}/${MAX_RETRIES - 1} after ${RETRY_DELAYS[attempt]}ms delay`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAYS[attempt]));
      }

      try {
        // GTM-FIX-029 AC19/AC20: Timeout hierarchy (outermost → innermost):
        // FE proxy (480s) > Pipeline FETCH_TIMEOUT (360s) > Consolidation (300s) > Per-Source (180s) > Per-UF (90s)
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 8 * 60 * 1000);

        response = await fetch(`${backendUrl}/v1/buscar`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            ufs,
            data_inicial,
            data_final,
            setor_id: setor_id || "vestuario",
            termos_busca: termos_busca || undefined,
            search_id: search_id || undefined,
            // New filter parameters
            status: status || undefined,
            modalidades: modalidades || undefined,
            valor_minimo: valor_minimo ?? undefined,
            valor_maximo: valor_maximo ?? undefined,
            esferas: esferas || undefined,
            municipios: municipios || undefined,
            ordenacao: ordenacao || undefined,
          }),
          signal: controller.signal,
        });

        clearTimeout(timeout);

        // If successful or non-retryable error, break out
        if (response.ok || !RETRYABLE_STATUSES.includes(response.status)) {
          break;
        }

        // Retryable error - log and continue loop
        const errorBody = await response.json().catch(() => ({}));
        lastError = { detail: errorBody.detail, status: response.status };
        console.warn(
          `[buscar] Backend returned ${response.status}: ${errorBody.detail || 'unknown error'}. ` +
          `${attempt < MAX_RETRIES - 1 ? 'Will retry...' : 'No more retries.'}`
        );

      } catch (error) {
        const isTimeout = error instanceof DOMException && error.name === "AbortError";
        if (isTimeout || attempt >= MAX_RETRIES - 1) {
          // Timeout or final attempt - return error
          const message = isTimeout
            ? "A consulta excedeu o tempo limite (8 min). Tente com menos estados ou um período menor."
            : `Backend indisponível em ${backendUrl}: ${error instanceof Error ? error.message : 'conexão recusada'}`;
          console.error(`Erro ao conectar com backend em ${backendUrl}:`, error);
          return NextResponse.json(
            { message },
            { status: isTimeout ? 504 : 503 }
          );
        }
        // Connection error - will retry
        console.warn(`[buscar] Connection error on attempt ${attempt + 1}: ${error instanceof Error ? error.message : 'unknown'}. Will retry...`);
        continue;
      }
    }

    // After retry loop - check if we got a successful response
    // CRIT-009 AC4-AC5: Preserve structured error metadata from backend
    if (!response || !response.ok) {
      const requestId = headers["X-Request-ID"];
      if (lastError) {
        // lastError.detail may be a structured object from CRIT-009 backend
        const detail = lastError.detail;
        const isStructured = detail && typeof detail === "object" && detail.error_code;
        const errorResponse = NextResponse.json(
          {
            message: isStructured ? detail.detail : getContextualErrorMessage(lastError.status, typeof detail === "string" ? detail : undefined),
            error_code: isStructured ? detail.error_code : null,
            search_id: isStructured ? detail.search_id : null,
            correlation_id: isStructured ? detail.correlation_id : null,
            request_id: requestId,
            timestamp: new Date().toISOString(),
            status: lastError.status,
          },
          { status: lastError.status }
        );
        errorResponse.headers.set("X-Request-ID", requestId);
        return errorResponse;
      }
      // Try to extract error from last response
      if (response && !response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        // CRIT-009 AC4: Handle structured detail (object) or legacy detail (string)
        const detail = errorBody.detail;
        const isStructured = detail && typeof detail === "object" && detail.error_code;
        const backendCorrelationId = response.headers.get("X-Correlation-ID");
        const errorResponse = NextResponse.json(
          {
            message: isStructured ? detail.detail : getContextualErrorMessage(response.status, typeof detail === "string" ? detail : errorBody.message),
            error_code: isStructured ? detail.error_code : (errorBody.error_code || null),
            search_id: isStructured ? detail.search_id : (errorBody.search_id || null),
            correlation_id: isStructured ? detail.correlation_id : (backendCorrelationId || null),
            request_id: requestId,
            timestamp: isStructured ? detail.timestamp : new Date().toISOString(),
            status: response.status,
          },
          { status: response.status }
        );
        errorResponse.headers.set("X-Request-ID", requestId);
        return errorResponse;
      }
      const fallbackResponse = NextResponse.json(
        {
          message: "Backend indisponível após múltiplas tentativas",
          error_code: null,
          search_id: null,
          correlation_id: null,
          request_id: requestId,
          timestamp: new Date().toISOString(),
          status: 503,
        },
        { status: 503 }
      );
      fallbackResponse.headers.set("X-Request-ID", requestId);
      return fallbackResponse;
    }

    const responseText = await response.text();
    const data = (() => {
      try {
        return JSON.parse(responseText);
      } catch {
        console.error(`[buscar] Backend returned non-JSON response: ${responseText.slice(0, 200)}`);
        return null;
      }
    })();

    if (!data) {
      return NextResponse.json(
        { message: "Resposta inesperada do servidor. Tente novamente." },
        { status: 502 }
      );
    }

    // Handle Excel download: prefer signed URL from storage, fallback to base64 + filesystem
    let downloadId: string | null = null;
    let downloadUrl: string | null = null;

    if (data.download_url) {
      // Backend provided a signed URL from object storage (preferred)
      downloadUrl = data.download_url;
      console.log(`✅ Excel available via signed URL (TTL: 60min)`);
    } else if (data.excel_base64) {
      // Fallback: Backend sent base64, save to filesystem (legacy mode)
      downloadId = randomUUID();
      const buffer = Buffer.from(data.excel_base64, "base64");
      const tmpDir = tmpdir();
      const filePath = join(tmpDir, `bidiq_${downloadId}.xlsx`);

      try {
        await writeFile(filePath, buffer);
        console.log(`✅ Excel saved to filesystem: ${filePath} (fallback mode)`);

        // Limpar arquivo após 60 minutos (buscas longas + tempo de análise)
        setTimeout(async () => {
          try {
            const { unlink } = await import("fs/promises");
            await unlink(filePath);
            console.log(`🗑️ Cleaned up expired download: ${downloadId}`);
          } catch (error) {
            console.error(`Failed to clean up ${downloadId}:`, error);
          }
        }, 60 * 60 * 1000);
      } catch (error) {
        console.error("Failed to save Excel to filesystem:", error);
        // Continue without download_id (user will see error when trying to download)
        downloadId = null;
      }
    }

    // STORY-222 AC8: Forward ALL backend response fields (no cherry-picking).
    // Only override download_id/download_url (proxy-generated) and strip
    // excel_base64 (already consumed above, too large to forward).
    const { excel_base64: _stripped, ...backendFields } = data;

    // CRIT-009 AC5: Include X-Request-ID in success response header
    const successResponse = NextResponse.json({
      ...backendFields,
      // Proxy-generated fields (override backend values)
      download_id: downloadId,
      download_url: downloadUrl,  // Signed URL from object storage (preferred)
      // Safe defaults for required fields
      licitacoes: data.licitacoes || [],
      total_raw: data.total_raw || 0,
      total_filtrado: data.total_filtrado || 0,
      excel_available: data.excel_available || false,
    });
    successResponse.headers.set("X-Request-ID", headers["X-Request-ID"]);
    return successResponse;

  } catch (error) {
    console.error("Erro na busca:", error);
    return NextResponse.json(
      { message: "Erro interno do servidor" },
      { status: 500 }
    );
  }
}
