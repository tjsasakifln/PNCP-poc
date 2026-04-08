"use client";

import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useAnalytics } from "../../../../hooks/useAnalytics";
import { useAuth } from "../../../components/AuthProvider";
import { UFS } from "../../../../lib/constants/uf-names";
import { safeGetItem } from "../../../../lib/storage";

interface UseSearchFilterPersistenceParams {
  setUfsSelecionadas: (ufs: Set<string>) => void;
  setDataInicial: (date: string) => void;
  setDataFinal: (date: string) => void;
  setSearchMode: (mode: "setor" | "termos") => void;
  setSetorId: (id: string) => void;
  setTermosArray: (terms: string[]) => void;
  setValorMin: (val: number | null) => void;
  setValorMax: (val: number | null) => void;
  setModalidades: (m: number[]) => void;
}

interface UseSearchFilterPersistenceReturn {
  urlParamsApplied: boolean;
}

export function useSearchFilterPersistence(
  params: UseSearchFilterPersistenceParams,
): UseSearchFilterPersistenceReturn {
  const {
    setUfsSelecionadas, setDataInicial, setDataFinal,
    setSearchMode, setSetorId, setTermosArray,
    setValorMin, setValorMax, setModalidades,
  } = params;

  const searchParams = useSearchParams();
  const { trackEvent } = useAnalytics();
  const { user } = useAuth();
  const [urlParamsApplied, setUrlParamsApplied] = useState(false);
  const profileContextAppliedRef = useRef(false);

  // Apply URL params on first render
  useEffect(() => {
    if (urlParamsApplied || !searchParams) return;
    const ufsParam = searchParams.get("ufs");
    const dataInicialParam = searchParams.get("data_inicial");
    const dataFinalParam = searchParams.get("data_final");
    const modeParam = searchParams.get("mode");
    const setorParam = searchParams.get("setor");
    const termosParam = searchParams.get("termos");

    if (ufsParam) {
      const ufsArray = ufsParam.split(",").filter(uf => (UFS as readonly string[]).includes(uf));
      if (ufsArray.length > 0) {
        setUfsSelecionadas(new Set(ufsArray));
        if (dataInicialParam) setDataInicial(dataInicialParam);
        if (dataFinalParam) setDataFinal(dataFinalParam);
        if (modeParam === "termos" && termosParam) {
          setSearchMode("termos");
          setTermosArray(termosParam.split(" ").filter(Boolean));
        } else if (modeParam === "setor" && setorParam) {
          setSearchMode("setor");
          setSetorId(setorParam);
        }
        trackEvent("search_params_loaded_from_url", {
          ufs: ufsArray, mode: modeParam, setor: setorParam, has_termos: Boolean(termosParam),
        });
      }
    }
    setUrlParamsApplied(true);
  }, [searchParams, urlParamsApplied]);

  // Pre-select sector from user profile (after URL params resolved)
  useEffect(() => {
    if (urlParamsApplied && !searchParams?.get("setor")) {
      const userSector = user?.user_metadata?.sector;
      if (userSector && typeof userSector === "string") {
        setSetorId(userSector);
      }
    }
  }, [user, urlParamsApplied, searchParams]);

  // Apply non-UF search defaults from profile context
  useEffect(() => {
    if (profileContextAppliedRef.current) return;
    if (!urlParamsApplied) return;
    if (searchParams?.get("ufs") || searchParams?.get("setor")) return;

    const cachedContext = typeof window !== "undefined" ? safeGetItem("smartlic-profile-context") : null;
    if (!cachedContext) return;

    try {
      const ctx = JSON.parse(cachedContext);
      if (!ctx.porte_empresa) return;
      profileContextAppliedRef.current = true;
      if (ctx.faixa_valor_min != null) setValorMin(ctx.faixa_valor_min);
      if (ctx.faixa_valor_max != null) setValorMax(ctx.faixa_valor_max);
      if (ctx.modalidades_interesse && Array.isArray(ctx.modalidades_interesse) && ctx.modalidades_interesse.length > 0) {
        setModalidades(ctx.modalidades_interesse);
      }
    } catch { /* invalid cache */ }
  }, [urlParamsApplied, searchParams]);

  return { urlParamsApplied };
}
