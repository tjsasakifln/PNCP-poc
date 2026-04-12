import Link from 'next/link';
import { BLOG_ARTICLES, type BlogArticleMeta } from '@/lib/blog';
import { SECTORS, type SectorMeta } from '@/lib/sectors';
import { getUfPrep, UF_NAMES } from '@/lib/programmatic';

/**
 * MKT-002 AC5: Automatic internal linking component.
 *
 * Each programmatic page links to:
 * 1. Editorial post of the corresponding sector (if exists)
 * 2. Sector panorama page
 * 3. 3-5 related programmatic pages (same sector, neighboring UFs)
 */

// UF adjacency map for "neighboring UFs" linking
const UF_NEIGHBORS: Record<string, string[]> = {
  SP: ['RJ', 'MG', 'PR', 'MS'],
  RJ: ['SP', 'MG', 'ES'],
  MG: ['SP', 'RJ', 'ES', 'BA', 'GO', 'DF'],
  DF: ['GO', 'MG'],
  PR: ['SP', 'SC', 'MS'],
  RS: ['SC', 'PR'],
  SC: ['PR', 'RS'],
  BA: ['MG', 'SE', 'PE', 'ES', 'GO'],
  PE: ['BA', 'AL', 'PB', 'CE'],
  CE: ['PE', 'PI', 'PB', 'RN'],
  GO: ['MG', 'DF', 'MT', 'MS', 'BA', 'TO'],
  PA: ['AM', 'MA', 'TO', 'AP'],
  AM: ['PA', 'RR', 'AC', 'RO'],
  MA: ['PA', 'PI', 'TO'],
  ES: ['RJ', 'MG', 'BA'],
  MT: ['GO', 'MS', 'PA', 'RO'],
  MS: ['SP', 'PR', 'GO', 'MT', 'MG'],
  PI: ['MA', 'CE', 'BA', 'PE', 'TO'],
  RN: ['CE', 'PB'],
  PB: ['PE', 'RN', 'CE'],
  AL: ['PE', 'SE', 'BA'],
  SE: ['BA', 'AL'],
  TO: ['GO', 'MA', 'PA', 'PI', 'MT', 'BA'],
  RO: ['AM', 'MT', 'AC'],
  AC: ['AM', 'RO'],
  RR: ['AM', 'PA'],
  AP: ['PA'],
};

// Sector → editorial topic mapping (sector keywords → likely blog articles)
const SECTOR_EDITORIAL_MAP: Record<string, string[]> = {
  vestuario: ['como-aumentar-taxa-vitoria-licitacoes'],
  alimentos: ['vale-a-pena-disputar-pregao'],
  informatica: ['nova-geracao-ferramentas-mercado-licitacoes', 'inteligencia-artificial-consultoria-licitacao-2026'],
  software: ['inteligencia-artificial-consultoria-licitacao-2026', 'nova-geracao-ferramentas-mercado-licitacoes'],
  engenharia: ['estruturar-setor-licitacao-5-milhoes'],
  saude: ['clausulas-escondidas-editais-licitacao'],
  facilities: ['reduzir-tempo-analisando-editais-irrelevantes'],
  vigilancia: ['empresas-vencem-30-porcento-pregoes'],
  transporte: ['pipeline-licitacoes-funil-comercial'],
  mobiliario: ['custo-invisivel-disputar-pregoes-errados'],
  papelaria: ['equipe-40-horas-mes-editais-descartados'],
  manutencao_predial: ['ata-registro-precos-como-escolher'],
  engenharia_rodoviaria: ['estruturar-setor-licitacao-5-milhoes'],
  materiais_eletricos: ['disputar-todas-licitacoes-matematica-real'],
  materiais_hidraulicos: ['licitacao-volume-ou-inteligencia'],
};

interface RelatedPagesProps {
  sectorId: string;
  currentUf?: string;
  currentType: 'sector' | 'sector-uf' | 'panorama';
}

interface RelatedLink {
  title: string;
  href: string;
  type: 'editorial' | 'panorama' | 'programmatic' | 'ferramenta';
}

