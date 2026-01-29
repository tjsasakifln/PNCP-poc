import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";

// Cache temporário para downloads (em produção usar Redis)
const downloadCache = new Map<string, Buffer>();

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { ufs, data_inicial, data_final, setor_id } = body;

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
    // Use BACKEND_URL (set via env var in CI) instead of NEXT_PUBLIC_BACKEND_URL (build-time)
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    let response: Response;
    try {
      // Timeout de 5 minutos — consultas com muitos estados podem demorar
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5 * 60 * 1000);

      response = await fetch(`${backendUrl}/buscar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ufs, data_inicial, data_final, setor_id: setor_id || "vestuario" }),
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

    // Only cache Excel if there are actual results
    let downloadId: string | null = null;
    if (data.excel_base64) {
      downloadId = randomUUID();
      downloadCache.set(downloadId, Buffer.from(data.excel_base64, "base64"));
      // Limpar cache após 10 minutos
      setTimeout(() => downloadCache.delete(downloadId!), 10 * 60 * 1000);
    }

    return NextResponse.json({
      resumo: data.resumo,
      download_id: downloadId,
      total_raw: data.total_raw || 0,
      total_filtrado: data.total_filtrado || 0,
      filter_stats: data.filter_stats || null,
    });

  } catch (error) {
    console.error("Erro na busca:", error);
    return NextResponse.json(
      { message: "Erro interno do servidor" },
      { status: 500 }
    );
  }
}

// Export downloadCache for download route
export { downloadCache };
