'use client';

import { useState } from 'react';
import { useAdminSWR } from '../../../../hooks/useAdminSWR';

interface GSCQueryRow {
  query: string;
  impressions: number;
  clicks: number;
  ctr: number;
  position: number;
}

interface GSCPageRow {
  page: string;
  impressions: number;
  clicks: number;
  ctr: number;
  position: number;
}

interface GSCLowCTROpportunity {
  page: string;
  impressions: number;
  clicks: number;
  ctr: number;
}

interface GSCSummaryResponse {
  top_queries: GSCQueryRow[];
  top_pages_ctr: GSCPageRow[];
  low_ctr_opportunities: GSCLowCTROpportunity[];
  last_sync_at: string | null;
  days: number;
  enabled: boolean;
}

const RANGES: { label: string; value: number }[] = [
  { label: '7 dias', value: 7 },
  { label: '30 dias', value: 30 },
  { label: '90 dias', value: 90 },
];

function formatCTR(ctr: number): string {
  return `${(ctr * 100).toFixed(2)}%`;
}

function formatPosition(pos: number): string {
  return pos.toFixed(1);
}

function gscOpenLink(page: string): string {
  return `https://search.google.com/search-console/performance/search-analytics?resource_id=sc-domain%3Asmartlic.tech&page=!${encodeURIComponent(page)}`;
}

