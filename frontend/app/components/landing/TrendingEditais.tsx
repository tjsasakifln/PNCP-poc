/**
 * TrendingEditais — SEO internal link injection from homepage to programmatic pages.
 * Pure server component. No client JS needed.
 * A5: Now fetches live trending data from backend with static fallback.
 */
import Link from 'next/link';
import { SECTORS, fetchTrendingSectors } from '@/lib/sectors';

const TOP_UFS = ['SP', 'MG', 'RJ', 'RS', 'PR', 'BA', 'SC', 'GO', 'PE', 'CE'];

// Static fallback: first 8 sectors
const FALLBACK_SECTORS = SECTORS.slice(0, 8);

export async function TrendingEditais() {
  const now = new Date();
  const month = now.toLocaleString('pt-BR', { month: 'long' });
  const year = now.getFullYear();
  const monthCapitalized = month.charAt(0).toUpperCase() + month.slice(1);

  // A5: Try to fetch live trending data
  const trending = await fetchTrendingSectors();
  const hasLiveData = trending && trending.length > 0;

  // Use live data if available, otherwise static fallback
  const displaySectors = hasLiveData
    ? trending.map((t) => ({ slug: t.slug, name: t.name, count: t.count_this_week }))
    : FALLBACK_SECTORS.map((s) => ({ slug: s.slug, name: s.name, count: 0 }));

  return (
    <section className="py-16 bg-surface-0 border-t border-[var(--border)]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-2xl font-bold text-ink mb-2">
          Licitações Abertas — {monthCapitalized} {year}
        </h2>
        <p className="text-sm text-ink-secondary mb-8">
          {hasLiveData
            ? 'Setores mais ativos esta semana — dados ao vivo do PNCP'
            : 'Dados atualizados diariamente do Portal Nacional de Contratações Públicas (PNCP)'}
        </p>

        {/* Sector links with optional count badges */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-8">
          {displaySectors.map((sector) => (
            <Link
              key={sector.slug}
              href={`/licitacoes/${sector.slug}`}
              className="block p-4 rounded-xl border border-[var(--border)] hover:border-brand-blue hover:bg-brand-blue/5 transition-colors group"
            >
              <span className="text-sm font-semibold text-ink group-hover:text-brand-blue transition-colors">
                {sector.name}
              </span>
              {sector.count > 0 && (
                <span className="block text-xs text-ink-secondary mt-1">
                  {sector.count} editais esta semana
                </span>
              )}
            </Link>
          ))}
        </div>

        {/* UF links */}
        <div className="mb-6">
          <h3 className="text-base font-semibold text-ink mb-3">Por Estado</h3>
          <div className="flex flex-wrap gap-2">
            {TOP_UFS.map((uf) => (
              <Link
                key={uf}
                href={`/blog/licitacoes/engenharia/${uf.toLowerCase()}`}
                className="px-3 py-1.5 text-sm rounded-lg bg-surface-1 text-ink-secondary hover:bg-brand-blue hover:text-white transition-colors"
              >
                {uf}
              </Link>
            ))}
          </div>
        </div>

        {/* Utility links */}
        <div className="flex flex-wrap gap-x-4 gap-y-2">
          <Link href="/calculadora" className="text-sm text-brand-blue hover:underline">
            Calculadora B2G →
          </Link>
          <Link href="/cnpj" className="text-sm text-brand-blue hover:underline">
            Consulta CNPJ →
          </Link>
          <Link href="/alertas-publicos" className="text-sm text-brand-blue hover:underline">
            Alertas Públicos →
          </Link>
          <Link href="/glossario" className="text-sm text-brand-blue hover:underline">
            Glossário →
          </Link>
          <Link href="/blog" className="text-sm text-brand-blue hover:underline">
            Blog →
          </Link>
        </div>
      </div>
    </section>
  );
}
