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

    let response: Response;
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
    } catch (error) {
      const isTimeout = error instanceof DOMException && error.name === "AbortError";
      const message = isTimeout
        ? "A consulta excedeu o tempo limite (5 min). Tente com menos estados ou um período menor."
        : `Backend indisponível em ${backendUrl}: ${error instanceof Error ? error.message : 'conexão recusada'}`;
      console.error(`Erro ao conectar com backend em ${backendUrl}:`, error);
      return NextResponse.json(
        { message },
        { status: isTimeout ? 504 : 503 }
      );
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { message: error.detail || "Erro no backend" },
        { status: response.status }
      );
    }

    const data = await response.json();

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

        // Limpar arquivo após 10 minutos
        setTimeout(async () => {
          try {
            const { unlink } = await import("fs/promises");
            await unlink(filePath);
            console.log(`🗑️ Cleaned up expired download: ${downloadId}`);
          } catch (error) {
            console.error(`Failed to clean up ${downloadId}:`, error);
          }
        }, 10 * 60 * 1000);
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
