"use client";

import { useState, useCallback, useEffect } from "react";
import { useAuth } from "../app/components/AuthProvider";
import type { PipelineItem, PipelineStage } from "../app/pipeline/types";

export function usePipeline() {
  const { session } = useAuth();
  const [items, setItems] = useState<PipelineItem[]>([]);
  const [alerts, setAlerts] = useState<PipelineItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const authHeaders = useCallback(() => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (session?.access_token) {
      headers["Authorization"] = `Bearer ${session.access_token}`;
    }
    return headers;
  }, [session]);

  const fetchItems = useCallback(async (stage?: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (stage) params.set("stage", stage);
      params.set("limit", "200");
      const res = await fetch(`/api/pipeline?${params.toString()}`, {
        headers: authHeaders(),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail?.message || data.message || data.detail || "Erro ao carregar pipeline");
      }
      const data = await res.json();
      setItems(data.items || []);
      setTotal(data.total || 0);
      return data.items as PipelineItem[];
    } catch (err: any) {
      setError(err.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, [authHeaders]);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch("/api/pipeline?_path=/pipeline/alerts", {
        headers: authHeaders(),
      });
      if (!res.ok) return;
      const data = await res.json();
      setAlerts(data.items || []);
    } catch {
      // Silent fail for alerts
    }
  }, [authHeaders]);

  const addItem = useCallback(async (item: Omit<PipelineItem, "id" | "user_id" | "created_at" | "updated_at">) => {
    try {
      const res = await fetch("/api/pipeline", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(item),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (res.status === 409) throw new Error("Esta licitação já está no seu pipeline.");
        if (res.status === 403) throw new Error(data.detail?.message || "Pipeline não disponível no seu plano.");
        throw new Error(data.detail || "Erro ao adicionar ao pipeline.");
      }
      const newItem = await res.json();
      setItems((prev) => [newItem, ...prev]);
      return newItem as PipelineItem;
    } catch (err: any) {
      throw err;
    }
  }, [authHeaders]);

  const updateItem = useCallback(async (itemId: string, update: { stage?: PipelineStage; notes?: string }) => {
    try {
      const res = await fetch("/api/pipeline", {
        method: "PATCH",
        headers: authHeaders(),
        body: JSON.stringify({ item_id: itemId, ...update }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Erro ao atualizar item.");
      }
      const updated = await res.json();
      setItems((prev) => prev.map((i) => (i.id === itemId ? updated : i)));
      return updated as PipelineItem;
    } catch (err: any) {
      throw err;
    }
  }, [authHeaders]);

  const removeItem = useCallback(async (itemId: string) => {
    try {
      const res = await fetch(`/api/pipeline?id=${itemId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Erro ao remover item.");
      }
      setItems((prev) => prev.filter((i) => i.id !== itemId));
    } catch (err: any) {
      throw err;
    }
  }, [authHeaders]);

  return {
    items,
    alerts,
    total,
    loading,
    error,
    fetchItems,
    fetchAlerts,
    addItem,
    updateItem,
    removeItem,
  };
}
