"use client";

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import type { Setor, ValidationErrors } from "../../types";
import { useAnalytics } from "../../../hooks/useAnalytics";
import type { StatusLicitacao } from "../../../components/StatusFilter";
import type { Esfera } from "../../components/EsferaFilter";
import type { Municipio } from "../../components/MunicipioFilter";
import type { OrdenacaoOption } from "../../components/OrdenacaoSelect";
import { UFS } from "../../../lib/constants/uf-names";
import { STOPWORDS_PT, stripAccents, isStopword } from "../../../lib/constants/stopwords";
import { useAuth } from "../../components/AuthProvider";

export interface TermValidation {
  valid: string[];
  ignored: string[];
  reasons: Record<string, string>;
}

const validateTermsClientSide = (terms: string[]): TermValidation => {
  const MIN_LENGTH = 4;
  const valid: string[] = [];
  const ignored: string[] = [];
  const reasons: Record<string, string> = {};

  terms.forEach(term => {
    const cleaned = term.trim().toLowerCase();
    if (!cleaned) {
      ignored.push(term);
      reasons[term] = 'Termo vazio ou apenas espaços';
      return;
    }
    const words = cleaned.split(/\s+/);
    if (words.length === 1 && isStopword(cleaned)) {
      ignored.push(term);
      reasons[term] = 'Palavra comum não indexada (stopword)';
      return;
    }
    if (words.length === 1 && cleaned.length < MIN_LENGTH) {
      ignored.push(term);
      reasons[term] = `Muito curto (mínimo ${MIN_LENGTH} caracteres)`;
      return;
    }
    const hasInvalidChars = !Array.from(cleaned).every(c =>
      /[a-z0-9\s\-áéíóúàèìòùâêîôûãõñç]/i.test(c)
    );
    if (hasInvalidChars) {
      ignored.push(term);
      reasons[term] = 'Contém caracteres especiais não permitidos';
      return;
    }
    valid.push(term);
  });

  return { valid, ignored, reasons };
};

// Fallback sectors list — synced with backend/sectors_data.yaml (STORY-249)
const SETORES_FALLBACK: Setor[] = [
  { id: "vestuario", name: "Vestuário e Uniformes", description: "Uniformes, fardamentos, roupas profissionais, EPIs de vestuário" },
  { id: "alimentos", name: "Alimentos e Merenda", description: "Gêneros alimentícios, merenda escolar, refeições, rancho" },
  { id: "informatica", name: "Hardware e Equipamentos de TI", description: "Computadores, servidores, periféricos, redes, equipamentos de informática, impressoras, switches, storage" },
  { id: "mobiliario", name: "Mobiliário", description: "Mesas, cadeiras, armários, estantes, móveis de escritório" },
  { id: "papelaria", name: "Papelaria e Material de Escritório", description: "Papel, canetas, material de escritório, suprimentos administrativos" },
  { id: "engenharia", name: "Engenharia, Projetos e Obras", description: "Obras, reformas, construção civil, pavimentação, infraestrutura, escritórios de projeto, consultorias de engenharia, fiscalização, topografia" },
  { id: "software", name: "Software e Sistemas", description: "Licenças de software, SaaS, desenvolvimento de sistemas, consultoria de TI" },
  { id: "facilities", name: "Facilities e Manutenção", description: "Limpeza predial, produtos de limpeza, conservação, copa/cozinha, portaria, recepção, zeladoria, jardinagem, manutenção predial" },
  { id: "saude", name: "Saúde", description: "Medicamentos, equipamentos hospitalares, insumos médicos, materiais de laboratório, órteses e próteses" },
  { id: "vigilancia", name: "Vigilância e Segurança Patrimonial", description: "Vigilância patrimonial, segurança eletrônica, CFTV, alarmes, controle de acesso, portaria armada/desarmada" },
  { id: "transporte", name: "Transporte e Veículos", description: "Aquisição/locação de veículos, combustíveis, manutenção de frota, pneus, peças automotivas, gerenciamento de frota" },
  { id: "manutencao_predial", name: "Manutenção e Conservação Predial", description: "Manutenção preventiva/corretiva de edificações, PMOC, ar condicionado, elevadores, instalações elétricas/hidráulicas, pintura predial, impermeabilização" },
  { id: "engenharia_rodoviaria", name: "Engenharia Rodoviária e Infraestrutura Viária", description: "Pavimentação, rodovias, pontes, viadutos, sinalização viária, conservação rodoviária" },
  { id: "materiais_eletricos", name: "Materiais Elétricos e Instalações", description: "Fios, cabos, disjuntores, quadros elétricos, iluminação pública, subestações" },
  { id: "materiais_hidraulicos", name: "Materiais Hidráulicos e Saneamento", description: "Tubos, conexões, bombas, tratamento de água, esgoto, redes de distribuição" },
];

