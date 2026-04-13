import Link from 'next/link';
import { getUfPrep } from '@/lib/programmatic';
import ContractsPanoramaBlock from './ContractsPanoramaBlock';
import type {
  ContratosSetorUfStats,
  ContratosCidadeStats,
  ContratosCidadeSetorStats,
} from '@/lib/contracts-fallback';

/**
 * HistoricalContractsFallback — adaptador de compatibilidade retroativa.
 *
 * Mantido como re-export de ContractsPanoramaBlock para não quebrar nenhum
 * import existente. Mapeia a prop `scope` legada para a nova prop `variant`
 * e adiciona o bloco de CTA específico do contexto de zero-editais.
 *
 * Novos consumidores devem importar ContractsPanoramaBlock diretamente.
 */

type ContractsData =
  | ContratosSetorUfStats
  | ContratosCidadeStats
  | ContratosCidadeSetorStats;

interface Props {
  scope: 'sector-uf' | 'cidade' | 'cidade-setor';
  sectorName?: string;
  ufName?: string;
  /** Código de 2 letras da UF — usado para preposição correta */
  uf?: string;
  cityName?: string;
  data: ContractsData;
  /** Slug usado no utm_content do CTA de alertas */
  ctaSlug: string;
}

function buildCtaTitle(props: Props): string {
  const { scope, sectorName, ufName, uf, cityName } = props;
  switch (scope) {
    case 'sector-uf':
      return `Receba alerta quando o próximo edital de ${sectorName} abrir ${getUfPrep(uf)} ${ufName}`;
    case 'cidade':
      return `Receba alerta quando novas licitações abrirem em ${cityName}`;
    case 'cidade-setor':
      return `Receba alerta quando o próximo edital de ${sectorName} abrir em ${cityName}`;
  }
}

function scopeToVariant(
  scope: Props['scope'],
): 'setor-uf' | 'cidade' | 'nacional' {
  switch (scope) {
    case 'sector-uf':
      return 'setor-uf';
    case 'cidade':
      return 'cidade';
    case 'cidade-setor':
      // Setor × Cidade — sem UF direta; melhor aproximação é 'setor-uf'
      // com cityName passada para o heading contextualizar corretamente.
      return 'setor-uf';
  }
}

export default function HistoricalContractsFallback(props: Props) {
  const { data, ctaSlug, scope, sectorName, ufName, uf, cityName } = props;
  const signupHref = `/signup?source=blog&utm_source=blog&utm_medium=programmatic&utm_content=${encodeURIComponent(ctaSlug)}`;
  const variant = scopeToVariant(scope);

  return (
    <>
      <ContractsPanoramaBlock
        variant={variant}
        data={data}
        sectorName={sectorName}
        ufName={ufName}
        uf={uf}
        cityName={cityName}
      />

      {/* CTA de alertas — exclusivo do contexto de fallback (zero-editais) */}
      <div className="not-prose bg-brand-blue-subtle/50 rounded-lg p-4 sm:p-5 border border-brand-blue/15 flex flex-col sm:flex-row items-center gap-3 sm:gap-4 mb-10">
        <p className="text-sm sm:text-base text-[var(--ink)] font-medium text-center sm:text-left flex-1">
          {buildCtaTitle(props)} — teste grátis por 14 dias, sem cartão.
        </p>
        <Link
          href={signupHref}
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2 rounded-button text-sm transition-all hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap"
        >
          Ativar Alertas
        </Link>
      </div>
    </>
  );
}
