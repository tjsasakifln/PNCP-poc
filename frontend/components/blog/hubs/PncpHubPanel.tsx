/**
 * PncpHubPanel — painel de dados reais acima da dobra para o Hub PNCP.
 *
 * PSEO-HUB-002: Async server component que busca dados com ISR 3600s.
 * Exibe KPIs consolidados para os 3 setores de maior volume (saúde, TI,
 * engenharia), cards de todos os setores com links diretos para páginas
 * programáticas, CTA principal e links de navegação.
 *
 * Retorna null silenciosamente se BACKEND_URL não estiver configurado.
 */

import Link from 'next/link';
import { SECTOR_SLUG_TO_BACKEND_ID } from '@/lib/programmatic';
import type { PanoramaStats } from '@/lib/programmatic';
import { formatBRL } from '@/lib/programmatic';

// Setores destacados para o hub PNCP (top por volume de editais)
const FEATURED_SECTORS = [
  { slug: 'saude', label: 'Saúde', desc: 'Medicamentos, equipamentos e serviços hospitalares', icon: '🏥' },
  { slug: 'informatica', label: 'TI e Tecnologia', desc: 'Software, hardware, suporte e consultoria', icon: '💻' },
  { slug: 'engenharia', label: 'Engenharia e Obras', desc: 'Construção, manutenção e projetos técnicos', icon: '🏗️' },
  { slug: 'alimentos', label: 'Alimentos e Merenda', desc: 'Merenda escolar, gêneros alimentícios', icon: '🍽️' },
  { slug: 'facilities', label: 'Facilities e Limpeza', desc: 'Limpeza, conservação e serviços prediais', icon: '🧹' },
  { slug: 'transporte', label: 'Transporte', desc: 'Frota, veículos e serviços de transporte', icon: '🚌' },
];

// Links de navegação rápida por tipo
const QUICK_LINKS = [
  { href: '/fornecedores', label: 'Fornecedores por CNPJ' },
  { href: '/orgaos', label: 'Órgãos compradores' },
  { href: '/contratos/engenharia/SP', label: 'Contratos de Engenharia/SP' },
  { href: '/contratos/saude/SP', label: 'Contratos de Saúde/SP' },
  { href: '/blog/licitacoes/saude/SP', label: 'Editais de Saúde em SP' },
  { href: '/blog/licitacoes/informatica/SP', label: 'Editais de TI em SP' },
  { href: '/blog/licitacoes/engenharia/SP', label: 'Editais de Engenharia em SP' },
  { href: '/blog/licitacoes/informatica/RJ', label: 'Editais de TI no RJ' },
];

// Setores topo para KPIs — busca em paralelo com ISR 3600s
const TOP_SECTOR_SLUGS = ['saude', 'informatica', 'engenharia'] as const;