function getEditorialLinks(sectorId: string): RelatedLink[] {
  const slugs = SECTOR_EDITORIAL_MAP[sectorId] || [];
  const results: RelatedLink[] = [];
  for (const slug of slugs) {
    const article = BLOG_ARTICLES.find((a) => a.slug === slug);
    if (article) {
      results.push({
        title: article.title,
        href: `/blog/${slug}`,
        type: 'editorial',
      });
    }
    if (results.length >= 2) break;
  }
  return results;
}

function getPanoramaLink(sectorId: string, sector: SectorMeta): RelatedLink | null {
  return {
    title: `Panorama Nacional: ${sector.name}`,
    href: `/blog/panorama/${sector.slug}`,
    type: 'panorama',
  };
}

/** All 15 sectors × 27 UFs now have /blog/licitacoes/ pages (P1 complete) */
function getLicitacoesHref(sectorSlug: string, uf: string): string {
  return `/blog/licitacoes/${sectorSlug}/${uf.toLowerCase()}`;
}

function getNeighboringUfLinks(
  sectorId: string,
  currentUf: string,
  sector: SectorMeta,
): RelatedLink[] {
  const neighbors = UF_NEIGHBORS[currentUf] || [];
  return neighbors.slice(0, 3).map((uf) => ({
    title: `Licitações de ${sector.name} ${getUfPrep(uf)} ${UF_NAMES[uf] ?? uf}`,
    href: getLicitacoesHref(sector.slug, uf),
    type: 'programmatic',
  }));
}

function getRelatedSectorLinks(sectorId: string): RelatedLink[] {
  const relatedSectors = SECTORS.filter((s) => s.id !== sectorId).slice(0, 2);
  return relatedSectors.map((s) => ({
    title: `Licitações de ${s.name}`,
    href: `/blog/programmatic/${s.slug}`,
    type: 'programmatic',
  }));
}

export default function RelatedPages({
  sectorId,
  currentUf,
  currentType,
}: RelatedPagesProps) {
  const sector = SECTORS.find((s) => s.id === sectorId);
  if (!sector) return null;

  const links: RelatedLink[] = [];

  // 1. Editorial posts for this sector
  links.push(...getEditorialLinks(sectorId));

  // 2. Panorama page (if not already on panorama)
  if (currentType !== 'panorama') {
    const panorama = getPanoramaLink(sectorId, sector);
    if (panorama) links.push(panorama);
  }

  // 3. Neighboring UF pages (if on a sector-uf page)
  if (currentUf) {
    links.push(...getNeighboringUfLinks(sectorId, currentUf, sector));
  }

  // 4. Related sector pages
  links.push(...getRelatedSectorLinks(sectorId));

  // 5. Free tools (cross-link to high-conversion pages)
  links.push(
    { title: 'Calculadora de Licitacoes', href: '/calculadora', type: 'ferramenta' },
    { title: 'Consulta CNPJ B2G', href: '/cnpj', type: 'ferramenta' },
  );

  // Deduplicate and limit to 7
  const seen = new Set<string>();
  const unique = links.filter((link) => {
    if (seen.has(link.href)) return false;
    seen.add(link.href);
    return true;
  }).slice(0, 7);

  if (unique.length === 0) return null;

  const typeLabel: Record<string, string> = {
    editorial: 'Artigo',
    panorama: 'Panorama',
    programmatic: 'Dados',
    ferramenta: 'Ferramenta',
  };

  return (
    <nav className="mt-12 pt-8 border-t border-[var(--border)]" aria-label="Páginas relacionadas">
      <h3 className="text-lg font-semibold text-ink mb-4">Explore mais</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {unique.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="group flex items-start gap-3 p-3 rounded-lg border border-[var(--border)] hover:border-brand-blue/30 hover:bg-surface-1 transition-colors"
          >
            <span className="shrink-0 mt-0.5 text-xs font-medium px-2 py-0.5 rounded bg-brand-blue-subtle/50 text-brand-blue">
              {typeLabel[link.type]}
            </span>
            <span className="text-sm text-ink group-hover:text-brand-blue transition-colors line-clamp-2">
              {link.title}
            </span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
