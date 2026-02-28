/**
 * STORY-324: Sector metadata and API helpers for SEO landing pages.
 *
 * Static sector data (from sectors_data.yaml) + API fetch for stats.
 */

export interface SectorMeta {
  id: string;
  slug: string;
  name: string;
  description: string;
}

export interface SectorStats {
  sector_id: string;
  sector_name: string;
  sector_description: string;
  slug: string;
  total_open: number;
  total_value: number;
  avg_value: number;
  top_ufs: { name: string; count: number }[];
  top_modalidades: { name: string; count: number }[];
  sample_items: {
    titulo: string;
    orgao: string;
    valor: number | null;
    uf: string;
    data: string;
  }[];
  last_updated: string;
}

/**
 * Static sector metadata — source of truth derived from sectors_data.yaml.
 * Slug = sector_id with underscores replaced by hyphens.
 */
export const SECTORS: SectorMeta[] = [
  { id: "vestuario", slug: "vestuario", name: "Vestuário e Uniformes", description: "Uniformes, fardamentos, roupas profissionais, EPIs de vestuário" },
  { id: "alimentos", slug: "alimentos", name: "Alimentos e Merenda", description: "Gêneros alimentícios, merenda escolar, refeições, rancho" },
  { id: "informatica", slug: "informatica", name: "Hardware e Equipamentos de TI", description: "Computadores, servidores, periféricos, redes, equipamentos de informática" },
  { id: "mobiliario", slug: "mobiliario", name: "Mobiliário", description: "Mesas, cadeiras, armários, estantes, móveis de escritório" },
  { id: "papelaria", slug: "papelaria", name: "Papelaria e Material de Escritório", description: "Papel, canetas, material de escritório, suprimentos administrativos" },
  { id: "engenharia", slug: "engenharia", name: "Engenharia, Projetos e Obras", description: "Obras, reformas, construção civil, pavimentação, infraestrutura" },
  { id: "software", slug: "software", name: "Software e Sistemas", description: "Licenças de software, SaaS, desenvolvimento de sistemas, consultoria de TI" },
  { id: "facilities", slug: "facilities", name: "Facilities e Manutenção", description: "Limpeza predial, produtos de limpeza, conservação, portaria, recepção" },
  { id: "saude", slug: "saude", name: "Saúde", description: "Medicamentos, equipamentos hospitalares, insumos médicos" },
  { id: "vigilancia", slug: "vigilancia", name: "Vigilância e Segurança Patrimonial", description: "Vigilância patrimonial, segurança eletrônica, CFTV, alarmes" },
  { id: "transporte", slug: "transporte", name: "Transporte e Veículos", description: "Aquisição/locação de veículos, combustíveis, manutenção de frota" },
  { id: "manutencao_predial", slug: "manutencao-predial", name: "Manutenção e Conservação Predial", description: "Manutenção preventiva/corretiva de edificações, PMOC, ar-condicionado" },
  { id: "engenharia_rodoviaria", slug: "engenharia-rodoviaria", name: "Engenharia Rodoviária e Infraestrutura Viária", description: "Pavimentação, rodovias, pontes, viadutos, sinalização viária" },
  { id: "materiais_eletricos", slug: "materiais-eletricos", name: "Materiais Elétricos e Instalações", description: "Fios, cabos, disjuntores, quadros elétricos, iluminação pública" },
  { id: "materiais_hidraulicos", slug: "materiais-hidraulicos", name: "Materiais Hidráulicos e Saneamento", description: "Tubos, conexões, bombas, tratamento de água, esgoto" },
];

/**
 * Get sector metadata by slug.
 */
export function getSectorBySlug(slug: string): SectorMeta | undefined {
  return SECTORS.find((s) => s.slug === slug);
}

/**
 * Get all sector slugs for generateStaticParams.
 */
export function getAllSectorSlugs(): string[] {
  return SECTORS.map((s) => s.slug);
}

/**
 * Get related sectors (all except current, shuffled, max 4).
 */
export function getRelatedSectors(currentSlug: string): SectorMeta[] {
  const others = SECTORS.filter((s) => s.slug !== currentSlug);
  // Deterministic "shuffle" based on slug — pick evenly spaced sectors
  const step = Math.max(1, Math.floor(others.length / 4));
  const related: SectorMeta[] = [];
  for (let i = 0; i < others.length && related.length < 4; i += step) {
    related.push(others[i]);
  }
  return related;
}

/**
 * Fetch sector stats from backend API (server-side only).
 * Returns null on error (page renders with fallback).
 */
export async function fetchSectorStats(slug: string): Promise<SectorStats | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) return null;

  try {
    const res = await fetch(`${backendUrl}/v1/sectors/${slug}/stats`, {
      next: { revalidate: 21600 }, // 6h ISR
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * Format currency in BRL.
 */
export function formatBRL(value: number): string {
  if (value >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `R$ ${(value / 1_000).toFixed(0)}K`;
  }
  return `R$ ${value.toFixed(0)}`;
}