async function fetchHubPanoramaStats(sectorSlug: string): Promise<PanoramaStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;
  try {
    const sectorId = SECTOR_SLUG_TO_BACKEND_ID[sectorSlug] ?? sectorSlug.replace(/-/g, '_');
    const res = await fetch(`${backendUrl}/v1/blog/stats/panorama/${sectorId}`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function PncpHubPanel() {
  // Busca paralela com ISR 3600s — falha silenciosa por setor
  const [saudeStats, tiStats, engenhStats] = await Promise.all(
    TOP_SECTOR_SLUGS.map((slug) => fetchHubPanoramaStats(slug)),
  );

  const totalNacional =
    (saudeStats?.total_nacional ?? 0) +
    (tiStats?.total_nacional ?? 0) +
    (engenhStats?.total_nacional ?? 0);

  const totalValue =
    (saudeStats?.total_value ?? 0) +
    (tiStats?.total_value ?? 0) +
    (engenhStats?.total_value ?? 0);

  const hasKpis = totalNacional > 0;

  return (
    <div className="not-prose mb-10">
      {/* CTA principal — above the fold */}
      <div className="bg-gradient-to-r from-brand-navy to-brand-blue rounded-xl p-6 sm:p-8 text-white mb-6">
        <h2 className="text-xl sm:text-2xl font-bold mb-2">
          PNCP na prática: encontre editais abertos agora
        </h2>
        <p className="text-white/80 text-sm sm:text-base mb-4 max-w-xl">
          Mais de 200 mil novos contratos por ano. Filtre por setor, UF e modalidade —
          sem garimpar manualmente o portal do governo.
        </p>

        {/* KPIs reais — visíveis quando backend retorna dados */}
        {hasKpis && (
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">{totalNacional.toLocaleString('pt-BR')}</p>
              <p className="text-xs text-white/70 mt-0.5">editais (saúde+TI+eng.)</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">
                {totalValue > 0 ? formatBRL(totalValue) : '—'}
              </p>
              <p className="text-xs text-white/70 mt-0.5">volume contratado</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">27</p>
              <p className="text-xs text-white/70 mt-0.5">estados cobertos</p>
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <Link
            href="/consultoria-b2g?source=pncp-hub&utm_source=blog&utm_medium=hub&utm_content=pncp-guia"
            className="inline-block bg-white text-brand-navy font-semibold px-6 py-3 rounded-button text-sm transition-all hover:scale-[1.02] active:scale-[0.98] text-center"
          >
            Consultar editais agora
          </Link>
          <Link
            href="/buscar"
            className="inline-block bg-white/10 hover:bg-white/20 border border-white/30 text-white font-medium px-6 py-3 rounded-button text-sm transition-all text-center"
          >
            Fazer busca inteligente
          </Link>
        </div>
      </div>

      {/* KPIs por setor — linha resumo */}
      {(saudeStats || tiStats || engenhStats) && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
          {[
            { stats: saudeStats, label: 'Saúde', slug: 'saude' },
            { stats: tiStats, label: 'TI e Tecnologia', slug: 'informatica' },
            { stats: engenhStats, label: 'Engenharia', slug: 'engenharia' },
          ].map(({ stats, label, slug }) =>
            stats ? (
              <Link
                key={slug}
                href={`/blog/licitacoes/${slug}/SP`}
                className="block p-4 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] hover:border-[var(--brand-blue)] hover:shadow-sm transition-all"
              >
                <p className="text-xs font-semibold text-[var(--ink-secondary)] uppercase tracking-wide mb-1">
                  {label}
                </p>
                <p className="text-xl font-bold text-[var(--ink)]">
                  {stats.total_nacional.toLocaleString('pt-BR')} editais
                </p>
                {stats.avg_value > 0 && (
                  <p className="text-xs text-[var(--ink-secondary)] mt-0.5">
                    média {formatBRL(stats.avg_value)}
                  </p>
                )}
              </Link>
            ) : null,
          )}
        </div>
      )}

      {/* Cards de todos os setores */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
          Editais por setor — consulte agora
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {FEATURED_SECTORS.map((sector) => (
            <Link
              key={sector.slug}
              href={`/blog/licitacoes/${sector.slug}/SP`}
              className="block p-4 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] hover:border-[var(--brand-blue)] hover:shadow-sm transition-all group"
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl" aria-hidden="true">{sector.icon}</span>
                <div>
                  <p className="font-semibold text-sm text-[var(--ink)] group-hover:text-[var(--brand-blue)] transition-colors">
                    {sector.label}
                  </p>
                  <p className="text-xs text-[var(--ink-secondary)] mt-0.5 leading-relaxed">
                    {sector.desc}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Links rápidos internos */}
      <div className="bg-[var(--surface-1)] rounded-lg border border-[var(--border)] p-4">
        <h3 className="text-sm font-semibold text-[var(--ink)] mb-3">
          Acesso rápido — consulte por tipo
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {QUICK_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm text-[var(--brand-blue)] hover:underline flex items-center gap-1"
            >
              <span aria-hidden="true">→</span>
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
