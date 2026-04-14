"use client";

import { useCallback } from "react";
import useSWR from "swr";
import { useAuth } from "../app/components/AuthProvider";
import type { PipelineItem, PipelineStage, PipelineListResponse } from "../app/pipeline/types";
import { getUserFriendlyError } from "../lib/error-messages";
import { FetchError } from "../lib/fetcher";
import { useAnalytics } from "./useAnalytics";

// STORY-2.1 (EPIC-TD-2026Q2): Reuse the shared PipelineListResponse shape
// declared in app/pipeline/types.ts. Backend counterpart is
// backend/schemas/pipeline.py::PipelineListResponse. After the next
// regeneration of api-types.generated.ts (CI: api-types-check.yml) this
// can be swapped for `components["schemas"]["PipelineListResponse"]`.
type PipelineApiResponse = Pick<PipelineListResponse, "items" | "total">;

/**
 * TD-008 AC6/AC9/AC11/AC12: SWR-based pipeline hook.
 * - GET uses useSWR with deduplication
 * - Mutations use direct fetch + mutate() for cache invalidation
 * - Optimistic updates via setItems in mutate callback
 */

const fetchPipelineWithAuth = async (url: string, token: string) => {
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new FetchError(
      data.detail?.message || data.message || data.detail || "Erro ao carregar pipeline",
      res.status
    );
  }
  return res.json();
};

export function usePipeline() {
  const { session } = useAuth();
  const accessToken = session?.access_token;
  const { trackEvent } = useAnalytics();

  // AC6: SWR for GET /api/pipeline
  const {
    data: pipelineData,
    error: pipelineError,
    isLoading,
    mutate,
  } = useSWR(
    accessToken ? ["/api/pipeline?limit=200", accessToken] : null,
    ([url, token]: [string, string]) => fetchPipelineWithAuth(url, token),
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
      errorRetryCount: 2,
    }
  );

  // AC6: SWR for alerts
  const { data: alertsData } = useSWR(
    accessToken ? ["/api/pipeline?_path=/pipeline/alerts", accessToken] : null,
    ([url, token]: [string, string]) => fetchPipelineWithAuth(url, token),
    {
      revalidateOnFocus: false,
      dedupingInterval: 30000,
      errorRetryCount: 1,
    }
  );

  const items: PipelineItem[] = pipelineData?.items || [];
  const alerts: PipelineItem[] = alertsData?.items || [];
  const total: number = pipelineData?.total || 0;

  const authHeaders = useCallback(() => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
    return headers;
  }, [accessToken]);

  // AC6: fetchItems triggers SWR revalidation (backward compat)
  const fetchItems = useCallback(
    async (stage?: string) => {
      if (stage) {
        // For stage-filtered fetches, do a direct fetch (SWR key is for all items)
        try {
          const params = new URLSearchParams();
          params.set("stage", stage);
          params.set("limit", "200");
          const res = await fetch(`/api/pipeline?${params.toString()}`, {
            headers: authHeaders(),
          });
          if (!res.ok) throw new Error("Erro ao carregar pipeline");
          const data = await res.json();
          return (data.items || []) as PipelineItem[];
        } catch {
          return [];
        }
      }
      // No stage filter — revalidate SWR cache
      const data = await mutate();
      return (data?.items || []) as PipelineItem[];
    },
    [authHeaders, mutate]
  );

  const fetchAlerts = useCallback(async () => {
    // SWR handles this automatically, but provide manual trigger for compat
    await mutate();
  }, [mutate]);

  // AC9: Mutation — add item with AC12 cache invalidation
  const addItem = useCallback(
    async (item: Omit<PipelineItem, "id" | "user_id" | "created_at" | "updated_at" | "version">) => {
      const res = await fetch("/api/pipeline", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(item),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (res.status === 409) {
          // ISSUE-021: Treat duplicate as soft success — refresh and return
          await mutate();
          return data as PipelineItem;
        }
        if (res.status === 403) {
          if (data.detail?.error_code === "PIPELINE_LIMIT_EXCEEDED") {
            const pipelineErr = Object.assign(
            new Error(`Limite de ${data.detail.limit} itens no pipeline atingido.`),
            { isPipelineLimitExceeded: true as const, limit: data.detail.limit as number, current: data.detail.current as number }
          );
            throw pipelineErr;
          }
          throw new Error(data.detail?.message || "Pipeline não disponível no seu plano.");
        }
        throw new Error(data.detail || "Erro ao adicionar ao pipeline.");
      }
      const newItem = await res.json();
      // AC11: Optimistic update + AC12: cache invalidation
      await mutate(
        (current: PipelineApiResponse | undefined) => ({
          ...current,
          items: [newItem, ...(current?.items || [])],
          total: (current?.total || 0) + 1,
        }),
        { revalidate: true, rollbackOnError: true }
      );
      trackEvent('pipeline_item_added', {
        stage: newItem.stage,
        item_id: newItem.id,
      });
      return newItem as PipelineItem;
    },
    [authHeaders, mutate, trackEvent]
  );

  // AC9: Mutation — update item (stage/notes)
  const updateItem = useCallback(
    async (itemId: string, update: { stage?: PipelineStage; notes?: string; version?: number }) => {
      const currentItem = items.find((i) => i.id === itemId);
      const version = update.version ?? currentItem?.version;
      const res = await fetch("/api/pipeline", {
        method: "PATCH",
        headers: authHeaders(),
        body: JSON.stringify({ item_id: itemId, ...update, version }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (res.status === 409) {
          const conflictErr = Object.assign(
          new Error(data.detail || "Item foi atualizado por outra operação. Recarregue a página."),
          { isConflict: true as const }
        );
          throw conflictErr;
        }
        throw new Error(data.detail || "Erro ao atualizar item.");
      }
      const updated = await res.json();
      // AC11: Optimistic update
      await mutate(
        (current: PipelineApiResponse | undefined) => ({
          ...current,
          items: (current?.items || []).map((i: PipelineItem) =>
            i.id === itemId ? updated : i
          ),
        }),
        { revalidate: true, rollbackOnError: true }
      );
      return updated as PipelineItem;
    },
    [authHeaders, items, mutate]
  );

  // AC9: Mutation — remove item
  const removeItem = useCallback(
    async (itemId: string) => {
      const res = await fetch(`/api/pipeline?id=${itemId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Erro ao remover item.");
      }
      // AC11: Optimistic update
      await mutate(
        (current: PipelineApiResponse | undefined) => ({
          ...current,
          items: (current?.items || []).filter((i: PipelineItem) => i.id !== itemId),
          total: Math.max(0, (current?.total || 0) - 1),
        }),
        { revalidate: true, rollbackOnError: true }
      );
    },
    [authHeaders, mutate]
  );

  return {
    items,
    alerts,
    total,
    loading: isLoading,
    error: pipelineError ? getUserFriendlyError(pipelineError) : null,
    fetchItems,
    fetchAlerts,
    addItem,
    updateItem,
    removeItem,
  };
}