export interface SearchFiltersState {
  // Sectors
  setores: Setor[];
  setoresLoading: boolean;
  setoresError: boolean;
  setoresUsingFallback: boolean;
  setoresRetryCount: number;
  setorId: string;
  setSetorId: (id: string) => void;
  fetchSetores: (attempt?: number) => Promise<void>;

  // Search mode
  searchMode: "setor" | "termos";
  setSearchMode: (mode: "setor" | "termos") => void;

  // Search paradigm (STORY-240)
  modoBusca: "abertas" | "publicacao";
  setModoBusca: (mode: "abertas" | "publicacao") => void;

  // Terms
  termosArray: string[];
  setTermosArray: (terms: string[]) => void;
  termoInput: string;
  setTermoInput: (input: string) => void;
  termValidation: TermValidation | null;
  addTerms: (newTerms: string[]) => void;
  removeTerm: (term: string) => void;

  // UFs
  ufsSelecionadas: Set<string>;
  setUfsSelecionadas: (ufs: Set<string>) => void;
  toggleUf: (uf: string) => void;
  toggleRegion: (regionUfs: string[]) => void;
  selecionarTodos: () => void;
  limparSelecao: () => void;

  // Dates
  dataInicial: string;
  setDataInicial: (date: string) => void;
  dataFinal: string;
  setDataFinal: (date: string) => void;

  // P0 Filters
  status: StatusLicitacao;
  setStatus: (status: StatusLicitacao) => void;
  modalidades: number[];
  setModalidades: (modalidades: number[]) => void;
  valorMin: number | null;
  setValorMin: (val: number | null) => void;
  valorMax: number | null;
  setValorMax: (val: number | null) => void;
  valorValid: boolean;
  setValorValid: (valid: boolean) => void;

  // P1 Filters
  esferas: Esfera[];
  setEsferas: (esferas: Esfera[]) => void;
  municipios: Municipio[];
  setMunicipios: (municipios: Municipio[]) => void;
  ordenacao: OrdenacaoOption;
  setOrdenacao: (ord: OrdenacaoOption) => void;

  // Collapsibles
  locationFiltersOpen: boolean;
  setLocationFiltersOpen: (open: boolean) => void;
  advancedFiltersOpen: boolean;
  setAdvancedFiltersOpen: (open: boolean) => void;

  // Validation
  validationErrors: ValidationErrors;
  canSearch: boolean;

  // Computed
  sectorName: string;
  searchLabel: string;
  dateLabel: string;
  isUsingDefaults: boolean;
  allUfsSelected: boolean;

  // Clear result callback (provided by parent)
  clearResult: () => void;
}