export default function GSCSummarySection() {
  const [days, setDays] = useState<number>(30);
  const { data, error, isLoading } = useAdminSWR<GSCSummaryResponse>(
    `/api/admin/seo/summary?days=${days}`,
  );

  return (
    <section
      className="mt-10 pt-8 border-t border-[var(--border)]"
      data-testid="gsc-summary"
    >
      <div className="flex items-center justify-between mb-6 flex-wrap gap-2">
        <div>
          <h2 className="text-xl font-bold text-ink-primary">
            Google Search Console — Query Analytics
          </h2>
          <p className="text-xs text-ink-muted mt-1">
            {data?.last_sync_at
              ? `Último sync: ${new Date(data.last_sync_at).toLocaleString('pt-BR')}`
              : 'Aguardando primeiro sync'}
            {data?.enabled === false && ' — GSC_SERVICE_ACCOUNT_JSON não configurado'}
          </p>
        </div>
        <div className="flex gap-2" role="group" aria-label="Filtro de período">
          {RANGES.map((r) => (
            <button
              type="button"
              key={r.value}
              onClick={() => setDays(r.value)}
              className={
                'px-3 py-1 text-xs font-medium rounded-md border transition-colors ' +
                (days === r.value
                  ? 'bg-brand-blue text-white border-brand-blue'
                  : 'bg-transparent text-ink-secondary border-[var(--border)] hover:border-brand-blue')
              }
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-700">
          Falha ao carregar dados GSC: {String((error as Error)?.message || error)}
        </div>
      )}

      {isLoading && (
        <div className="rounded-lg border border-[var(--border)] p-6 text-center text-ink-muted">
          Carregando...
        </div>
      )}

      {!isLoading && !error && data && !data.enabled && (
        <div className="rounded-lg border border-[var(--border)] bg-surface-1 p-6 text-sm text-ink-secondary">
          <p className="font-semibold mb-2">GSC sync não ativo</p>
          <ol className="list-decimal list-inside space-y-1">
            <li>
              Crie service account em Google Cloud + habilite Search Console API
            </li>
            <li>
              Adicione a JSON como variável de ambiente{' '}
              <code className="text-xs bg-canvas px-1 rounded">GSC_SERVICE_ACCOUNT_JSON</code>{' '}
              no Railway
            </li>
            <li>
              Adicione o email da service account como usuário em{' '}
              <a
                href="https://search.google.com/search-console/users"
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-blue hover:underline"
              >
                GSC &gt; Configurações &gt; Usuários e permissões
              </a>
            </li>
            <li>Cron semanal (domingo 06 UTC) popula o cache automaticamente.</li>
          </ol>
        </div>
      )}

      {!isLoading && !error && data && data.enabled && (
        <div className="space-y-8">
          <div>
            <h3 className="font-semibold text-ink-primary mb-3">
              Top 50 Queries por Impressões
            </h3>
            {data.top_queries.length === 0 ? (
              <p className="text-sm text-ink-muted">
                Sem dados ainda. Próximo sync: domingo.
              </p>
            ) : (
              <div className="overflow-x-auto border border-[var(--border)] rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-surface-1 text-xs text-ink-muted uppercase">
                    <tr>
                      <th className="px-3 py-2 text-left">Query</th>
                      <th className="px-3 py-2 text-right">Impressões</th>
                      <th className="px-3 py-2 text-right">Cliques</th>
                      <th className="px-3 py-2 text-right">CTR</th>
                      <th className="px-3 py-2 text-right">Posição</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_queries.map((q) => (
                      <tr
                        key={q.query}
                        className="border-t border-[var(--border)] hover:bg-surface-1"
                      >
                        <td className="px-3 py-2 text-ink-primary">{q.query}</td>
                        <td className="px-3 py-2 text-right">
                          {q.impressions.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {q.clicks.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-3 py-2 text-right">{formatCTR(q.ctr)}</td>
                        <td className="px-3 py-2 text-right">
                          {formatPosition(q.position)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div>
            <h3 className="font-semibold text-ink-primary mb-3">
              Top 50 Pages por CTR
            </h3>
            {data.top_pages_ctr.length === 0 ? (
              <p className="text-sm text-ink-muted">
                Sem dados ainda. Próximo sync: domingo.
              </p>
            ) : (
              <div className="overflow-x-auto border border-[var(--border)] rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-surface-1 text-xs text-ink-muted uppercase">
                    <tr>
                      <th className="px-3 py-2 text-left">Page</th>
                      <th className="px-3 py-2 text-right">Impressões</th>
                      <th className="px-3 py-2 text-right">Cliques</th>
                      <th className="px-3 py-2 text-right">CTR</th>
                      <th className="px-3 py-2 text-right">Posição</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_pages_ctr.map((p) => (
                      <tr
                        key={p.page}
                        className="border-t border-[var(--border)] hover:bg-surface-1"
                      >
                        <td className="px-3 py-2 text-ink-primary">
                          <a
                            href={gscOpenLink(p.page)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:underline"
                          >
                            {p.page}
                          </a>
                        </td>
                        <td className="px-3 py-2 text-right">
                          {p.impressions.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {p.clicks.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-3 py-2 text-right">{formatCTR(p.ctr)}</td>
                        <td className="px-3 py-2 text-right">
                          {formatPosition(p.position)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div>
            <h3 className="font-semibold text-ink-primary mb-3">
              Oportunidades: Pages com CTR &lt;1%
            </h3>
            <p className="text-xs text-ink-muted mb-3">
              Pages com &ge;100 impressões e CTR abaixo de 1%. Revisar title/meta-description.
            </p>
            {data.low_ctr_opportunities.length === 0 ? (
              <p className="text-sm text-ink-muted">Sem oportunidades detectadas.</p>
            ) : (
              <div className="overflow-x-auto border border-[var(--border)] rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-surface-1 text-xs text-ink-muted uppercase">
                    <tr>
                      <th className="px-3 py-2 text-left">Page</th>
                      <th className="px-3 py-2 text-right">Impressões</th>
                      <th className="px-3 py-2 text-right">Cliques</th>
                      <th className="px-3 py-2 text-right">CTR</th>
                      <th className="px-3 py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.low_ctr_opportunities.map((p) => (
                      <tr
                        key={p.page}
                        className="border-t border-[var(--border)] hover:bg-surface-1"
                      >
                        <td className="px-3 py-2 text-ink-primary">{p.page}</td>
                        <td className="px-3 py-2 text-right">
                          {p.impressions.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-3 py-2 text-right">{p.clicks}</td>
                        <td className="px-3 py-2 text-right text-amber-600 font-medium">
                          {formatCTR(p.ctr)}
                        </td>
                        <td className="px-3 py-2 text-right">
                          <a
                            href={gscOpenLink(p.page)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-brand-blue hover:underline"
                          >
                            Abrir GSC →
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
