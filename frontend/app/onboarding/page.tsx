"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../components/AuthProvider";
import { UF_NAMES, UFS } from "../../lib/constants/uf-names";
import { toast } from "sonner";

// ============================================================================
// Constants
// ============================================================================

const PORTE_OPTIONS = [
  { value: "ME", label: "Microempresa (ME)", desc: "Faturamento até R$ 360 mil/ano" },
  { value: "EPP", label: "Empresa de Pequeno Porte (EPP)", desc: "Faturamento até R$ 4,8 mi/ano" },
  { value: "MEDIO", label: "Médio Porte", desc: "Faturamento acima de R$ 4,8 mi/ano" },
  { value: "GRANDE", label: "Grande Porte", desc: "Grandes corporações" },
] as const;

const EXPERIENCIA_OPTIONS = [
  { value: "PRIMEIRA_VEZ", label: "Primeira vez", desc: "Nunca participei de licitações" },
  { value: "INICIANTE", label: "Iniciante", desc: "Participei de 1-5 licitações" },
  { value: "EXPERIENTE", label: "Experiente", desc: "Participo regularmente" },
] as const;

const REGIONS: Record<string, string[]> = {
  Norte: ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
  Nordeste: ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
  "Centro-Oeste": ["DF", "GO", "MS", "MT"],
  Sudeste: ["ES", "MG", "RJ", "SP"],
  Sul: ["PR", "RS", "SC"],
};

// ============================================================================
// Types
// ============================================================================

interface OnboardingData {
  porte_empresa: string;
  ufs_atuacao: string[];
  experiencia_licitacoes: string;
  faixa_valor_min: number | null;
  faixa_valor_max: number | null;
  palavras_chave: string[];
}

// ============================================================================
// Progress Bar Component
// ============================================================================

function ProgressBar({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {Array.from({ length: totalSteps }, (_, i) => (
        <div key={i} className="flex-1 flex items-center gap-2">
          <div
            className={`h-2 rounded-full flex-1 transition-colors duration-300 ${
              i < currentStep
                ? "bg-[var(--brand-blue)]"
                : i === currentStep
                ? "bg-[var(--brand-blue)] opacity-60"
                : "bg-[var(--border)]"
            }`}
          />
        </div>
      ))}
      <span className="text-xs text-[var(--ink-secondary)] ml-2 whitespace-nowrap">
        {currentStep + 1} de {totalSteps}
      </span>
    </div>
  );
}

// ============================================================================
// Step 1: Sua Empresa
// ============================================================================

