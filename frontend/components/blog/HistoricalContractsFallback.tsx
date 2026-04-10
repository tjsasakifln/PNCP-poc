import Link from 'next/link';
import { formatBRL } from '@/lib/programmatic';
import type {
  ContratosSetorUfStats,
  ContratosCidadeStats,
  ContratosCidadeSetorStats,
} from '@/lib/contracts-fallback';

/**
 * Zero-state fallback for blog programmatic pages when no open editais exist.
 *
 * Instead of rendering a thin "no results" warning, this component surfaces
 * historical contract activity from `pncp_supplier_contracts` so visitors
 * arriving via SEO still get genuine value (market intelligence, top buyers,
 * competitors and signed-contract price benchmarks).
 *
 * Rendered conditionally from the page server component:
 *   {stats.total_editais === 0 && contractsData && <HistoricalContractsFallback … />}
 */

type ContractsData =
  | ContratosSetorUfStats
  | ContratosCidadeStats
  | ContratosCidadeSetorStats;

interface Props {
  scope: 'sector-uf' | 'cidade' | 'cidade-setor';
  sectorName?: string;
  ufName?: string;
  cityName?: string;
  data: ContractsData;
  /** Slug used by the inner CTA (utm_content). */
  ctaSlug: string;
}

function maskCnpj(cnpj: string): string {
  const digits = (cnpj || '').replace(/\D/g, '');
  if (digits.length !== 14) return cnpj || '—';
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
}

function buildHeading(props: Props): string {
  const { scope, sectorName, ufName, cityName } = props;
  switch (scope) {
    case 'sector-uf':
      return `Histórico de contratos públicos — ${sectorName} em ${ufName}`;
    case 'cidade':
      return `Histórico de contratos públicos em ${cityName}`;
    case 'cidade-setor':
      return `Histórico de contratos públicos — ${sectorName} em ${cityName}`;
  }
}

function buildIntro(props: Props): string {
  const { scope, sectorName, ufName, cityName } = props;
  const filter = (() => {
    switch (scope) {
      case 'sector-uf':
        return `${sectorName} em ${ufName}`;
      case 'cidade':
        return cityName || '';
      case 'cidade-setor':
        return `${sectorName} em ${cityName}`;
    }
  })();
  return `Não há editais abertos neste momento para ${filter}, mas esta demanda tem histórico. Veja o que os órgãos públicos contrataram nos últimos 12 meses — uma referência real para dimensionar propostas e identificar compradores recorrentes.`;
}

function buildCtaTitle(props: Props): string {
  const { scope, sectorName, ufName, cityName } = props;
  switch (scope) {
    case 'sector-uf':
      return `Receba alerta quando o próximo edital de ${sectorName} abrir em ${ufName}`;
    case 'cidade':
      return `Receba alerta quando novas licitações abrirem em ${cityName}`;
    case 'cidade-setor':
      return `Receba alerta quando o próximo edital de ${sectorName} abrir em ${cityName}`;
  }
}

