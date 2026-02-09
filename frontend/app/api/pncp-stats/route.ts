import { NextResponse } from 'next/server';

/**
 * GET /api/pncp-stats
 *
 * Proxy endpoint to fetch PNCP platform-wide statistics from backend.
 * No authentication required (public landing page data).
 *
 * Returns:
 * - 200: PNCPStatsAPIResponse
 * - 503: Service unavailable (backend down)
 * - 500: Internal error
 */
export async function GET() {
  try {
    const backendUrl = process.env.BACKEND_URL;

    if (!backendUrl) {
      console.error('BACKEND_URL environment variable is not configured');
      return NextResponse.json(
        { message: 'Servidor não configurado. Contate o suporte.' },
        { status: 503 }
      );
    }

    const response = await fetch(`${backendUrl}/api/pncp-stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // 30s timeout for this endpoint (backend has 90s + cache)
      signal: AbortSignal.timeout(30000),
    });

    if (!response.ok) {
      console.error(`Backend returned ${response.status}: ${response.statusText}`);
      return NextResponse.json(
        { message: 'Erro ao buscar estatísticas. Tente novamente.' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof Error && error.name === 'TimeoutError') {
      console.error('PNCP stats fetch timeout (30s)');
      return NextResponse.json(
        { message: 'Timeout ao buscar estatísticas.' },
        { status: 504 }
      );
    }

    console.error('Error fetching PNCP stats:', error);
    return NextResponse.json(
      { message: 'Erro interno ao buscar estatísticas.' },
      { status: 500 }
    );
  }
}
