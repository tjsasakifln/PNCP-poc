"use client";

import { useState, useCallback, useEffect } from "react";
import { supabase } from "../../../../lib/supabase";
import { useAuth } from "../../../components/AuthProvider";
import { toast } from "sonner";

export interface FilterPreset {
  id: string;
  name: string;
  filters_json: Record<string, unknown>;
  created_at: string;
}

export interface SavedPresetsState {
  presets: FilterPreset[];
  loading: boolean;
  saving: boolean;
  fetchPresets: () => Promise<void>;
  savePreset: (name: string, filtersJson: Record<string, unknown>) => Promise<FilterPreset | null>;
  deletePreset: (id: string) => Promise<void>;
  canSaveMore: boolean;
}

const MAX_PRESETS = 10;

export function useSavedFilterPresets(): SavedPresetsState {
  const { session } = useAuth();
  const [presets, setPresets] = useState<FilterPreset[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchPresets = useCallback(async () => {
    if (!session?.user?.id) return;
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from("saved_filter_presets")
        .select("id, name, filters_json, created_at")
        .eq("user_id", session.user.id)
        .order("created_at", { ascending: false })
        .limit(MAX_PRESETS);

      if (error) throw error;
      setPresets((data as FilterPreset[]) || []);
    } catch (e) {
      console.error("[useSavedFilterPresets] fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, [session?.user?.id]);

  useEffect(() => { fetchPresets(); }, [fetchPresets]);

  const savePreset = useCallback(async (
    name: string,
    filtersJson: Record<string, unknown>,
  ): Promise<FilterPreset | null> => {
    if (!session?.user?.id) { toast.error("Faça login para salvar presets"); return null; }
    if (presets.length >= MAX_PRESETS) {
      toast.error(`Limite de ${MAX_PRESETS} presets atingido. Delete um antes de salvar.`);
      return null;
    }
    setSaving(true);
    try {
      const { data, error } = await supabase
        .from("saved_filter_presets")
        .insert({ user_id: session.user.id, name: name.trim(), filters_json: filtersJson })
        .select("id, name, filters_json, created_at")
        .single();

      if (error) {
        if (error.message?.includes("Limite de 10")) {
          toast.error(`Limite de ${MAX_PRESETS} presets atingido.`);
        } else {
          toast.error("Erro ao salvar preset. Tente novamente.");
        }
        return null;
      }

      const preset = data as FilterPreset;
      setPresets(prev => [preset, ...prev]);
      toast.success(`Preset "${name}" salvo!`);
      return preset;
    } catch {
      toast.error("Erro ao salvar preset.");
      return null;
    } finally {
      setSaving(false);
    }
  }, [session?.user?.id, presets.length]);

  const deletePreset = useCallback(async (id: string) => {
    if (!session?.user?.id) return;
    const preset = presets.find(p => p.id === id);
    try {
      const { error } = await supabase
        .from("saved_filter_presets")
        .delete()
        .eq("id", id)
        .eq("user_id", session.user.id);

      if (error) throw error;
      setPresets(prev => prev.filter(p => p.id !== id));
      toast.success(`Preset "${preset?.name}" removido.`);
    } catch {
      toast.error("Erro ao remover preset.");
    }
  }, [session?.user?.id, presets]);

  return {
    presets,
    loading,
    saving,
    fetchPresets,
    savePreset,
    deletePreset,
    canSaveMore: presets.length < MAX_PRESETS,
  };
}