export default function HistoricalContractsFallback(props: Props) {
  const { data, ctaSlug } = props;
  const signupHref = `/signup?source=blog&utm_source=blog&utm_medium=programmatic&utm_content=${encodeURIComponent(ctaSlug)}`;

  // Max monthly count/value to scale the bar chart
  const maxMonthlyCount = Math.max(
    1,
    ...data.monthly_trend.map((m) => m.count),
  );

  const topOrgaos = data.top_orgaos.slice(0, 5);
  const topFornecedores = data.top_fornecedores.slice(0, 5);

  return (
    <section className="mb-10">
      <h2 className="text-xl font-semibold text-ink mb-2">{buildHeading(props)}</h2>
      <p className="text-sm text-ink-secondary mb-6 leading-relaxed">{buildIntro(props)}</p>

      {/* Headline stats — 3 cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="p-4 rounded-lg border border-[var(--border)] text-center">
          <p className="text-sm text-ink-secondary mb-1">Contratos assinados (12 meses)</p>
          <p className="text-2xl font-bold text-ink">
            {data.total_contracts.toLocaleString('pt-BR')}
          </p>
        </div>
        <div className="p-4 rounded-lg border border-[var(--border)] text-center">
          <p className="text-sm text-ink-secondary mb-1">Valor total contratado</p>
          <p className="text-2xl font-bold text-ink">{formatBRL(data.total_value)}</p>
        </div>
        <div className="p-4 rounded-lg border border-[var(--border)] text-center">
          <p className="text-sm text-ink-secondary mb-1">Valor médio por contrato</p>
          <p className="text-2xl font-bold text-ink">{formatBRL(data.avg_value)}</p>
        </div>
      </div>

      {/* Top órgãos compradores */}
      {topOrgaos.length > 0 && (
        <div className="mb-8">
          <h3 className="text-base font-semibold text-ink mb-3">
            Top {topOrgaos.length} órgãos compradores
          </h3>
          <div className="overflow-hidden rounded-lg border border-[var(--border)]">
            <table className="w-full text-sm">
              <thead className="bg-surface-1 text-ink-secondary">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Órgão</th>
                  <th className="text-left px-4 py-2 font-medium hidden sm:table-cell">CNPJ</th>
                  <th className="text-right px-4 py-2 font-medium">Contratos</th>
                  <th className="text-right px-4 py-2 font-medium">Valor total</th>
                </tr>
              </thead>
              <tbody>
                {topOrgaos.map((o) => (
                  <tr key={o.cnpj} className="border-t border-[var(--border)]">
                    <td className="px-4 py-2 text-ink">{o.nome}</td>
                    <td className="px-4 py-2 text-ink-secondary hidden sm:table-cell font-mono text-xs">
                      {maskCnpj(o.cnpj)}
                    </td>
                    <td className="px-4 py-2 text-right text-ink">
                      {o.total_contratos.toLocaleString('pt-BR')}
                    </td>
                    <td className="px-4 py-2 text-right text-ink font-medium">
                      {formatBRL(o.valor_total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Top fornecedores */}
      {topFornecedores.length > 0 && (
        <div className="mb-8">
          <h3 className="text-base font-semibold text-ink mb-1">
            Top {topFornecedores.length} fornecedores neste mercado
          </h3>
          <p className="text-xs text-ink-secondary mb-3">
            Empresas que mais contrataram com o setor público neste filtro nos últimos 12 meses —
            inteligência competitiva para analisar o mercado.
          </p>
          <div className="overflow-hidden rounded-lg border border-[var(--border)]">
            <table className="w-full text-sm">
              <thead className="bg-surface-1 text-ink-secondary">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Fornecedor</th>
                  <th className="text-left px-4 py-2 font-medium hidden sm:table-cell">CNPJ</th>
                  <th className="text-right px-4 py-2 font-medium">Contratos</th>
                  <th className="text-right px-4 py-2 font-medium">Valor total</th>
                </tr>
              </thead>
              <tbody>
                {topFornecedores.map((f) => (
                  <tr key={f.cnpj} className="border-t border-[var(--border)]">
                    <td className="px-4 py-2 text-ink">{f.nome}</td>
                    <td className="px-4 py-2 text-ink-secondary hidden sm:table-cell font-mono text-xs">
                      {maskCnpj(f.cnpj)}
                    </td>
                    <td className="px-4 py-2 text-right text-ink">
                      {f.total_contratos.toLocaleString('pt-BR')}
                    </td>
                    <td className="px-4 py-2 text-right text-ink font-medium">
                      {formatBRL(f.valor_total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Monthly trend mini-chart */}
      {data.monthly_trend.length > 0 && (
        <div className="mb-8">
          <h3 className="text-base font-semibold text-ink mb-3">
            Contratos assinados por mês (últimos 12 meses)
          </h3>
          <div className="space-y-2">
            {data.monthly_trend.map((point) => {
              const pct = Math.round((point.count / maxMonthlyCount) * 100);
              return (
                <div key={point.month} className="flex items-center gap-3">
                  <span className="text-xs text-ink-secondary w-16 shrink-0 font-mono">
                    {point.month}
                  </span>
                  <div className="flex-1 bg-surface-2 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-brand-blue h-full rounded-full transition-all"
                      style={{ width: `${Math.max(pct, point.count > 0 ? 2 : 0)}%` }}
                    />
                  </div>
                  <span className="text-xs text-ink w-20 text-right">
                    {point.count.toLocaleString('pt-BR')}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="not-prose bg-brand-blue-subtle/50 rounded-lg p-4 sm:p-5 border border-brand-blue/15 flex flex-col sm:flex-row items-center gap-3 sm:gap-4">
        <p className="text-sm sm:text-base text-ink font-medium text-center sm:text-left flex-1">
          {buildCtaTitle(props)} — teste grátis 14 dias, sem cartão.
        </p>
        <Link
          href={signupHref}
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2 rounded-button text-sm transition-all hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap"
        >
          Ativar Alertas
        </Link>
      </div>
    </section>
  );
}
