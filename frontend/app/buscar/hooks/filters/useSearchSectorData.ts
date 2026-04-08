"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { Setor } from "../../../../app/types";
import { SETORES_FALLBACK, getCachedSectors, getStaleCachedSectors, cacheSectors } from "./sectorData";

interface UseSearchSectorDataReturn {
  setores: Setor[];
  setoresLoading: boolean;
  setoresError: boolean;
  setoresUsingFallback: boolean;
  setoresUsingStaleCache: boolean;
  staleCacheAge: number | null;
  setoresRetryCount: number;
  setorId: string;
  setSetorId: (id: string) => void;
  fetchSetores: (attempt?: number) => Promise<void>;
}

export function useSearchSectorData(
  onSetorChange?: () => void,
): UseSearchSectorDataReturn {
  const [setores, setSetores] = useState<Setor[]>([]);
  const [setoresLoading, setSetoresLoading] = useState(true);
  const [setoresError, setSetoresError] = useState(false);
  const [setoresUsingFallback, setSetoresUsingFallback] = useState(false);
  const [setoresUsingStaleCache, setSetoresUsingStaleCache] = useState(false);
  const [staleCacheAge, setStaleCacheAge] = useState<number | null>(null);
  const [setoresRetryCount, setSetoresRetryCount] = useState(0);
  const [setorId, _setSetorId] = useState("vestuario");

  const setSetorId = useCallback((id: string) => {
    _setSetorId(id);
    onSetorChange?.();
  }, [onSetorChange]);

  const fetchSetores = useCallback(async (attempt = 0) => {
    const cachedSectors = getCachedSectors();
    if (cachedSectors && cachedSectors.length > 0) {
      setSetores(cachedSectors);
      setSetoresUsingFallback(false);
      setSetoresUsingStaleCache(false);
      setStaleCacheAge(null);
      setSetoresLoading(false);
      return;
    }

    setSetoresLoading(true);
    setSetoresError(false);
    try {
      const res = await fetch("/api/setores");
      const data = await res.json();
      if (data.setores && data.setores.length > 0) {
        setSetores(data.setores);
        setSetoresUsingFallback(false);
        setSetoresUsingStaleCache(false);
        setStaleCacheAge(null);
        cacheSectors(data.setores);
      } else {
        throw new Error("Empty response");
      }
    } catch {
      if (attempt < 2) {
        setTimeout(() => fetchSetores(attempt + 1), Math.pow(2, attempt) * 1000);
        return;
      }
      const stale = getStaleCachedSectors();
      if (stale) {
        setSetores(stale.data);
        setSetoresUsingStaleCache(true);
        setStaleCacheAge(stale.ageMs);
        setSetoresUsingFallback(false);
      } else {
        setSetores(SETORES_FALLBACK);
        setSetoresUsingFallback(true);
        setSetoresUsingStaleCache(false);
        setStaleCacheAge(null);
      }
      setSetoresError(true);
    } finally {
      if (attempt >= 2 || !setoresError) setSetoresLoading(false);
      setSetoresRetryCount(attempt);
    }
  }, []);

  useEffect(() => { fetchSetores(); }, [fetchSetores]);

  // Background revalidation when using stale cache
  const revalidationAttemptRef = useRef(0);
  useEffect(() => {
    if (!setoresUsingStaleCache) { revalidationAttemptRef.current = 0; return; }
    const MAX_ATTEMPTS = 5;
    const INTERVAL_MS = 30_000;
    const intervalId = setInterval(async () => {
      if (revalidationAttemptRef.current >= MAX_ATTEMPTS) { clearInterval(intervalId); return; }
      revalidationAttemptRef.current++;
      try {
        const res = await fetch("/api/setores");
        const data = await res.json();
        if (data.setores && data.setores.length > 0) {
          setSetores(data.setores);
          setSetoresUsingStaleCache(false);
          setStaleCacheAge(null);
          setSetoresError(false);
          cacheSectors(data.setores);
          clearInterval(intervalId);
        }
      } catch { /* continue trying */ }
    }, INTERVAL_MS);
    return () => clearInterval(intervalId);
  }, [setoresUsingStaleCache]);

  return {
    setores, setoresLoading, setoresError, setoresUsingFallback, setoresUsingStaleCache, staleCacheAge, setoresRetryCount,
    setorId, setSetorId, fetchSetores,
  };
}
