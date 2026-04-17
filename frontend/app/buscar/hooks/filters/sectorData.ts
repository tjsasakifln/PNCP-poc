/**
 * Sector data constants and cache utilities.
 * Pure functions — no React hooks.
 */

import type { Setor } from "../../../../app/types";
import { safeGetItem, safeSetItem } from "../../../../lib/storage";

// Fallback sectors list — synced with backend/sectors_data.yaml (STORY-249)
export const SETORES_FALLBACK: Setor[] = [
  { id: "vestuario", name: "Vestuário e Uniformes", description: "Uniformes, fardamentos, roupas profissionais, EPIs de vestuário" },
  { id: "alimentos", name: "Alimentos e Merenda", description: "Gêneros alimentícios, merenda escolar, refeições, rancho" },
  { id: "informatica", name: "Hardware e Equipamentos de TI", description: "Computadores, servidores, periféricos, redes, equipamentos de informática, impressoras, switches, storage" },
  { id: "mobiliario", name: "Mobiliário", description: "Mesas, cadeiras, armários, estantes, móveis de escritório" },
  { id: "papelaria", name: "Papelaria e Material de Escritório", description: "Papel, canetas, material de escritório, suprimentos administrativos" },
  { id: "engenharia", name: "Engenharia, Projetos e Obras", description: "Obras, reformas, construção civil, pavimentação, infraestrutura, escritórios de projeto, consultorias de engenharia, fiscalização, topografia" },
  { id: "software_desenvolvimento", name: "Desenvolvimento de Software e Consultoria de TI", description: "Contratação de desenvolvimento de software customizado, SaaS, implantação de sistemas, consultoria e fábrica de software" },
  { id: "software_licencas", name: "Licenciamento de Software Comercial", description: "Aquisição e renovação de licenças de software de terceiros: Microsoft, Oracle, SAP, Adobe, Autodesk, antivírus, sistemas operacionais" },
  { id: "servicos_prediais", name: "Serviços Prediais e Facilities", description: "Contratação de serviços prediais terceirizados: limpeza e conservação, portaria, zeladoria, copeiragem, jardinagem, dedetização e controle de pragas" },
  { id: "produtos_limpeza", name: "Produtos de Limpeza e Higienização", description: "Aquisição de materiais e produtos de limpeza, higienização e saneantes para uso em repartições públicas e unidades de saúde" },
  { id: "medicamentos", name: "Medicamentos e Produtos Farmacêuticos", description: "Aquisição de medicamentos, fármacos, imunobiológicos e produtos farmacêuticos para assistência farmacêutica, farmácia básica e unidades de saúde" },
  { id: "equipamentos_medicos", name: "Equipamentos Médico-Hospitalares", description: "Aquisição de equipamentos médicos, hospitalares e odontológicos de grande e médio porte, instrumentais, OPME, próteses, órteses e mobiliário hospitalar" },
  { id: "insumos_hospitalares", name: "Insumos e Materiais Hospitalares", description: "Aquisição de insumos hospitalares, materiais médico-hospitalares descartáveis, materiais de laboratório, materiais odontológicos de consumo, nutrição enteral e gases medicinais" },
  { id: "vigilancia", name: "Vigilância e Segurança Patrimonial", description: "Vigilância patrimonial, segurança eletrônica, CFTV, alarmes, controle de acesso, portaria armada/desarmada" },
  { id: "transporte_servicos", name: "Transporte de Pessoas e Cargas", description: "Contratação de serviços de transporte: transporte escolar, fretamento, locação de veículos, translados, transporte de pacientes e cargas" },
  { id: "frota_veicular", name: "Frota e Veículos", description: "Aquisição de veículos, manutenção de frota, combustíveis, pneus, peças automotivas e serviços de oficina" },
  { id: "manutencao_predial", name: "Manutenção e Conservação Predial", description: "Manutenção preventiva/corretiva de edificações, PMOC, ar condicionado, elevadores, instalações elétricas/hidráulicas, pintura predial, impermeabilização" },
  { id: "engenharia_rodoviaria", name: "Engenharia Rodoviária e Infraestrutura Viária", description: "Pavimentação, rodovias, pontes, viadutos, sinalização viária, conservação rodoviária" },
  { id: "materiais_eletricos", name: "Materiais Elétricos e Instalações", description: "Fios, cabos, disjuntores, quadros elétricos, iluminação pública, subestações" },
  { id: "materiais_hidraulicos", name: "Materiais Hidráulicos e Saneamento", description: "Tubos, conexões, bombas, tratamento de água, esgoto, redes de distribuição" },
];

export const SECTOR_CACHE_KEY = "smartlic-sectors-cache-v3";
export const SECTOR_CACHE_TTL = 5 * 60 * 1000;

interface SectorCache { data: Setor[]; timestamp: number; }

export function getCachedSectors(): Setor[] | null {
  if (typeof window === "undefined") return null;
  try {
    const cached = safeGetItem(SECTOR_CACHE_KEY);
    if (!cached) return null;
    const { data, timestamp }: SectorCache = JSON.parse(cached);
    if (Date.now() - timestamp > SECTOR_CACHE_TTL) return null;
    return data;
  } catch { return null; }
}

export function getStaleCachedSectors(): { data: Setor[]; ageMs: number } | null {
  if (typeof window === "undefined") return null;
  try {
    const cached = safeGetItem(SECTOR_CACHE_KEY);
    if (!cached) return null;
    const { data, timestamp }: SectorCache = JSON.parse(cached);
    if (!data || data.length === 0) return null;
    return { data, ageMs: Date.now() - timestamp };
  } catch { return null; }
}

export function cacheSectors(sectors: Setor[]): void {
  if (typeof window === "undefined") return;
  try {
    safeSetItem(SECTOR_CACHE_KEY, JSON.stringify({ data: sectors, timestamp: Date.now() } as SectorCache));
  } catch { /* ignore quota errors */ }
}
