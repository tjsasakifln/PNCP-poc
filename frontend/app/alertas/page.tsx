"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import { PageHeader } from "../../components/PageHeader";
import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";
import { ErrorStateWithRetry } from "../../components/ErrorStateWithRetry";
import { toast } from "sonner";
import { SECTOR_DISPLAY_NAMES } from "../../lib/constants/sector-names";
import { UFS, UF_NAMES } from "../../lib/constants/uf-names";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AlertFilters {
  setor: string;
  ufs: string[];
  valor_min: number | null;
  valor_max: number | null;
  keywords: string[];
}

interface Alert {
  id: string;
  name: string;
  filters: AlertFilters;
  active: boolean;
  created_at: string;
  updated_at: string;
}

interface AlertFormData {
  name: string;
  setor: string;
  ufs: string[];
  valor_min: string;
  valor_max: string;
  keywords: string[];
}

const EMPTY_FORM: AlertFormData = {
  name: "",
  setor: "",
  ufs: [],
  valor_min: "",
  valor_max: "",
  keywords: [],
};

// ---------------------------------------------------------------------------
// Sector options derived from canonical constants
// ---------------------------------------------------------------------------
const SECTOR_OPTIONS = Object.entries(SECTOR_DISPLAY_NAMES).map(
  ([slug, label]) => ({ value: slug, label }),
);

// ---------------------------------------------------------------------------
// UF Region groups for quick-select buttons
// ---------------------------------------------------------------------------
const UF_REGIONS: Record<string, string[]> = {
  Norte: ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
  Nordeste: ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
  "Centro-Oeste": ["DF", "GO", "MT", "MS"],
  Sudeste: ["ES", "MG", "RJ", "SP"],
  Sul: ["PR", "RS", "SC"],
};

