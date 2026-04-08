"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Bookmark, Plus, Trash2, ChevronDown, Loader2 } from "lucide-react";
import { useSavedFilterPresets, type FilterPreset } from "../hooks/useSavedFilterPresets";

const MAX_PRESETS = 10;

interface ApplyPresetFilters {
  setUfsSelecionadas?: (ufs: Set<string>) => void;
  setSearchMode?: (mode: "setor" | "termos") => void;
  setSetorId?: (id: string) => void;
  setTermosArray?: (terms: string[]) => void;
  setStatus?: (status: string) => void;
  setModalidades?: (m: number[]) => void;
  setValorMin?: (v: number | null) => void;
  setValorMax?: (v: number | null) => void;
}

interface SavedPresetsProps {
  /** Current filter state to snapshot when saving */
  getCurrentFilters: () => Record<string, unknown>;
  /** Callbacks to apply a loaded preset */
  applyFilters: ApplyPresetFilters;
}

export default function SavedPresets({ getCurrentFilters, applyFilters }: SavedPresetsProps) {
  const { presets, loading, saving, savePreset, deletePreset, canSaveMore } = useSavedFilterPresets();
  const [open, setOpen] = useState(false);
  const [saveMode, setSaveMode] = useState(false);
  const [presetName, setPresetName] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
        setSaveMode(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  useEffect(() => {
    if (saveMode && inputRef.current) inputRef.current.focus();
  }, [saveMode]);

  const handleApply = useCallback((preset: FilterPreset) => {
    const f = preset.filters_json;
    if (Array.isArray(f.ufs) && applyFilters.setUfsSelecionadas) {
      applyFilters.setUfsSelecionadas(new Set(f.ufs as string[]));
    }
    if (f.searchMode && applyFilters.setSearchMode) {
      applyFilters.setSearchMode(f.searchMode as "setor" | "termos");
    }
    if (f.setorId && applyFilters.setSetorId) applyFilters.setSetorId(f.setorId as string);
    if (Array.isArray(f.termosArray) && applyFilters.setTermosArray) applyFilters.setTermosArray(f.termosArray as string[]);
    if (f.status && applyFilters.setStatus) applyFilters.setStatus(f.status as string);
    if (Array.isArray(f.modalidades) && applyFilters.setModalidades) applyFilters.setModalidades(f.modalidades as number[]);
    if (applyFilters.setValorMin) applyFilters.setValorMin(typeof f.valorMin === "number" ? f.valorMin : null);
    if (applyFilters.setValorMax) applyFilters.setValorMax(typeof f.valorMax === "number" ? f.valorMax : null);
    setOpen(false);
  }, [applyFilters]);

  const handleSave = useCallback(async () => {
    if (!presetName.trim()) return;
    const filters = getCurrentFilters();
    const result = await savePreset(presetName.trim(), filters);
    if (result) {
      setPresetName("");
      setSaveMode(false);
    }
  }, [presetName, getCurrentFilters, savePreset]);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => { setOpen(o => !o); setSaveMode(false); }}
        className="flex items-center gap-1.5 text-sm font-medium text-ink-secondary hover:text-brand-blue transition-colors px-2 py-1.5 rounded-button hover:bg-surface-1"
        aria-expanded={open}
        aria-haspopup="listbox"
        title="Presets de filtros salvos"
      >
        <Bookmark className="w-4 h-4" strokeWidth={2} />
        <span className="hidden sm:inline">Presets</span>
        {presets.length > 0 && (
          <span className="bg-brand-blue text-white text-xs rounded-full w-4 h-4 flex items-center justify-center leading-none">
            {presets.length}
          </span>
        )}
        <ChevronDown className={`w-3 h-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Presets de filtros"
          className="absolute left-0 top-full mt-1 w-72 bg-surface-0 border border-strong rounded-card shadow-elevated z-50 animate-fade-in-up"
        >
          <div className="p-3 border-b border-strong flex items-center justify-between">
            <span className="text-sm font-semibold text-ink">Presets salvos</span>
            {canSaveMore && !saveMode && (
              <button
                type="button"
                onClick={() => setSaveMode(true)}
                className="flex items-center gap-1 text-xs font-medium text-brand-blue hover:underline"
              >
                <Plus className="w-3.5 h-3.5" />
                Salvar atual
              </button>
            )}
            {!canSaveMore && !saveMode && (
              <span className="text-xs text-ink-muted">{MAX_PRESETS}/{MAX_PRESETS}</span>
            )}
          </div>

          {saveMode && (
            <div className="p-3 border-b border-strong">
              <label htmlFor="preset-name" className="text-xs font-medium text-ink-secondary block mb-1.5">
                Nome do preset
              </label>
              <div className="flex gap-2">
                <input
                  id="preset-name"
                  ref={inputRef}
                  type="text"
                  value={presetName}
                  onChange={e => setPresetName(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter") handleSave(); if (e.key === "Escape") { setSaveMode(false); setPresetName(""); } }}
                  maxLength={60}
                  placeholder="Ex: SP + TI abertas"
                  className="flex-1 text-sm border border-strong rounded-input px-2 py-1.5 bg-surface-0 focus:ring-2 focus:ring-brand-blue focus:outline-none"
                />
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={!presetName.trim() || saving}
                  className="px-3 py-1.5 text-xs font-medium bg-brand-blue text-white rounded-button disabled:opacity-50 hover:bg-brand-blue/90 transition-colors flex items-center gap-1"
                >
                  {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Salvar"}
                </button>
              </div>
            </div>
          )}

          <div className="max-h-56 overflow-y-auto">
            {loading && (
              <div className="flex items-center justify-center p-4">
                <Loader2 className="w-4 h-4 animate-spin text-brand-blue" />
              </div>
            )}

            {!loading && presets.length === 0 && (
              <div className="p-4 text-center">
                <p className="text-sm text-ink-muted">Nenhum preset salvo.</p>
                <p className="text-xs text-ink-muted mt-1">Configure filtros e clique em &quot;Salvar atual&quot;.</p>
              </div>
            )}

            {!loading && presets.map(preset => (
              <div
                key={preset.id}
                className="flex items-center gap-2 px-3 py-2.5 hover:bg-surface-1 transition-colors group"
              >
                <button
                  type="button"
                  onClick={() => handleApply(preset)}
                  className="flex-1 text-left text-sm text-ink truncate hover:text-brand-blue transition-colors"
                  title={preset.name}
                >
                  {preset.name}
                </button>
                <button
                  type="button"
                  onClick={() => deletePreset(preset.id)}
                  className="opacity-0 group-hover:opacity-100 text-ink-muted hover:text-error transition-all p-1 rounded"
                  aria-label={`Remover preset "${preset.name}"`}
                >
                  <Trash2 className="w-3.5 h-3.5" strokeWidth={2} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
