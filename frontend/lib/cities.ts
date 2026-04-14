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
  SP: ['São Paulo', 'Campinas', 'Guarulhos', 'São Bernardo do Campo', 'Osasco', 'Santo André', 'Mauá', 'Mogi das Cruzes', 'Diadema'],
  RJ: ['Rio de Janeiro', 'Niterói', 'Duque de Caxias', 'Nova Iguaçu', 'São Gonçalo', 'Belford Roxo', 'São João de Meriti'],
  MG: ['Belo Horizonte', 'Uberlândia', 'Contagem', 'Juiz de Fora', 'Betim', 'Montes Claros', 'Ribeirão das Neves'],
  DF: ['Brasília'],
  PR: ['Curitiba', 'Londrina', 'Maringá', 'Cascavel', 'Ponta Grossa', 'São José dos Pinhais', 'Foz do Iguaçu'],
  BA: ['Salvador', 'Feira de Santana', 'Vitória da Conquista', 'Camaçari', 'Juazeiro', 'Ilhéus'],
  RS: ['Porto Alegre', 'Caxias do Sul', 'Pelotas', 'Canoas', 'Santa Maria', 'Viamão'],
  GO: ['Goiânia', 'Aparecida de Goiânia', 'Anápolis', 'Rio Verde', 'Águas Lindas de Goiás'],
  PE: ['Recife', 'Jaboatão dos Guararapes', 'Olinda', 'Caruaru', 'Petrolina'],
  SC: ['Florianópolis', 'Joinville', 'Blumenau', 'São José'],
  CE: ['Fortaleza', 'Caucaia', 'Juazeiro do Norte', 'Maracanaú'],
  PA: ['Belém', 'Ananindeua', 'Santarém', 'Marabá'],
  AM: ['Manaus', 'Parintins', 'Manacapuru'],
  MA: ['São Luís', 'Imperatriz', 'Timon', 'Caxias'],
  ES: ['Vitória', 'Vila Velha', 'Serra', 'Cariacica'],
  RN: ['Mossoró'],
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
 * Currently 81 cities across 16 UFs (matches backend UF_CITIES).
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
      { next: { revalidate: 86400 }, signal: AbortSignal.timeout(10000) },
    );
    if (!res.ok) return null;
    return (await res.json()) as CidadeStats;
  } catch {
    return null;
  }
}

/**
 * Onda 3: City × Sector cross-reference stats from backend
 * (GET /v1/blog/stats/cidade/{cidade}/setor/{sectorId}).
 */
export interface CidadeSectorStats {
  cidade: string;
  uf: string;
  sector_id: string;
  sector_name: string;
  total_editais: number;
  avg_value: number;
  value_range_min: number;
  value_range_max: number;
  top_modalidades: { name: string; count: number }[];
  orgaos_frequentes: { name: string; count: number }[];
  top_oportunidades: {
    titulo: string;
    orgao: string;
    valor: number | null;
    uf: string;
    data: string;
  }[];
  has_sufficient_data: boolean;
  last_updated: string;
}

/**
 * Fetch city × sector stats from backend (server-side, ISR-friendly).
 * Returns null on any failure so pages can render gracefully.
 */
export async function fetchCidadeSectorStats(
  citySlug: string,
  sectorId: string,
): Promise<CidadeSectorStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const res = await fetch(
      `${backendUrl}/v1/blog/stats/cidade/${encodeURIComponent(citySlug)}/setor/${encodeURIComponent(sectorId)}`,
      { next: { revalidate: 86400 }, signal: AbortSignal.timeout(10000) },
    );
    if (!res.ok) return null;
    return (await res.json()) as CidadeSectorStats;
  } catch {
    return null;
  }
}
