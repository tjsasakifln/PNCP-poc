"use client";

import { useState, useEffect } from "react";
import type { StatusLicitacao } from "../../components/StatusFilter";
import type { Esfera } from "../../../components/EsferaFilter";
import type { Municipio } from "../../../components/MunicipioFilter";
import type { OrdenacaoOption } from "../../../components/OrdenacaoSelect";
import { UFS } from "../../../../lib/constants/uf-names";
import { safeGetItem, safeSetItem } from "../../../../lib/storage";
import { getBrtDate, addDays } from "../../utils/dates";

export const DEFAULT_SEARCH_DAYS = 10;

interface UseSearchFormStateReturn {
  searchMode: "setor" | "termos";
  setSearchMode: (mode: "setor" | "termos") => void;
  modoBusca: "abertas" | "publicacao";
  setModoBusca: (mode: "abertas" | "publicacao") => void;
  termosArray: string[];
  setTermosArray: (terms: string[]) => void;
  termoInput: string;
  setTermoInput: (input: string) => void;
  ufsSelecionadas: Set<string>;
  setUfsSelecionadas: (ufs: Set<string>) => void;
  dataInicial: string;
  setDataInicial: (date: string) => void;
  dataFinal: string;
  setDataFinal: (date: string) => void;
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
  esferas: Esfera[];
  setEsferas: (esferas: Esfera[]) => void;
  municipios: Municipio[];
  setMunicipios: (municipios: Municipio[]) => void;
  ordenacao: OrdenacaoOption;
  setOrdenacao: (ord: OrdenacaoOption) => void;
  locationFiltersOpen: boolean;
  setLocationFiltersOpen: (open: boolean) => void;
  advancedFiltersOpen: boolean;
  setAdvancedFiltersOpen: (open: boolean) => void;
}

export function useSearchFormState(clearResult: () => void): UseSearchFormStateReturn {
  const [searchMode, _setSearchMode] = useState<"setor" | "termos">("setor");
  const [modoBusca, _setModoBusca] = useState<"abertas" | "publicacao">("abertas");
  const [termosArray, setTermosArray] = useState<string[]>([]);
  const [termoInput, setTermoInput] = useState("");
  const [status, _setStatus] = useState<StatusLicitacao>("recebendo_proposta");
  const [modalidades, _setModalidades] = useState<number[]>([]);
  const [valorMin, _setValorMin] = useState<number | null>(null);
  const [valorMax, _setValorMax] = useState<number | null>(null);
  const [valorValid, setValorValid] = useState(true);
  const [esferas, _setEsferas] = useState<Esfera[]>(["F", "E", "M"]);
  const [municipios, _setMunicipios] = useState<Municipio[]>([]);
  const [ordenacao, setOrdenacao] = useState<OrdenacaoOption>("data_desc");

  const [locationFiltersOpen, setLocationFiltersOpen] = useState(() => {
    if (typeof window === "undefined") return false;
    return safeGetItem("smartlic-location-filters") === "open";
  });
  const [advancedFiltersOpen, setAdvancedFiltersOpen] = useState(() => {
    if (typeof window === "undefined") return false;
    return safeGetItem("smartlic-advanced-filters") === "open";
  });

  // UFs — smart default: profile context → SP
  const [ufsSelecionadas, setUfsSelecionadas] = useState<Set<string>>(() => {
    if (typeof window !== "undefined") {
      try {
        const cached = safeGetItem("smartlic-profile-context");
        if (cached) {
          const ctx = JSON.parse(cached);
          if (ctx.ufs_atuacao && Array.isArray(ctx.ufs_atuacao) && ctx.ufs_atuacao.length > 0) {
            const valid = ctx.ufs_atuacao.filter((uf: string) => (UFS as readonly string[]).includes(uf));
            if (valid.length > 0) return new Set(valid);
          }
        }
      } catch { /* fall through */ }
    }
    return new Set(["SP"]);
  });

  const [dataInicial, setDataInicial] = useState(() => addDays(getBrtDate(), -DEFAULT_SEARCH_DAYS));
  const [dataFinal, setDataFinal] = useState(() => getBrtDate());

  // Override dates when modoBusca changes to "abertas"
  useEffect(() => {
    if (modoBusca === "abertas") {
      const today = getBrtDate();
      setDataFinal(today);
      setDataInicial(addDays(today, -DEFAULT_SEARCH_DAYS));
    }
  }, [modoBusca]);

  // Persist collapsible states
  useEffect(() => { safeSetItem("smartlic-location-filters", locationFiltersOpen ? "open" : "closed"); }, [locationFiltersOpen]);
  useEffect(() => { safeSetItem("smartlic-advanced-filters", advancedFiltersOpen ? "open" : "closed"); }, [advancedFiltersOpen]);

  // Clear municipios when UFs change
  useEffect(() => { _setMunicipios([]); }, [Array.from(ufsSelecionadas).sort().join(",")]);

  const setSearchMode = (mode: "setor" | "termos") => { _setSearchMode(mode); clearResult(); };
  const setModoBusca = (mode: "abertas" | "publicacao") => { _setModoBusca(mode); clearResult(); };
  const setStatus = (s: StatusLicitacao) => { _setStatus(s); clearResult(); };
  const setModalidades = (m: number[]) => { _setModalidades(m); clearResult(); };
  const setValorMin = (v: number | null) => { _setValorMin(v); clearResult(); };
  const setValorMax = (v: number | null) => { _setValorMax(v); clearResult(); };
  const setEsferas = (e: Esfera[]) => { _setEsferas(e); clearResult(); };
  const setMunicipios = (m: Municipio[]) => { _setMunicipios(m); clearResult(); };

  return {
    searchMode, setSearchMode,
    modoBusca, setModoBusca,
    termosArray, setTermosArray,
    termoInput, setTermoInput,
    ufsSelecionadas, setUfsSelecionadas,
    dataInicial, setDataInicial: (d: string) => { setDataInicial(d); clearResult(); },
    dataFinal, setDataFinal: (d: string) => { setDataFinal(d); clearResult(); },
    status, setStatus,
    modalidades, setModalidades,
    valorMin, setValorMin,
    valorMax, setValorMax,
    valorValid, setValorValid,
    esferas, setEsferas,
    municipios, setMunicipios,
    ordenacao, setOrdenacao,
    locationFiltersOpen, setLocationFiltersOpen,
    advancedFiltersOpen, setAdvancedFiltersOpen,
  };
}
