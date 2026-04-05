/**
 * SEO Frente 4: pSEO de cidades.
 *
 * Canonical list of Brazilian cities supported by the city blog stats
 * endpoint. Source of truth is `backend/routes/blog_stats.py::UF_CITIES`.
 * Keep this file in sync manually (or via a script) if the backend changes.
 */

export interface CityMeta {
  /** URL slug (lowercase, no accents, hyphens). */
  slug: string;
  /** Display name (with accents). */
  name: string;
  /** UF code (2 letters, uppercase). */
  uf: string;
}

/**
 * Remove accents, lowercase, replace spaces and punctuation with hyphens.
 */
export function slugify(input: string): string {
  return input
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/['`´^~]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * Raw UF -> cities mapping mirroring backend/routes/blog_stats.py::UF_CITIES.
 * When the backend adds more cities, append them here.
 */
const UF_CITIES_RAW: Record<string, string[]> = {
  SP: ['São Paulo', 'Campinas', 'Guarulhos', 'São Bernardo do Campo', 'Osasco'],
  RJ: ['Rio de Janeiro', 'Niterói', 'Duque de Caxias', 'Nova Iguaçu'],
  MG: ['Belo Horizonte', 'Uberlândia', 'Contagem', 'Juiz de Fora'],
  DF: ['Brasília'],
  PR: ['Curitiba', 'Londrina', 'Maringá', 'Cascavel'],
  BA: ['Salvador', 'Feira de Santana', 'Vitória da Conquista'],
  RS: ['Porto Alegre', 'Caxias do Sul', 'Pelotas'],
  GO: ['Goiânia', 'Aparecida de Goiânia', 'Anápolis'],
  PE: ['Recife', 'Jaboatão dos Guararapes', 'Olinda'],
  SC: ['Florianópolis', 'Joinville', 'Blumenau'],
  CE: ['Fortaleza', 'Caucaia', 'Juazeiro do Norte'],
  PA: ['Belém', 'Ananindeua', 'Santarém'],
  AM: ['Manaus', 'Parintins'],
  MA: ['São Luís', 'Imperatriz'],
  ES: ['Vitória', 'Vila Velha', 'Serra'],
};

function buildCities(): CityMeta[] {
  const out: CityMeta[] = [];
  for (const [uf, names] of Object.entries(UF_CITIES_RAW)) {
    for (const name of names) {
      out.push({ slug: slugify(name), name, uf });
    }
  }
  return out;
}

/**
 * Canonical list of cities for programmatic SEO pages.
 * Currently ~46 cities across 15 UFs (matches backend UF_CITIES).
 */
export const CITIES: CityMeta[] = buildCities();

/**
 * Lookup a city by its URL slug.
 */
export function getCityBySlug(slug: string): CityMeta | undefined {
  const normalized = slugify(slug);
  return CITIES.find((c) => c.slug === normalized);
}

/**
 * All cities for a given UF (sorted as in source).
 */
export function getCitiesByUf(uf: string): CityMeta[] {
  const code = uf.toUpperCase();
  return CITIES.filter((c) => c.uf === code);
}

/**
 * City blog stats response from backend
 * (GET /v1/blog/stats/cidade/{cidade}).
 */
export interface CidadeStats {
  cidade: string;
  uf: string;
  total_editais: number;
  orgaos_frequentes: { name: string; count: number }[];
  avg_value: number;
  last_updated: string;
}

/**
 * Fetch city stats from backend (server-side, ISR-friendly).
 * Returns null on any failure so pages can render gracefully.
 */
export async function fetchCidadeStats(citySlug: string): Promise<CidadeStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const res = await fetch(
      `${backendUrl}/v1/blog/stats/cidade/${encodeURIComponent(citySlug)}`,
      { next: { revalidate: 86400 } },
    );
    if (!res.ok) return null;
    return (await res.json()) as CidadeStats;
  } catch {
    return null;
  }
}