// ---------------------------------------------------------------------------
// Helper: Format currency for display
// ---------------------------------------------------------------------------
function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) return "-";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function AlertCard({
  alert,
  onToggle,
  onEdit,
  onDelete,
}: {
  alert: Alert;
  onToggle: (id: string, active: boolean) => void;
  onEdit: (alert: Alert) => void;
  onDelete: (id: string) => void;
}) {
  const [toggling, setToggling] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleToggle = async () => {
    setToggling(true);
    await onToggle(alert.id, !alert.active);
    setToggling(false);
  };

  const handleDelete = async () => {
    setDeleting(true);
    await onDelete(alert.id);
    setDeleting(false);
    setShowConfirm(false);
  };

  const filterSummary: string[] = [];
  if (alert.filters.setor) {
    filterSummary.push(
      SECTOR_DISPLAY_NAMES[alert.filters.setor] || alert.filters.setor,
    );
  }
  if (alert.filters.ufs && alert.filters.ufs.length > 0) {
    if (alert.filters.ufs.length <= 3) {
      filterSummary.push(alert.filters.ufs.join(", "));
    } else {
      filterSummary.push(`${alert.filters.ufs.length} UFs`);
    }
  }
  if (alert.filters.valor_min !== null || alert.filters.valor_max !== null) {
    const parts: string[] = [];
    if (alert.filters.valor_min !== null) parts.push(`Min ${formatCurrency(alert.filters.valor_min)}`);
    if (alert.filters.valor_max !== null) parts.push(`Max ${formatCurrency(alert.filters.valor_max)}`);
    filterSummary.push(parts.join(" - "));
  }
  if (alert.filters.keywords && alert.filters.keywords.length > 0) {
    filterSummary.push(
      alert.filters.keywords.length === 1
        ? `"${alert.filters.keywords[0]}"`
        : `${alert.filters.keywords.length} palavras-chave`,
    );
  }

  return (
    <div
      className={`rounded-xl border transition-colors ${
        alert.active
          ? "border-[var(--brand-blue)]/30 bg-[var(--surface-0)]"
          : "border-[var(--border)] bg-[var(--surface-0)] opacity-70"
      }`}
      data-testid={`alert-card-${alert.id}`}
    >
      <div className="p-4 sm:p-5">
        {/* Header row: name + toggle */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-[var(--ink)] truncate">
              {alert.name}
            </h3>
            <p className="text-xs text-[var(--ink-muted)] mt-0.5">
              Criado em{" "}
              {new Date(alert.created_at).toLocaleDateString("pt-BR")}
            </p>
          </div>

          {/* Active toggle */}
          <button
            onClick={handleToggle}
            disabled={toggling}
            className="relative flex-shrink-0"
            aria-label={alert.active ? "Desativar alerta" : "Ativar alerta"}
            data-testid={`alert-toggle-${alert.id}`}
          >
            <div
              className={`w-11 h-6 rounded-full transition-colors ${
                alert.active
                  ? "bg-[var(--brand-blue)]"
                  : "bg-[var(--ink-faint)]"
              } ${toggling ? "opacity-50" : ""}`}
            >
              <div
                className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                  alert.active ? "translate-x-[22px]" : "translate-x-0.5"
                }`}
              />
            </div>
          </button>
        </div>

        {/* Filters summary chips */}
        {filterSummary.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {filterSummary.map((chip, i) => (
              <span
                key={i}
                className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-[var(--surface-1)] text-[var(--ink-secondary)]"
              >
                {chip}
              </span>
            ))}
          </div>
        )}

        {/* Keywords display */}
        {alert.filters.keywords && alert.filters.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {alert.filters.keywords.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)]"
              >
                {kw}
              </span>
            ))}
          </div>
        )}

        {/* Actions row */}
        <div className="flex items-center gap-2 pt-2 border-t border-[var(--border)]">
          <button
            onClick={() => onEdit(alert)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--ink-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--ink)] transition-colors"
            data-testid={`alert-edit-${alert.id}`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
            </svg>
            Editar
          </button>

          {showConfirm ? (
            <div className="flex items-center gap-1.5 ml-auto">
              <span className="text-xs text-[var(--error)]">Excluir?</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-2 py-1 rounded text-xs font-medium bg-[var(--error)] text-white hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {deleting ? "..." : "Sim"}
              </button>
              <button
                onClick={() => setShowConfirm(false)}
                className="px-2 py-1 rounded text-xs font-medium text-[var(--ink-secondary)] hover:bg-[var(--surface-1)] transition-colors"
              >
                Nao
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowConfirm(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--error)]/70 hover:text-[var(--error)] hover:bg-[var(--error-subtle)] transition-colors ml-auto"
              data-testid={`alert-delete-${alert.id}`}
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>
              Excluir
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Keywords tag input
// ---------------------------------------------------------------------------
function KeywordsInput({
  keywords,
  onChange,
}: {
  keywords: string[];
  onChange: (kws: string[]) => void;
}) {
  const [input, setInput] = useState("");

  const addKeyword = () => {
    const trimmed = input.trim();
    if (trimmed && !keywords.includes(trimmed)) {
      onChange([...keywords, trimmed]);
    }
    setInput("");
  };

  const removeKeyword = (kw: string) => {
    onChange(keywords.filter((k) => k !== kw));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addKeyword();
    }
    if (e.key === "Backspace" && input === "" && keywords.length > 0) {
      removeKeyword(keywords[keywords.length - 1]);
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-[var(--ink)] mb-1.5">
        Palavras-chave
      </label>
      <div className="flex flex-wrap gap-1.5 p-2 min-h-[42px] rounded-lg border border-[var(--border)] bg-[var(--surface-0)] focus-within:border-[var(--brand-blue)] focus-within:ring-1 focus-within:ring-[var(--brand-blue)]/20 transition-colors">
        {keywords.map((kw) => (
          <span
            key={kw}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)]"
          >
            {kw}
            <button
              type="button"
              onClick={() => removeKeyword(kw)}
              className="ml-0.5 hover:text-[var(--error)] transition-colors"
              aria-label={`Remover "${kw}"`}
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </span>
        ))}
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={addKeyword}
          placeholder={keywords.length === 0 ? "Digite e pressione Enter..." : ""}
          className="flex-1 min-w-[120px] border-none outline-none bg-transparent text-sm text-[var(--ink)] placeholder:text-[var(--ink-muted)]"
        />
      </div>
      <p className="text-[11px] text-[var(--ink-muted)] mt-1">
        Pressione Enter ou virgula para adicionar. Backspace remove a ultima.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// UF Multi-select with region quick-buttons
// ---------------------------------------------------------------------------
function UFMultiSelect({
  selected,
  onChange,
}: {
  selected: string[];
  onChange: (ufs: string[]) => void;
}) {
  const selectedSet = new Set(selected);

  const toggleUf = (uf: string) => {
    const newSet = new Set(selectedSet);
    if (newSet.has(uf)) newSet.delete(uf);
    else newSet.add(uf);
    onChange(Array.from(newSet));
  };

  const toggleRegion = (regionUfs: string[]) => {
    const allSelected = regionUfs.every((uf) => selectedSet.has(uf));
    const newSet = new Set(selectedSet);
    if (allSelected) {
      regionUfs.forEach((uf) => newSet.delete(uf));
    } else {
      regionUfs.forEach((uf) => newSet.add(uf));
    }
    onChange(Array.from(newSet));
  };

  const selectAll = () => onChange([...UFS]);
  const clearAll = () => onChange([]);

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="block text-sm font-medium text-[var(--ink)]">
          Estados (UFs)
        </label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={selectAll}
            className="text-[11px] text-[var(--brand-blue)] hover:underline"
          >
            Todos
          </button>
          <button
            type="button"
            onClick={clearAll}
            className="text-[11px] text-[var(--ink-muted)] hover:underline"
          >
            Limpar
          </button>
        </div>
      </div>

      {/* Region quick-buttons */}
      <div className="flex flex-wrap gap-1.5 mb-2">
        {Object.entries(UF_REGIONS).map(([region, ufs]) => {
          const allSelected = ufs.every((uf) => selectedSet.has(uf));
          return (
            <button
              key={region}
              type="button"
              onClick={() => toggleRegion(ufs)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium border transition-colors ${
                allSelected
                  ? "bg-[var(--brand-blue)] text-white border-[var(--brand-blue)]"
                  : "bg-[var(--surface-0)] text-[var(--ink-secondary)] border-[var(--border)] hover:border-[var(--brand-blue)]"
              }`}
            >
              {region}
            </button>
          );
        })}
      </div>

      {/* UF grid */}
      <div className="grid grid-cols-5 sm:grid-cols-7 md:grid-cols-9 gap-1">
        {UFS.map((uf) => (
          <label
            key={uf}
            className={`flex items-center justify-center px-1 py-1.5 rounded cursor-pointer text-xs font-medium transition-colors select-none ${
              selectedSet.has(uf)
                ? "bg-[var(--brand-blue)] text-white"
                : "bg-[var(--surface-1)] text-[var(--ink-secondary)] hover:bg-[var(--surface-2,var(--surface-1))] hover:text-[var(--ink)]"
            }`}
            title={UF_NAMES[uf]}
          >
            <input
              type="checkbox"
              checked={selectedSet.has(uf)}
              onChange={() => toggleUf(uf)}
              className="sr-only"
            />
            {uf}
          </label>
        ))}
      </div>
      {selected.length > 0 && (
        <p className="text-[11px] text-[var(--ink-muted)] mt-1">
          {selected.length} {selected.length === 1 ? "estado selecionado" : "estados selecionados"}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Alert Form Modal
// ---------------------------------------------------------------------------
function AlertFormModal({
  editingAlert,
  onSave,
  onClose,
  saving,
}: {
  editingAlert: Alert | null;
  onSave: (data: AlertFormData) => Promise<void>;
  onClose: () => void;
  saving: boolean;
}) {
  const [form, setForm] = useState<AlertFormData>(() => {
    if (editingAlert) {
      return {
        name: editingAlert.name,
        setor: editingAlert.filters.setor || "",
        ufs: editingAlert.filters.ufs || [],
        valor_min:
          editingAlert.filters.valor_min !== null
            ? String(editingAlert.filters.valor_min)
            : "",
        valor_max:
          editingAlert.filters.valor_max !== null
            ? String(editingAlert.filters.valor_max)
            : "",
        keywords: editingAlert.filters.keywords || [],
      };
    }
    return { ...EMPTY_FORM };
  });

  const [showPreview, setShowPreview] = useState(false);

  const isValid = form.name.trim().length >= 3;

  const hasFilters =
    form.setor !== "" ||
    form.ufs.length > 0 ||
    form.valor_min !== "" ||
    form.valor_max !== "" ||
    form.keywords.length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    await onSave(form);
  };

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[5vh] sm:pt-[10vh]"
      role="dialog"
      aria-modal="true"
      aria-label={editingAlert ? "Editar alerta" : "Criar novo alerta"}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal panel */}
      <div className="relative w-full max-w-xl mx-4 max-h-[85vh] overflow-y-auto rounded-2xl bg-[var(--surface-0)] border border-[var(--border)] shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 border-b border-[var(--border)] bg-[var(--surface-0)] rounded-t-2xl">
          <h2 className="text-lg font-semibold text-[var(--ink)]">
            {editingAlert ? "Editar Alerta" : "Criar Novo Alerta"}
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[var(--ink-muted)] hover:bg-[var(--surface-1)] hover:text-[var(--ink)] transition-colors"
            aria-label="Fechar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {/* Alert name */}
          <div>
            <label
              htmlFor="alert-name"
              className="block text-sm font-medium text-[var(--ink)] mb-1.5"
            >
              Nome do alerta <span className="text-[var(--error)]">*</span>
            </label>
            <input
              id="alert-name"
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder='Ex.: "Uniformes SP e RJ"'
              maxLength={100}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)] placeholder:text-[var(--ink-muted)] focus:border-[var(--brand-blue)] focus:ring-1 focus:ring-[var(--brand-blue)]/20 outline-none transition-colors"
              autoFocus
            />
            {form.name.length > 0 && form.name.trim().length < 3 && (
              <p className="text-[11px] text-[var(--error)] mt-1">
                Nome deve ter pelo menos 3 caracteres
              </p>
            )}
          </div>

          {/* Sector dropdown */}
          <div>
            <label
              htmlFor="alert-setor"
              className="block text-sm font-medium text-[var(--ink)] mb-1.5"
            >
              Setor
            </label>
            <select
              id="alert-setor"
              value={form.setor}
              onChange={(e) => setForm((f) => ({ ...f, setor: e.target.value }))}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)] focus:border-[var(--brand-blue)] focus:ring-1 focus:ring-[var(--brand-blue)]/20 outline-none transition-colors"
            >
              <option value="">Todos os setores</option>
              {SECTOR_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* UFs multi-select */}
          <UFMultiSelect
            selected={form.ufs}
            onChange={(ufs) => setForm((f) => ({ ...f, ufs }))}
          />

          {/* Value range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label
                htmlFor="alert-valor-min"
                className="block text-sm font-medium text-[var(--ink)] mb-1.5"
              >
                Valor minimo (R$)
              </label>
              <input
                id="alert-valor-min"
                type="number"
                min={0}
                step={1000}
                value={form.valor_min}
                onChange={(e) =>
                  setForm((f) => ({ ...f, valor_min: e.target.value }))
                }
                placeholder="0"
                className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)] placeholder:text-[var(--ink-muted)] focus:border-[var(--brand-blue)] focus:ring-1 focus:ring-[var(--brand-blue)]/20 outline-none transition-colors"
              />
            </div>
            <div>
              <label
                htmlFor="alert-valor-max"
                className="block text-sm font-medium text-[var(--ink)] mb-1.5"
              >
                Valor maximo (R$)
              </label>
              <input
                id="alert-valor-max"
                type="number"
                min={0}
                step={1000}
                value={form.valor_max}
                onChange={(e) =>
                  setForm((f) => ({ ...f, valor_max: e.target.value }))
                }
                placeholder="Sem limite"
                className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)] placeholder:text-[var(--ink-muted)] focus:border-[var(--brand-blue)] focus:ring-1 focus:ring-[var(--brand-blue)]/20 outline-none transition-colors"
              />
            </div>
          </div>

          {/* Keywords */}
          <KeywordsInput
            keywords={form.keywords}
            onChange={(kws) =>
              setForm((f) => ({ ...f, keywords: kws }))
            }
          />

          {/* Preview toggle (AC12) */}
          {hasFilters && (
            <div>
              <button
                type="button"
                onClick={() => setShowPreview(!showPreview)}
                className="flex items-center gap-1.5 text-sm text-[var(--brand-blue)] hover:underline"
              >
                <svg
                  className={`w-4 h-4 transition-transform ${showPreview ? "rotate-90" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                </svg>
                {showPreview ? "Ocultar preview" : "Preview do alerta"}
              </button>

              {showPreview && (
                <div className="mt-3 p-4 rounded-lg bg-[var(--surface-1)] border border-[var(--border)]">
                  <h4 className="text-sm font-semibold text-[var(--ink)] mb-2">
                    Preview: {form.name || "Sem nome"}
                  </h4>
                  <dl className="space-y-1.5 text-xs">
                    {form.setor && (
                      <div className="flex gap-2">
                        <dt className="font-medium text-[var(--ink-secondary)] min-w-[80px]">Setor:</dt>
                        <dd className="text-[var(--ink)]">
                          {SECTOR_DISPLAY_NAMES[form.setor] || form.setor}
                        </dd>
                      </div>
                    )}
                    {form.ufs.length > 0 && (
                      <div className="flex gap-2">
                        <dt className="font-medium text-[var(--ink-secondary)] min-w-[80px]">UFs:</dt>
                        <dd className="text-[var(--ink)]">
                          {form.ufs.length === UFS.length
                            ? "Todos os estados"
                            : form.ufs.join(", ")}
                        </dd>
                      </div>
                    )}
                    {(form.valor_min || form.valor_max) && (
                      <div className="flex gap-2">
                        <dt className="font-medium text-[var(--ink-secondary)] min-w-[80px]">Valor:</dt>
                        <dd className="text-[var(--ink)]">
                          {form.valor_min
                            ? formatCurrency(Number(form.valor_min))
                            : "Sem min."}{" "}
                          a{" "}
                          {form.valor_max
                            ? formatCurrency(Number(form.valor_max))
                            : "Sem max."}
                        </dd>
                      </div>
                    )}
                    {form.keywords.length > 0 && (
                      <div className="flex gap-2">
                        <dt className="font-medium text-[var(--ink-secondary)] min-w-[80px]">Keywords:</dt>
                        <dd className="text-[var(--ink)]">
                          {form.keywords.map((kw) => `"${kw}"`).join(", ")}
                        </dd>
                      </div>
                    )}
                  </dl>
                </div>
              )}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[var(--border)]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--ink-secondary)] hover:bg-[var(--surface-1)] transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!isValid || saving}
              className="px-5 py-2 rounded-lg text-sm font-medium bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              data-testid="alert-save-button"
            >
              {saving && (
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
              {editingAlert ? "Salvar alteracoes" : "Criar alerta"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty State
// ---------------------------------------------------------------------------
function AlertsEmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="text-center py-16 px-4" data-testid="alerts-empty-state">
      <div className="mx-auto mb-6 w-16 h-16 flex items-center justify-center rounded-full bg-[var(--brand-blue-subtle)]">
        <svg
          aria-hidden="true"
          className="w-8 h-8 text-[var(--brand-blue)]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
        </svg>
      </div>
      <h2 className="text-xl font-display font-semibold text-[var(--ink)] mb-3">
        Nenhum alerta configurado
      </h2>
      <p className="text-[var(--ink-secondary)] mb-6 max-w-md mx-auto">
        Crie alertas para receber notificacoes por e-mail quando novas
        licitacoes forem publicadas nos setores e estados que voce acompanha.
      </p>
      <ol className="text-left max-w-sm mx-auto mb-8 space-y-3">
        {[
          "Defina um nome para o alerta",
          "Escolha setor, estados e palavras-chave",
          "Receba e-mails automaticos com novas oportunidades",
        ].map((step, i) => (
          <li key={i} className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[var(--brand-blue)] text-white text-xs font-bold flex items-center justify-center mt-0.5">
              {i + 1}
            </span>
            <span className="text-sm text-[var(--ink-secondary)]">{step}</span>
          </li>
        ))}
      </ol>
      <button
        onClick={onCreate}
        className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] transition-colors font-medium"
        data-testid="alerts-create-first"
      >
        Criar primeiro alerta
        <svg aria-hidden="true" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------
export default function AlertasPage() {
  const { session, loading: authLoading } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingAlert, setEditingAlert] = useState<Alert | null>(null);
  const [saving, setSaving] = useState(false);

  // Fetch all alerts
  const fetchAlerts = useCallback(async () => {
    if (!session?.access_token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/alerts", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.message || `Erro ${res.status}`);
      }
      const data = await res.json();
      // Backend may return { alerts: [...] } or just [...]
      const list = Array.isArray(data) ? data : data.alerts || [];
      setAlerts(list);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao carregar alertas";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (session?.access_token) {
      fetchAlerts();
    }
  }, [session?.access_token, fetchAlerts]);

  // Create or update alert
  const handleSave = async (formData: AlertFormData) => {
    if (!session?.access_token) return;
    setSaving(true);
    try {
      const payload = {
        name: formData.name.trim(),
        filters: {
          setor: formData.setor || null,
          ufs: formData.ufs.length > 0 ? formData.ufs : null,
          valor_min: formData.valor_min ? Number(formData.valor_min) : null,
          valor_max: formData.valor_max ? Number(formData.valor_max) : null,
          keywords:
            formData.keywords.length > 0 ? formData.keywords : null,
        },
      };

      let res: Response;
      if (editingAlert) {
        res = await fetch(`/api/alerts/${editingAlert.id}`, {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
      } else {
        res = await fetch("/api/alerts", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.message || `Erro ${res.status}`);
      }

      toast.success(
        editingAlert ? "Alerta atualizado com sucesso" : "Alerta criado com sucesso",
      );
      setShowForm(false);
      setEditingAlert(null);
      await fetchAlerts();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao salvar alerta";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  // Toggle active/inactive (AC14)
  const handleToggle = async (id: string, active: boolean) => {
    if (!session?.access_token) return;
    // Optimistic update
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, active: active } : a)),
    );
    try {
      const res = await fetch(`/api/alerts/${id}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ active: active }),
      });
      if (!res.ok) {
        throw new Error("Falha ao atualizar status");
      }
      toast.success(active ? "Alerta ativado" : "Alerta desativado");
    } catch {
      // Revert optimistic update
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, active: !active } : a)),
      );
      toast.error("Erro ao atualizar status do alerta");
    }
  };

  // Delete alert
  const handleDelete = async (id: string) => {
    if (!session?.access_token) return;
    try {
      const res = await fetch(`/api/alerts/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok && res.status !== 204) {
        throw new Error("Falha ao excluir");
      }
      setAlerts((prev) => prev.filter((a) => a.id !== id));
      toast.success("Alerta excluido com sucesso");
    } catch {
      toast.error("Erro ao excluir alerta");
    }
  };

  // Edit alert
  const handleEdit = (alert: Alert) => {
    setEditingAlert(alert);
    setShowForm(true);
  };

  // Close modal
  const handleCloseForm = () => {
    setShowForm(false);
    setEditingAlert(null);
  };

  // Auth loading gate
  if (authLoading) {
    return <AuthLoadingScreen />;
  }

  if (!session?.access_token) {
    return (
      <>
        <PageHeader title="Alertas" />
        <div className="max-w-7xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold mb-4">Alertas por E-mail</h1>
          <p className="text-[var(--text-secondary)]">
            Faca login para gerenciar seus alertas.
          </p>
        </div>
      </>
    );
  }

  const activeCount = alerts.filter((a) => a.active).length;

  return (
    <>
      <PageHeader title="Alertas" />
      <main className="max-w-3xl mx-auto px-4 py-6">
        {/* Page heading */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">
              Alertas por E-mail
            </h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Receba notificacoes automaticas sobre novas licitacoes.
            </p>
          </div>
          {alerts.length > 0 && (
            <button
              onClick={() => {
                setEditingAlert(null);
                setShowForm(true);
              }}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] transition-colors"
              data-testid="alerts-create-button"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              <span className="hidden sm:inline">Criar alerta</span>
            </button>
          )}
        </div>

        {/* Stats bar */}
        {alerts.length > 0 && (
          <div className="flex items-center gap-4 mb-5 text-sm text-[var(--ink-secondary)]">
            <span>
              {alerts.length} {alerts.length === 1 ? "alerta" : "alertas"}
            </span>
            <span className="w-px h-4 bg-[var(--border)]" />
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              {activeCount} {activeCount === 1 ? "ativo" : "ativos"}
            </span>
          </div>
        )}

        {/* Content: loading / error / empty / list */}
        {loading ? (
          <div className="space-y-4" data-testid="alerts-skeleton">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-32 rounded-xl bg-[var(--surface-1)] animate-pulse"
                style={{ animationDelay: `${i * 100}ms` }}
              />
            ))}
          </div>
        ) : error ? (
          <ErrorStateWithRetry
            message={error}
            onRetry={fetchAlerts}
          />
        ) : alerts.length === 0 ? (
          <AlertsEmptyState
            onCreate={() => {
              setEditingAlert(null);
              setShowForm(true);
            }}
          />
        ) : (
          <div className="space-y-3" data-testid="alerts-list">
            {alerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onToggle={handleToggle}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </main>

      {/* Form modal */}
      {showForm && (
        <AlertFormModal
          editingAlert={editingAlert}
          onSave={handleSave}
          onClose={handleCloseForm}
          saving={saving}
        />
      )}
    </>
  );
}
