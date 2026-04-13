import dynamic from 'next/dynamic';
import Link from 'next/link';
import { formatBRL, getUfPrep } from '@/lib/programmatic';
import type {
  ContratosSetorUfStats,
  ContratosCidadeStats,
  ContratosCidadeSetorStats,
  SampleContract,
} from '@/lib/contracts-fallback';

/**
 * ContractsPanoramaBlock — bloco universal de autoridade de mercado em contratos públicos.
 *
 * Exibe KPIs consolidados, top órgãos/fornecedores com links internos, gráfico de
 * tendência mensal (Recharts, client-only) e amostra de contratos reais extraídos
 * do PNCP. Substitui a semântica de fallback do HistoricalContractsFallback por um
 * panorama permanente de inteligência de mercado.
 *
 * Retorna null quando `data` é null ou `total_contracts === 0`.
 */

// Gráfico carregado apenas no cliente — sem SSR — para evitar hydration mismatch do Recharts.
const TrendBarChart = dynamic(() => import('./TrendBarChart'), { ssr: false });

type ContractsData =
  | ContratosSetorUfStats
  | ContratosCidadeStats
  | ContratosCidadeSetorStats;

export interface ContractsPanoramaBlockProps {
  variant: 'setor-uf' | 'cidade' | 'nacional';
  data: ContractsData | null;
  sectorName?: string;
  ufName?: string;
  /** Código de 2 letras da UF — usado para preposição correta ("no Paraná", "em São Paulo") */
  uf?: string;
  cityName?: string;
}

// ---------------------------------------------------------------------------
// Helpers de formatação
// ---------------------------------------------------------------------------

function maskCnpj(cnpj: string): string {
  const digits = (cnpj ?? '').replace(/\D/g, '');
  if (digits.length !== 14) return cnpj ?? '—';
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
}

function formatDate(raw: string): string {
  if (!raw) return '—';
  // Aceita "YYYY-MM-DD" ou ISO com T
  const parts = raw.split('T')[0].split('-');
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }
  return raw;
}

// ---------------------------------------------------------------------------
// Textos dinâmicos
// ---------------------------------------------------------------------------

function buildHeading(props: ContractsPanoramaBlockProps): string {
  const { variant, sectorName, ufName, uf, cityName } = props;
  switch (variant) {
    case 'setor-uf':
      if (cityName && !ufName) {
        return `Panorama de Contratos Públicos — ${sectorName} em ${cityName}`;
      }
      return `Panorama de Contratos Públicos — ${sectorName} ${getUfPrep(uf)} ${ufName}`;
    case 'cidade':
      return `Panorama de Contratos Públicos em ${cityName}`;
    case 'nacional':
      return sectorName
        ? `Panorama de Contratos Públicos — ${sectorName} no Brasil`
        : 'Panorama de Contratos Públicos no Brasil';
  }
}

function buildSubtitle(
  props: ContractsPanoramaBlockProps,
  data: ContractsData,
): string {
  const { variant, sectorName, ufName, uf, cityName } = props;
  const total = data.total_contracts.toLocaleString('pt-BR');
  const valor = formatBRL(data.total_value);

  switch (variant) {
    case 'setor-uf': {
      const contexto = cityName && !ufName
        ? `de ${sectorName} em ${cityName}`
        : `de ${sectorName} ${getUfPrep(uf)} ${ufName}`;
      return `Nos últimos 12 meses, ${total} contratos públicos ${contexto} foram assinados, movimentando ${valor}. Os dados abaixo são extraídos diretamente do PNCP e permitem identificar os principais compradores, fornecedores recorrentes e a evolução mensal da demanda.`;
    }
    case 'cidade':
      return `Nos últimos 12 meses, ${total} contratos públicos em ${cityName} foram firmados, totalizando ${valor}. O panorama abaixo consolida todos os setores e permite identificar quais órgãos mais compram e quais fornecedores dominam o mercado local.`;
    case 'nacional':
      return sectorName
        ? `Nos últimos 12 meses, ${total} contratos públicos de ${sectorName} foram assinados no Brasil, movimentando ${valor}. O panorama abaixo consolida dados de todo o território nacional, extraídos diretamente do Portal Nacional de Contratações Públicas.`
        : `Nos últimos 12 meses, ${total} contratos públicos foram assinados no Brasil, movimentando ${valor}. Os dados abaixo são extraídos do PNCP e refletem a atividade de compras do setor público federal, estadual e municipal.`;
  }
}