export function useSearchFilters(clearResult: () => void): SearchFiltersState {
  const searchParams = useSearchParams();
  const [urlParamsApplied, setUrlParamsApplied] = useState(false);
  const { trackEvent } = useAnalytics();
  const { user } = useAuth();

  // Sectors state
  const [setores, setSetores] = useState<Setor[]>([]);
  const [setoresLoading, setSetoresLoading] = useState(true);
  const [setoresError, setSetoresError] = useState(false);
  const [setoresUsingFallback, setSetoresUsingFallback] = useState(false);
  const [setoresRetryCount, setSetoresRetryCount] = useState(0);
  const [setorId, setSetorId] = useState("vestuario");
  const [searchMode, setSearchMode] = useState<"setor" | "termos">("setor");
  const [modoBusca, setModoBusca] = useState<"abertas" | "publicacao">("abertas");
  const [termosArray, setTermosArray] = useState<string[]>([]);
  const [termoInput, setTermoInput] = useState("");
  const [termValidation, setTermValidation] = useState<TermValidation | null>(null);

  // P0 Filters
  const [status, setStatus] = useState<StatusLicitacao>("recebendo_proposta");
  const [modalidades, setModalidades] = useState<number[]>([4, 5, 6, 7]);
  const [valorMin, setValorMin] = useState<number | null>(null);
  const [valorMax, setValorMax] = useState<number | null>(null);
  const [valorValid, setValorValid] = useState(true);

  // P1 Filters
  const [esferas, setEsferas] = useState<Esfera[]>([]);
  const [municipios, setMunicipios] = useState<Municipio[]>([]);
  const [ordenacao, setOrdenacao] = useState<OrdenacaoOption>("data_desc");

  // Collapsible states
  const [locationFiltersOpen, setLocationFiltersOpen] = useState(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('smartlic-location-filters') === 'open';
  });
  const [advancedFiltersOpen, setAdvancedFiltersOpen] = useState(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('smartlic-advanced-filters') === 'open';
  });

  // UFs and dates
  const [ufsSelecionadas, setUfsSelecionadas] = useState<Set<string>>(
    new Set(UFS as readonly string[])
  );
  const [dataInicial, setDataInicial] = useState(() => {
    const now = new Date(new Date().toLocaleString("en-US", { timeZone: "America/Sao_Paulo" }));
    now.setDate(now.getDate() - 15);
    return now.toISOString().split("T")[0];
  });
  const [dataFinal, setDataFinal] = useState(() => {
    const now = new Date(new Date().toLocaleString("en-US", { timeZone: "America/Sao_Paulo" }));
    return now.toISOString().split("T")[0];
  });

  // STORY-240 AC7: Override dates when modo_busca changes
  useEffect(() => {
    if (modoBusca === "abertas") {
      const now = new Date(new Date().toLocaleString("en-US", { timeZone: "America/Sao_Paulo" }));
      const dataFim = now.toISOString().split("T")[0];
      now.setDate(now.getDate() - 15);
      const dataIni = now.toISOString().split("T")[0];
      setDataInicial(dataIni);
      setDataFinal(dataFim);
    }
  }, [modoBusca]);

  // Validation
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});

  // URL params handling
  useEffect(() => {
    if (urlParamsApplied) return;
    const ufsParam = searchParams.get('ufs');
    const dataInicialParam = searchParams.get('data_inicial');
    const dataFinalParam = searchParams.get('data_final');
    const modeParam = searchParams.get('mode');
    const setorParam = searchParams.get('setor');
    const termosParam = searchParams.get('termos');

    if (ufsParam) {
      const ufsArray = ufsParam.split(',').filter(uf => (UFS as readonly string[]).includes(uf));
      if (ufsArray.length > 0) {
        setUfsSelecionadas(new Set(ufsArray));
        if (dataInicialParam) setDataInicial(dataInicialParam);
        if (dataFinalParam) setDataFinal(dataFinalParam);
        if (modeParam === 'termos' && termosParam) {
          setSearchMode('termos');
          setTermosArray(termosParam.split(' ').filter(Boolean));
        } else if (modeParam === 'setor' && setorParam) {
          setSearchMode('setor');
          setSetorId(setorParam);
        }
        trackEvent('search_params_loaded_from_url', {
          ufs: ufsArray, mode: modeParam, setor: setorParam, has_termos: Boolean(termosParam),
        });
      }
    }
    setUrlParamsApplied(true);
  }, [searchParams, urlParamsApplied, trackEvent]);

  // Persist collapsible states
  useEffect(() => {
    localStorage.setItem('smartlic-location-filters', locationFiltersOpen ? 'open' : 'closed');
  }, [locationFiltersOpen]);
  useEffect(() => {
    localStorage.setItem('smartlic-advanced-filters', advancedFiltersOpen ? 'open' : 'closed');
  }, [advancedFiltersOpen]);

  // STORY-246 AC3: Pre-select sector from user profile (only if no URL params override)
  useEffect(() => {
    if (urlParamsApplied && !searchParams.get('setor')) {
      const userSector = user?.user_metadata?.sector;
      if (userSector && typeof userSector === 'string') {
        setSetorId(userSector);
      }
    }
  }, [user, urlParamsApplied, searchParams]);

  // STORY-247 AC12: Load search defaults from profile context
  const profileContextAppliedRef = useRef(false);
  useEffect(() => {
    if (profileContextAppliedRef.current) return;
    if (!urlParamsApplied) return;
    // Don't override if URL params were provided
    if (searchParams.get('ufs') || searchParams.get('setor')) return;

    const cachedContext = typeof window !== 'undefined'
      ? localStorage.getItem('smartlic-profile-context')
      : null;
    if (!cachedContext) return;

    try {
      const ctx = JSON.parse(cachedContext);
      if (!ctx.porte_empresa) return; // Not completed

      profileContextAppliedRef.current = true;

      // Apply UFs from profile
      if (ctx.ufs_atuacao && Array.isArray(ctx.ufs_atuacao) && ctx.ufs_atuacao.length > 0) {
        setUfsSelecionadas(new Set(ctx.ufs_atuacao.filter((uf: string) => (UFS as readonly string[]).includes(uf))));
      }

      // Apply value range from profile
      if (ctx.faixa_valor_min != null) setValorMin(ctx.faixa_valor_min);
      if (ctx.faixa_valor_max != null) setValorMax(ctx.faixa_valor_max);

      // Apply modalidades from profile
      if (ctx.modalidades_interesse && Array.isArray(ctx.modalidades_interesse) && ctx.modalidades_interesse.length > 0) {
        setModalidades(ctx.modalidades_interesse);
      }
    } catch {
      // Invalid cache, ignore
    }
  }, [urlParamsApplied, searchParams]);

  // Clear municipios when UFs change
  useEffect(() => {
    setMunicipios([]);
  }, [Array.from(ufsSelecionadas).sort().join(",")]);

  // Sector caching configuration (FE-NEW-08)
  // STORY-249 AC11: Bump version when sector IDs/names change to invalidate old cache
  const SECTOR_CACHE_KEY = "smartlic-sectors-cache-v2";
  const SECTOR_CACHE_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

  interface SectorCache {
    data: Setor[];
    timestamp: number;
  }

  // Check if cache is valid
  const getCachedSectors = (): Setor[] | null => {
    if (typeof window === 'undefined') return null;
    try {
      const cached = localStorage.getItem(SECTOR_CACHE_KEY);
      if (!cached) return null;

      const { data, timestamp }: SectorCache = JSON.parse(cached);
      const age = Date.now() - timestamp;

      if (age > SECTOR_CACHE_TTL) {
        // Cache expired
        localStorage.removeItem(SECTOR_CACHE_KEY);
        return null;
      }

      return data;
    } catch {
      return null;
    }
  };

  // Save sectors to cache
  const cacheSectors = (sectors: Setor[]) => {
    if (typeof window === 'undefined') return;
    try {
      const cache: SectorCache = {
        data: sectors,
        timestamp: Date.now(),
      };
      localStorage.setItem(SECTOR_CACHE_KEY, JSON.stringify(cache));
    } catch {
      // Ignore cache errors (e.g., quota exceeded)
    }
  };

  // Fetch sectors with caching
  const fetchSetores = async (attempt = 0) => {
    // Try cache first
    const cachedSectors = getCachedSectors();
    if (cachedSectors && cachedSectors.length > 0) {
      setSetores(cachedSectors);
      setSetoresUsingFallback(false);
      setSetoresLoading(false);
      return;
    }

    // Cache miss or expired - fetch from API
    setSetoresLoading(true);
    setSetoresError(false);
    try {
      const res = await fetch("/api/setores");
      const data = await res.json();
      if (data.setores && data.setores.length > 0) {
        setSetores(data.setores);
        setSetoresUsingFallback(false);
        cacheSectors(data.setores); // Cache successful response
      } else {
        throw new Error("Empty response");
      }
    } catch {
      if (attempt < 2) {
        setTimeout(() => fetchSetores(attempt + 1), Math.pow(2, attempt) * 1000);
        return;
      }
      setSetores(SETORES_FALLBACK);
      setSetoresUsingFallback(true);
      setSetoresError(true);
    } finally {
      if (attempt >= 2 || !setoresError) {
        setSetoresLoading(false);
      }
      setSetoresRetryCount(attempt);
    }
  };

  useEffect(() => { fetchSetores(); }, []);

  // Validation
  function validateForm(): ValidationErrors {
    const errors: ValidationErrors = {};
    if (ufsSelecionadas.size === 0) errors.ufs = "Selecione pelo menos um estado";
    if (dataFinal < dataInicial) errors.date_range = "Data final deve ser maior ou igual à data inicial";
    return errors;
  }

  const canSearch = Object.keys(validateForm()).length === 0
    && (searchMode === "setor" || (termosArray.length > 0 && (!termValidation || termValidation.valid.length > 0)))
    && valorValid;

  useEffect(() => { setValidationErrors(validateForm()); }, [ufsSelecionadas, dataInicial, dataFinal]);

  // Term validation
  const updateTermValidation = (terms: string[]) => {
    if (searchMode === "termos" && terms.length > 0) {
      setTermValidation(validateTermsClientSide(terms));
    } else {
      setTermValidation(null);
    }
  };

  useEffect(() => {
    if (searchMode === "termos") updateTermValidation(termosArray);
    else setTermValidation(null);
  }, [searchMode, termosArray]);

  // Term helpers
  const addTerms = (newTerms: string[]) => {
    const updated = [...termosArray, ...newTerms.filter(t => !termosArray.includes(t))];
    setTermosArray(updated);
    updateTermValidation(updated);
    clearResult();
  };

  const removeTerm = (termToRemove: string) => {
    const updated = termosArray.filter(t => t !== termToRemove);
    setTermosArray(updated);
    updateTermValidation(updated);
    clearResult();
  };

  // UF helpers
  const toggleUf = (uf: string) => {
    const newSet = new Set(ufsSelecionadas);
    if (newSet.has(uf)) newSet.delete(uf);
    else newSet.add(uf);
    setUfsSelecionadas(newSet);
    clearResult();
  };

  const toggleRegion = (regionUfs: string[]) => {
    const allSelected = regionUfs.every(uf => ufsSelecionadas.has(uf));
    const newSet = new Set(ufsSelecionadas);
    if (allSelected) regionUfs.forEach(uf => newSet.delete(uf));
    else regionUfs.forEach(uf => newSet.add(uf));
    setUfsSelecionadas(newSet);
    clearResult();
  };

  const selecionarTodos = () => { setUfsSelecionadas(new Set(UFS)); clearResult(); };
  const limparSelecao = () => { setUfsSelecionadas(new Set()); clearResult(); };

  // Computed values
  const sectorName = searchMode === "setor"
    ? (setores.find(s => s.id === setorId)?.name || "Licitações")
    : "Licitações";

  const searchLabel = searchMode === "setor"
    ? sectorName
    : termosArray.length > 0
      ? `"${termosArray.join('", "')}"`
      : "Licitações";

  const dateLabel = modoBusca === "abertas"
    ? "Mostrando licitações abertas para proposta"
    : "Período de publicação";

  // STORY-246 AC1-AC4: Compute smart defaults state
  const allUfsSelected = ufsSelecionadas.size === UFS.length;
  const isUsingDefaults = allUfsSelected &&
    modalidades.length === 4 &&
    modalidades.includes(4) &&
    modalidades.includes(5) &&
    modalidades.includes(6) &&
    modalidades.includes(7);

  return {
    setores, setoresLoading, setoresError, setoresUsingFallback, setoresRetryCount,
    setorId, setSetorId: (id: string) => { setSetorId(id); clearResult(); },
    fetchSetores,
    searchMode, setSearchMode: (mode: "setor" | "termos") => { setSearchMode(mode); clearResult(); },
    modoBusca, setModoBusca: (mode: "abertas" | "publicacao") => { setModoBusca(mode); clearResult(); },
    termosArray, setTermosArray, termoInput, setTermoInput,
    termValidation, addTerms, removeTerm,
    ufsSelecionadas, setUfsSelecionadas,
    toggleUf, toggleRegion, selecionarTodos, limparSelecao,
    dataInicial, setDataInicial: (d: string) => { setDataInicial(d); clearResult(); },
    dataFinal, setDataFinal: (d: string) => { setDataFinal(d); clearResult(); },
    status, setStatus: (s: StatusLicitacao) => { setStatus(s); clearResult(); },
    modalidades, setModalidades: (m: number[]) => { setModalidades(m); clearResult(); },
    valorMin, setValorMin: (v: number | null) => { setValorMin(v); clearResult(); },
    valorMax, setValorMax: (v: number | null) => { setValorMax(v); clearResult(); },
    valorValid, setValorValid,
    esferas, setEsferas: (e: Esfera[]) => { setEsferas(e); clearResult(); },
    municipios, setMunicipios: (m: Municipio[]) => { setMunicipios(m); clearResult(); },
    ordenacao, setOrdenacao,
    locationFiltersOpen, setLocationFiltersOpen,
    advancedFiltersOpen, setAdvancedFiltersOpen,
    validationErrors, canSearch,
    sectorName, searchLabel, dateLabel,
    isUsingDefaults, allUfsSelected,
    clearResult,
  };
}

export { validateTermsClientSide, SETORES_FALLBACK };
export type { StatusLicitacao, Esfera, Municipio, OrdenacaoOption };