function StepOne({
  data,
  onChange,
}: {
  data: OnboardingData;
  onChange: (partial: Partial<OnboardingData>) => void;
}) {
  const toggleUf = (uf: string) => {
    const current = new Set(data.ufs_atuacao);
    if (current.has(uf)) current.delete(uf);
    else current.add(uf);
    onChange({ ufs_atuacao: Array.from(current) });
  };

  const toggleRegion = (regionUfs: string[]) => {
    const current = new Set(data.ufs_atuacao);
    const allSelected = regionUfs.every((uf) => current.has(uf));
    if (allSelected) regionUfs.forEach((uf) => current.delete(uf));
    else regionUfs.forEach((uf) => current.add(uf));
    onChange({ ufs_atuacao: Array.from(current) });
  };

  const selectAll = () => onChange({ ufs_atuacao: [...UFS] });
  const clearAll = () => onChange({ ufs_atuacao: [] });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--ink)] mb-1">Sua Empresa</h2>
        <p className="text-sm text-[var(--ink-secondary)]">
          Nos conte sobre sua empresa para personalizar seus resultados
        </p>
      </div>

      {/* Porte */}
      <div>
        <label className="block text-sm font-medium text-[var(--ink)] mb-2">Porte da empresa *</label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {PORTE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onChange({ porte_empresa: opt.value })}
              className={`p-3 rounded-lg border text-left transition-all ${
                data.porte_empresa === opt.value
                  ? "border-[var(--brand-blue)] bg-[var(--brand-blue)]/5 ring-1 ring-[var(--brand-blue)]"
                  : "border-[var(--border)] hover:border-[var(--ink-secondary)]"
              }`}
            >
              <div className="text-sm font-medium text-[var(--ink)]">{opt.label}</div>
              <div className="text-xs text-[var(--ink-secondary)]">{opt.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* UFs de atuação */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-[var(--ink)]">
            UFs de atuação * <span className="font-normal text-[var(--ink-secondary)]">({data.ufs_atuacao.length} selecionadas)</span>
          </label>
          <div className="flex gap-2">
            <button onClick={selectAll} className="text-xs text-[var(--brand-blue)] hover:underline">
              Todas
            </button>
            <button onClick={clearAll} className="text-xs text-[var(--ink-secondary)] hover:underline">
              Limpar
            </button>
          </div>
        </div>
        <div className="space-y-3">
          {Object.entries(REGIONS).map(([region, ufs]) => {
            const allSelected = ufs.every((uf) => data.ufs_atuacao.includes(uf));
            const someSelected = ufs.some((uf) => data.ufs_atuacao.includes(uf));
            return (
              <div key={region}>
                <button
                  onClick={() => toggleRegion(ufs)}
                  className={`text-xs font-medium mb-1 px-2 py-0.5 rounded transition-colors ${
                    allSelected
                      ? "text-[var(--brand-blue)] bg-[var(--brand-blue)]/10"
                      : someSelected
                      ? "text-[var(--ink)] bg-[var(--surface-1)]"
                      : "text-[var(--ink-secondary)]"
                  }`}
                >
                  {region}
                </button>
                <div className="flex flex-wrap gap-1">
                  {ufs.map((uf) => (
                    <button
                      key={uf}
                      onClick={() => toggleUf(uf)}
                      className={`px-2 py-1 text-xs rounded border transition-colors ${
                        data.ufs_atuacao.includes(uf)
                          ? "border-[var(--brand-blue)] bg-[var(--brand-blue)] text-white"
                          : "border-[var(--border)] text-[var(--ink-secondary)] hover:border-[var(--ink-secondary)]"
                      }`}
                      title={UF_NAMES[uf]}
                    >
                      {uf}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Experiência */}
      <div>
        <label className="block text-sm font-medium text-[var(--ink)] mb-2">Experiência com licitações *</label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {EXPERIENCIA_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onChange({ experiencia_licitacoes: opt.value })}
              className={`p-3 rounded-lg border text-left transition-all ${
                data.experiencia_licitacoes === opt.value
                  ? "border-[var(--brand-blue)] bg-[var(--brand-blue)]/5 ring-1 ring-[var(--brand-blue)]"
                  : "border-[var(--border)] hover:border-[var(--ink-secondary)]"
              }`}
            >
              <div className="text-sm font-medium text-[var(--ink)]">{opt.label}</div>
              <div className="text-xs text-[var(--ink-secondary)]">{opt.desc}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Step 2: Seu Interesse
// ============================================================================

function StepTwo({
  data,
  onChange,
  userSector,
}: {
  data: OnboardingData;
  onChange: (partial: Partial<OnboardingData>) => void;
  userSector?: string;
}) {
  const [keywordInput, setKeywordInput] = useState("");

  const addKeyword = () => {
    const kw = keywordInput.trim();
    if (kw && !data.palavras_chave.includes(kw)) {
      onChange({ palavras_chave: [...data.palavras_chave, kw] });
    }
    setKeywordInput("");
  };

  const removeKeyword = (kw: string) => {
    onChange({ palavras_chave: data.palavras_chave.filter((k) => k !== kw) });
  };

  const formatCurrency = (val: number | null) => {
    if (val === null) return "";
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(val);
  };

  // Slider range presets
  const VALUE_PRESETS = [0, 50_000, 100_000, 500_000, 1_000_000, 5_000_000, 10_000_000, 50_000_000];

  const findClosestPreset = (val: number | null): number => {
    if (val === null) return 0;
    return VALUE_PRESETS.reduce((prev, curr) =>
      Math.abs(curr - val) < Math.abs(prev - val) ? curr : prev
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--ink)] mb-1">Seu Interesse</h2>
        <p className="text-sm text-[var(--ink-secondary)]">
          Configure suas preferências de busca para resultados mais relevantes
        </p>
      </div>

      {/* Setor (display only, from signup) */}
      {userSector && (
        <div>
          <label className="block text-sm font-medium text-[var(--ink)] mb-1">Setor principal</label>
          <div className="px-3 py-2 rounded-lg bg-[var(--surface-1)] border border-[var(--border)] text-sm text-[var(--ink)]">
            {userSector}
          </div>
          <p className="text-xs text-[var(--ink-secondary)] mt-1">Definido no cadastro</p>
        </div>
      )}

      {/* Value range */}
      <div>
        <label className="block text-sm font-medium text-[var(--ink)] mb-2">Faixa de valor dos contratos</label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-[var(--ink-secondary)] mb-1">Valor mínimo</label>
            <select
              value={findClosestPreset(data.faixa_valor_min)}
              onChange={(e) => {
                const v = parseInt(e.target.value);
                onChange({ faixa_valor_min: v === 0 ? null : v });
              }}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)]"
            >
              <option value={0}>Sem limite</option>
              {VALUE_PRESETS.slice(1).map((v) => (
                <option key={v} value={v}>{formatCurrency(v)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-[var(--ink-secondary)] mb-1">Valor máximo</label>
            <select
              value={findClosestPreset(data.faixa_valor_max)}
              onChange={(e) => {
                const v = parseInt(e.target.value);
                onChange({ faixa_valor_max: v === 0 ? null : v });
              }}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)]"
            >
              <option value={0}>Sem limite</option>
              {VALUE_PRESETS.slice(1).map((v) => (
                <option key={v} value={v}>{formatCurrency(v)}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Keywords */}
      <div>
        <label className="block text-sm font-medium text-[var(--ink)] mb-2">
          Palavras-chave do seu nicho <span className="font-normal text-[var(--ink-secondary)]">(opcional, máx. 20)</span>
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addKeyword(); } }}
            placeholder="Ex: jaleco, fardamento, EPI..."
            className="flex-1 px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)] placeholder:text-[var(--ink-secondary)]"
            maxLength={50}
          />
          <button
            onClick={addKeyword}
            disabled={!keywordInput.trim() || data.palavras_chave.length >= 20}
            className="px-4 py-2 rounded-lg bg-[var(--brand-blue)] text-white text-sm font-medium disabled:opacity-40 hover:bg-[var(--brand-blue-hover)] transition-colors"
          >
            Adicionar
          </button>
        </div>
        {data.palavras_chave.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {data.palavras_chave.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-[var(--brand-blue)]/10 text-[var(--brand-blue)] text-xs"
              >
                {kw}
                <button onClick={() => removeKeyword(kw)} className="hover:text-[var(--error)]" aria-label={`Remover ${kw}`}>
                  &times;
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Step 3: Resumo + CTA
// ============================================================================

function StepThree({
  data,
  saving,
}: {
  data: OnboardingData;
  saving: boolean;
}) {
  const porteLabel = PORTE_OPTIONS.find((o) => o.value === data.porte_empresa)?.label || data.porte_empresa;
  const expLabel = EXPERIENCIA_OPTIONS.find((o) => o.value === data.experiencia_licitacoes)?.label || data.experiencia_licitacoes;

  const formatCurrency = (val: number | null) => {
    if (val === null) return "Sem limite";
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(val);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--ink)] mb-1">Tudo pronto!</h2>
        <p className="text-sm text-[var(--ink-secondary)]">
          Confira seu perfil de licitações. Você pode alterar a qualquer momento.
        </p>
      </div>

      <div className="space-y-4 p-4 rounded-lg bg-[var(--surface-1)] border border-[var(--border)]">
        <div>
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Porte</div>
          <div className="text-sm font-medium text-[var(--ink)]">{porteLabel}</div>
        </div>
        <div>
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">UFs de atuação</div>
          <div className="flex flex-wrap gap-1 mt-1">
            {data.ufs_atuacao.length === 27 ? (
              <span className="text-sm text-[var(--ink)]">Todas as UFs</span>
            ) : (
              data.ufs_atuacao.map((uf) => (
                <span key={uf} className="px-1.5 py-0.5 text-xs rounded bg-[var(--brand-blue)]/10 text-[var(--brand-blue)]">
                  {uf}
                </span>
              ))
            )}
          </div>
        </div>
        <div>
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Experiência</div>
          <div className="text-sm font-medium text-[var(--ink)]">{expLabel}</div>
        </div>
        <div>
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Faixa de valor</div>
          <div className="text-sm text-[var(--ink)]">
            {formatCurrency(data.faixa_valor_min)} — {formatCurrency(data.faixa_valor_max)}
          </div>
        </div>
        {data.palavras_chave.length > 0 && (
          <div>
            <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Palavras-chave</div>
            <div className="flex flex-wrap gap-1 mt-1">
              {data.palavras_chave.map((kw) => (
                <span key={kw} className="px-2 py-0.5 text-xs rounded-full bg-[var(--brand-blue)]/10 text-[var(--brand-blue)]">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {saving && (
        <div className="flex items-center gap-2 text-sm text-[var(--ink-secondary)]">
          <div className="w-4 h-4 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
          Salvando seu perfil...
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Onboarding Page
// ============================================================================

export default function OnboardingPage() {
  const router = useRouter();
  const { user, session, loading: authLoading } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [existingContext, setExistingContext] = useState<Record<string, unknown> | null>(null);

  const [data, setData] = useState<OnboardingData>({
    porte_empresa: "",
    ufs_atuacao: [],
    experiencia_licitacoes: "",
    faixa_valor_min: null,
    faixa_valor_max: null,
    palavras_chave: [],
  });

  const updateData = useCallback((partial: Partial<OnboardingData>) => {
    setData((prev) => ({ ...prev, ...partial }));
  }, []);

  // Load existing context if user re-visits
  useEffect(() => {
    if (!session?.access_token) return;

    fetch("/api/profile-context", {
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
      .then((r) => r.json())
      .then((res) => {
        if (res.context_data && Object.keys(res.context_data).length > 0) {
          setExistingContext(res.context_data);
          setData({
            porte_empresa: res.context_data.porte_empresa || "",
            ufs_atuacao: res.context_data.ufs_atuacao || [],
            experiencia_licitacoes: res.context_data.experiencia_licitacoes || "",
            faixa_valor_min: res.context_data.faixa_valor_min ?? null,
            faixa_valor_max: res.context_data.faixa_valor_max ?? null,
            palavras_chave: res.context_data.palavras_chave || [],
          });
        }
      })
      .catch(() => {});
  }, [session?.access_token]);

  // Validation per step
  const canProceed = (): boolean => {
    if (currentStep === 0) {
      return !!data.porte_empresa && data.ufs_atuacao.length > 0 && !!data.experiencia_licitacoes;
    }
    if (currentStep === 1) {
      // Value range validation
      if (data.faixa_valor_min !== null && data.faixa_valor_max !== null) {
        return data.faixa_valor_max >= data.faixa_valor_min;
      }
      return true; // Step 2 fields are all optional
    }
    return true;
  };

  const handleSave = async () => {
    if (!session?.access_token) return;
    setSaving(true);

    try {
      const payload: Record<string, unknown> = {
        ufs_atuacao: data.ufs_atuacao,
        porte_empresa: data.porte_empresa,
        experiencia_licitacoes: data.experiencia_licitacoes,
      };
      if (data.faixa_valor_min !== null) payload.faixa_valor_min = data.faixa_valor_min;
      if (data.faixa_valor_max !== null) payload.faixa_valor_max = data.faixa_valor_max;
      if (data.palavras_chave.length > 0) payload.palavras_chave = data.palavras_chave;

      const res = await fetch("/api/profile-context", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to save");

      // Cache context locally for useSearchFilters (STORY-247 AC12)
      localStorage.setItem("smartlic-profile-context", JSON.stringify(payload));
      // Mark onboarding as completed so redirect doesn't trigger again (AC11)
      localStorage.setItem("smartlic-onboarding-completed", "true");

      toast.success("Perfil salvo com sucesso!");
      // Build search URL with profile defaults
      const searchParams = new URLSearchParams();
      searchParams.set("ufs", data.ufs_atuacao.join(","));
      router.push(`/buscar?${searchParams.toString()}`);
    } catch {
      toast.error("Erro ao salvar perfil. Tente novamente.");
      setSaving(false);
    }
  };

  const handleSkip = () => {
    router.push("/buscar");
  };

  const nextStep = () => {
    if (currentStep < 2) setCurrentStep(currentStep + 1);
    else handleSave();
  };

  const prevStep = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  // Auth guard
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--surface-0)]">
        <div className="w-8 h-8 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user || !session) {
    router.replace("/login");
    return null;
  }

  const userSector = user.user_metadata?.sector;

  return (
    <div className="min-h-screen bg-[var(--surface-0)] flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-[var(--ink)]">
            {existingContext ? "Atualizar Perfil de Licitações" : "Configure seu Perfil de Licitações"}
          </h1>
          <p className="text-sm text-[var(--ink-secondary)] mt-1">
            Personalize sua experiência em menos de 2 minutos
          </p>
        </div>

        {/* Card */}
        <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-xl p-6 shadow-sm">
          <ProgressBar currentStep={currentStep} totalSteps={3} />

          {/* Steps */}
          {currentStep === 0 && <StepOne data={data} onChange={updateData} />}
          {currentStep === 1 && <StepTwo data={data} onChange={updateData} userSector={userSector} />}
          {currentStep === 2 && <StepThree data={data} saving={saving} />}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-4 border-t border-[var(--border)]">
            <div>
              {currentStep > 0 ? (
                <button
                  onClick={prevStep}
                  className="px-4 py-2 text-sm text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
                >
                  Voltar
                </button>
              ) : (
                <button
                  onClick={handleSkip}
                  className="px-4 py-2 text-sm text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
                >
                  Pular por agora
                </button>
              )}
            </div>
            <div className="flex items-center gap-3">
              {currentStep < 2 && (
                <button
                  onClick={handleSkip}
                  className="px-4 py-2 text-sm text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
                >
                  Pular por agora
                </button>
              )}
              <button
                onClick={nextStep}
                disabled={!canProceed() || saving}
                className="px-6 py-2.5 rounded-lg bg-[var(--brand-blue)] text-white text-sm font-medium
                           disabled:opacity-40 hover:bg-[var(--brand-blue-hover)] transition-colors"
              >
                {currentStep === 2 ? (saving ? "Salvando..." : "Ver minhas oportunidades") : "Próximo"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
