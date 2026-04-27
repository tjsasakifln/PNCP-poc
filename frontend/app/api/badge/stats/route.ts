/**
 * S9: Dynamic SVG badge endpoint — proxies to backend stats and renders SVG.
 * This provides a convenient `/api/badge/stats` URL for external embeds.
 */

import { NextResponse } from 'next/server';

export const revalidate = 3600; // 1h ISR

export async function GET() {
  const backendUrl = process.env.BACKEND_URL;

  try {
    const resp = await fetch(`${backendUrl}/v1/stats/public?format=badge`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(8000),
    });

    if (!resp.ok) {
      return new NextResponse(fallbackBadge('Erro'), {
        status: 200,
        headers: svgHeaders(),
      });
    }

    const svg = await resp.text();
    return new NextResponse(svg, {
      status: 200,
      headers: svgHeaders(),
    });
  } catch {
    return new NextResponse(fallbackBadge('Indisponível'), {
      status: 200,
      headers: svgHeaders(),
    });
  }
}

function svgHeaders() {
  return {
    'Content-Type': 'image/svg+xml',
    'Cache-Control': 'public, max-age=3600, s-maxage=3600',
  };
}

function fallbackBadge(text: string): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="28" role="img" aria-label="SmartLic: ${text}">
  <title>SmartLic: ${text}</title>
  <clipPath id="r"><rect width="200" height="28" rx="5" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="100" height="28" fill="#1e3a5f"/>
    <rect x="100" width="100" height="28" fill="#6b7280"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,sans-serif" font-size="11">
    <text x="50" y="19">SmartLic</text>
    <text x="150" y="19">${text}</text>
  </g>
</svg>`;
}
