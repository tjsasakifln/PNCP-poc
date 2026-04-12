import { getSectorFromSlug, fetchAlertasPublicos, getUfPrep, ALL_UFS, UF_NAMES } from '@/lib/programmatic';

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ setor: string; uf: string }> },
) {
  const { setor, uf } = await params;
  const sector = getSectorFromSlug(setor);
  const ufUpper = uf.toUpperCase();
  if (!sector || !ALL_UFS.includes(ufUpper)) {
    return new Response('Not found', { status: 404 });
  }

  const ufName = UF_NAMES[ufUpper] || ufUpper;
  const data = await fetchAlertasPublicos(setor, ufUpper);
  const baseUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';
  const feedUrl = `${baseUrl}/alertas-publicos/${setor}/${uf}/rss.xml`;
  const pageUrl = `${baseUrl}/alertas-publicos/${setor}/${uf}`;

  const items = (data?.bids || []).map((bid) => `    <item>
      <title><![CDATA[${bid.titulo}]]></title>
      <link>${bid.link_pncp || pageUrl}</link>
      <description><![CDATA[${bid.orgao}${bid.municipio ? ` — ${bid.municipio}` : ''} — ${bid.modalidade || 'Licitação'}${bid.valor ? ` — R$ ${bid.valor.toLocaleString('pt-BR')}` : ''}]]></description>
      <pubDate>${new Date(bid.data_publicacao + 'T12:00:00-03:00').toUTCString()}</pubDate>
      <guid isPermaLink="false">${bid.pncp_id || `${setor}-${uf}-${bid.data_publicacao}-${bid.titulo.slice(0, 30)}`}</guid>
      <category><![CDATA[${sector.name}]]></category>
    </item>`).join('\n');

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Alertas de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} | SmartLic</title>
    <link>${pageUrl}</link>
    <description>Licitações recentes de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} — dados do PNCP atualizados a cada hora.</description>
    <language>pt-BR</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${feedUrl}" rel="self" type="application/rss+xml" />
${items}
  </channel>
</rss>`;

  return new Response(rss, {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  });
}
