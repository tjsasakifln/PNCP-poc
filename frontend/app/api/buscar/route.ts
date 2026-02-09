import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { writeFile } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";

export async function POST(request: NextRequest) {
  try {
    // Require authentication - return 401 if no auth header
    const authHeader = request.headers.get("authorization");
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
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "Authorization": authHeader,
    };

    const MAX_RETRIES = 2;
    const RETRY_DELAYS = [0, 3000]; // ms delay before each attempt
    // Only retry 503 (rate limit) — 502 means backend already retried PNCP internally
    const RETRYABLE_STATUSES = [503];

    let response: Response | null = null;
    let lastError: { detail?: string; status: number } | null = null;

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      if (attempt > 0) {
        console.warn(`[buscar] Retry attempt ${attempt}/${MAX_RETRIES - 1} after ${RETRY_DELAYS[attempt]}ms delay`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAYS[attempt]));
      }

      try {
        // Timeout de 5 minutos — consultas com muitos estados podem demorar
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5 * 60 * 1000);

        response = await fetch(`${backendUrl}/buscar`, {
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
            ? "A consulta excedeu o tempo limite (5 min). Tente com menos estados ou um período menor."
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
    if (!response || !response.ok) {
      if (lastError) {
        return NextResponse.json(
          { message: lastError.detail || "Erro no backend" },
          { status: lastError.status }
        );
      }
      // Try to extract error from last response
      if (response && !response.ok) {
        const error = await response.json().catch(() => ({}));
        return NextResponse.json(
          { message: error.detail || "Erro no backend" },
          { status: response.status }
        );
      }
      return NextResponse.json(
        { message: "Backend indisponível após múltiplas tentativas" },
        { status: 503 }
      );
    }

    const data = await response.json().catch(async () => {
      const text = await response.text().catch(() => "");
      console.error(`[buscar] Backend returned non-JSON response: ${text.slice(0, 200)}`);
      return null;
    });

    if (!data) {
      return NextResponse.json(
        { message: "Resposta inesperada do servidor. Tente novamente." },
        { status: 502 }
      );
    }

    // Only save Excel to filesystem if there are actual results
    let downloadId: string | null = null;
    if (data.excel_base64) {
      downloadId = randomUUID();
      const buffer = Buffer.from(data.excel_base64, "base64");
      const tmpDir = tmpdir();
      const filePath = join(tmpDir, `bidiq_${downloadId}.xlsx`);

      try {
        await writeFile(filePath, buffer);
        console.log(`✅ Excel saved to: ${filePath}`);

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

    return NextResponse.json({
      resumo: data.resumo,
      licitacoes: data.licitacoes || [],  // Individual bids for preview display
      download_id: downloadId,
      total_raw: data.total_raw || 0,
      total_filtrado: data.total_filtrado || 0,
      filter_stats: data.filter_stats || null,
      termos_utilizados: data.termos_utilizados || null,
      stopwords_removidas: data.stopwords_removidas || null,
      excel_available: data.excel_available || false,
      upgrade_message: data.upgrade_message || null,
    });

  } catch (error) {
    console.error("Erro na busca:", error);
    return NextResponse.json(
      { message: "Erro interno do servidor" },
      { status: 500 }
    );
  }
}