// ---------------------------------------------------------------------------
// Sub-seção: KPI Grid
// ---------------------------------------------------------------------------

function KpiCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] text-center">
      <p className="text-xs text-[var(--ink-secondary)] mb-1 leading-tight">{label}</p>
      <p className="text-xl font-bold text-[var(--ink)]">{value}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-seção: Amostra de contratos
// ---------------------------------------------------------------------------

function SampleContractRow({ item }: { item: SampleContract }) {
  return (
    <div className="py-3 border-t border-[var(--border)] first:border-t-0">
      <p className="text-sm text-[var(--ink)] font-medium leading-snug mb-1 line-clamp-2">
        {item.objeto}
      </p>
      <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-[var(--ink-secondary)]">
        <span>
          <span className="font-medium">Órgão:</span> {item.orgao}
        </span>
        <span>
          <span className="font-medium">Fornecedor:</span> {item.fornecedor}
        </span>
        {item.valor != null && (
          <span>
            <span className="font-medium">Valor:</span> {formatBRL(item.valor)}
          </span>
        )}
        <span>
          <span className="font-medium">Data:</span> {formatDate(item.data_assinatura)}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Componente principal
// ---------------------------------------------------------------------------

export default function ContractsPanoramaBlock(props: ContractsPanoramaBlockProps) {
  const { data } = props;

  // AC10: retorna null quando sem dados
  if (!data || data.total_contracts === 0) return null;

  const topOrgaos = data.top_orgaos.slice(0, 5);
  const topFornecedores = data.top_fornecedores.slice(0, 5);
  const sampleContracts = (data.sample_contracts ?? []).slice(0, 5);
  const hasTrend = data.monthly_trend.length > 0;
  const nUniqueOrgaos = data.n_unique_orgaos ?? 0;
  const nUniqueFornecedores = data.n_unique_fornecedores ?? 0;

  return (
    <section className="mb-10" aria-label="Panorama de contratos públicos">
      {/* Cabeçalho */}
      <h2 className="text-xl font-semibold text-[var(--ink)] mb-2">
        {buildHeading(props)}
      </h2>
      <p className="text-sm text-[var(--ink-secondary)] mb-6 leading-relaxed">
        {buildSubtitle(props, data)}
      </p>

      {/* AC4: KPI Grid — 5 métricas */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-8">
        <KpiCard
          label="Total movimentado"
          value={formatBRL(data.total_value)}
        />
        <KpiCard
          label="Contratos assinados"
          value={data.total_contracts.toLocaleString('pt-BR')}
        />
        <KpiCard
          label="Valor médio"
          value={formatBRL(data.avg_value)}
        />
        <KpiCard
          label="Órgãos compradores"
          value={nUniqueOrgaos > 0 ? nUniqueOrgaos.toLocaleString('pt-BR') : '—'}
        />
        <KpiCard
          label="Fornecedores ativos"
          value={nUniqueFornecedores > 0 ? nUniqueFornecedores.toLocaleString('pt-BR') : '—'}
        />
      </div>

      {/* AC5: Top órgãos compradores com links internos */}
      {topOrgaos.length > 0 && (
        <div className="mb-8">
          <h3 className="text-base font-semibold text-[var(--ink)] mb-3">
            Principais órgãos compradores
          </h3>
          <div className="overflow-hidden rounded-lg border border-[var(--border)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--surface-1)] text-[var(--ink-secondary)]">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Órgão</th>
                  <th className="text-left px-4 py-2 font-medium hidden sm:table-cell">CNPJ</th>
                  <th className="text-right px-4 py-2 font-medium">Contratos</th>
                  <th className="text-right px-4 py-2 font-medium">Valor total</th>
                </tr>
              </thead>
              <tbody>
                {topOrgaos.map((orgao) => (
                  <tr
                    key={orgao.cnpj}
                    className="border-t border-[var(--border)] hover:bg-[var(--surface-1)] transition-colors"
                  >
                    <td className="px-4 py-2">
                      <Link
                        href={`/orgaos/${orgao.cnpj}`}
                        className="text-[var(--brand-blue)] hover:underline font-medium"
                      >
                        {orgao.nome}
                      </Link>
                    </td>
                    <td className="px-4 py-2 text-[var(--ink-secondary)] hidden sm:table-cell font-mono text-xs">
                      {maskCnpj(orgao.cnpj)}
                    </td>
                    <td className="px-4 py-2 text-right text-[var(--ink)]">
                      {orgao.total_contratos.toLocaleString('pt-BR')}
                    </td>
                    <td className="px-4 py-2 text-right text-[var(--ink)] font-medium">
                      {formatBRL(orgao.valor_total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* AC6: Top fornecedores com links internos */}
      {topFornecedores.length > 0 && (
        <div className="mb-8">
          <h3 className="text-base font-semibold text-[var(--ink)] mb-1">
            Principais fornecedores do mercado
          </h3>
          <p className="text-xs text-[var(--ink-secondary)] mb-3">
            Empresas que mais contrataram com o poder público neste segmento nos últimos 12 meses —
            inteligência competitiva para analisar o mercado e identificar concorrentes recorrentes.
          </p>
          <div className="overflow-hidden rounded-lg border border-[var(--border)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--surface-1)] text-[var(--ink-secondary)]">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Fornecedor</th>
                  <th className="text-left px-4 py-2 font-medium hidden sm:table-cell">CNPJ</th>
                  <th className="text-right px-4 py-2 font-medium">Contratos</th>
                  <th className="text-right px-4 py-2 font-medium">Valor total</th>
                </tr>
              </thead>
              <tbody>
                {topFornecedores.map((forn) => (
                  <tr
                    key={forn.cnpj}
                    className="border-t border-[var(--border)] hover:bg-[var(--surface-1)] transition-colors"
                  >
                    <td className="px-4 py-2">
                      <Link
                        href={`/fornecedores/${forn.cnpj}`}
                        className="text-[var(--brand-blue)] hover:underline font-medium"
                      >
                        {forn.nome}
                      </Link>
                    </td>
                    <td className="px-4 py-2 text-[var(--ink-secondary)] hidden sm:table-cell font-mono text-xs">
                      {maskCnpj(forn.cnpj)}
                    </td>
                    <td className="px-4 py-2 text-right text-[var(--ink)]">
                      {forn.total_contratos.toLocaleString('pt-BR')}
                    </td>
                    <td className="px-4 py-2 text-right text-[var(--ink)] font-medium">
                      {formatBRL(forn.valor_total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* AC7: Gráfico de tendência mensal — Recharts (client-only) */}
      {hasTrend && (
        <div className="mb-8">
          <h3 className="text-base font-semibold text-[var(--ink)] mb-3">
            Evolução mensal de contratos — últimos 12 meses
          </h3>
          <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] p-4">
            <TrendBarChart data={data.monthly_trend} />
          </div>
        </div>
      )}

      {/* AC8: Amostra de contratos reais */}
      {sampleContracts.length > 0 && (
        <div className="mb-8">
          <h3 className="text-base font-semibold text-[var(--ink)] mb-3">
            Amostra de contratos recentes
          </h3>
          <p className="text-xs text-[var(--ink-secondary)] mb-3">
            Exemplos de objetos contratados recentemente — referência real para dimensionar
            propostas e entender o vocabulário técnico utilizado nos editais deste segmento.
          </p>
          <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-4 py-1">
            {sampleContracts.map((item, idx) => (
              <SampleContractRow key={idx} item={item} />
            ))}
          </div>
        </div>
      )}

      {/* AC9: Aviso legal PNCP */}
      <p className="text-xs text-[var(--ink-muted)] mt-2">
        Dados extraídos do Portal Nacional de Contratações Públicas (PNCP) — base oficial do
        governo federal. Atualização: últimos 12 meses.
      </p>
    </section>
  );
}
