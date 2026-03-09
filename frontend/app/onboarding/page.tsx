"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "../components/AuthProvider";
import { UF_NAMES, UFS } from "../../lib/constants/uf-names";
import { toast } from "sonner";
import { safeSetItem } from "../../lib/storage";
import { Input } from "../../components/ui/Input";
import { Label } from "../../components/ui/Label";
import {
  onboardingStep1Schema,
  onboardingStep2Schema,
  type OnboardingStep1Data,
  type OnboardingStep2Data,
} from "../../lib/schemas/forms";

// ============================================================================
// Constants
// ============================================================================

const REGIONS: Record<string, string[]> = {
  Norte: ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
  Nordeste: ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
  "Centro-Oeste": ["DF", "GO", "MS", "MT"],
  Sudeste: ["ES", "MG", "RJ", "SP"],
  Sul: ["PR", "RS", "SC"],
};

// CNAE suggestions for autocomplete (AC7)
const CNAE_SUGGESTIONS = [
  { code: "4781-4/00", label: "Comércio varejista de artigos de vestuário e acessórios" },
  { code: "1412-6/01", label: "Confecção de peças de vestuário profissional" },
  { code: "8121-4/00", label: "Limpeza em prédios e em domicílios" },
  { code: "8011-1/01", label: "Atividades de vigilância e segurança privada" },
  { code: "2710-4/01", label: "Fabricação de equipamentos elétricos" },
  { code: "3250-7/01", label: "Fabricação de instrumentos e materiais para uso médico" },
  { code: "1011-2/01", label: "Abate de reses" },
  { code: "1091-1/01", label: "Fabricação de produtos de panificação" },
  { code: "6201-5/01", label: "Desenvolvimento de software sob encomenda" },
  { code: "6202-3/00", label: "Desenvolvimento e licenciamento de software" },
] as const;

// Value presets in BRL
const VALUE_PRESETS = [
  { value: 50_000, label: "R$ 50 mil" },
  { value: 100_000, label: "R$ 100 mil" },
  { value: 250_000, label: "R$ 250 mil" },
  { value: 500_000, label: "R$ 500 mil" },
  { value: 1_000_000, label: "R$ 1 milhão" },
  { value: 2_000_000, label: "R$ 2 milhões" },
  { value: 5_000_000, label: "R$ 5 milhões" },
];

// ============================================================================
// Types
// ============================================================================

interface OnboardingData {
  cnae: string;
  objetivo_principal: string;
  ufs_atuacao: string[];
  faixa_valor_min: number;
  faixa_valor_max: number;
  // Keep legacy fields for backward compat with PerfilContexto
  porte_empresa: string;
  experiencia_licitacoes: string;
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
// CNAE Input with Autocomplete (AC7)
// ============================================================================

function CNAEInput({
  value,
  onChange,
  onBlur,
  error,
}: {
  value: string;
  onChange: (val: string) => void;
  onBlur?: () => void;
  error?: string;
}) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState(CNAE_SUGGESTIONS.slice());
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const query = value.toLowerCase().trim();
    if (!query) {
      setFilteredSuggestions(CNAE_SUGGESTIONS.slice());
      return;
    }
    setFilteredSuggestions(
      CNAE_SUGGESTIONS.filter(
        (s) => s.code.toLowerCase().includes(query) || s.label.toLowerCase().includes(query)
      )
    );
  }, [value]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={wrapperRef} className="relative">
      <Label required>Segmento / CNAE</Label>
      <Input
        id="cnae"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        onFocus={() => setShowSuggestions(true)}
        placeholder="Ex: Comércio de uniformes, 4781, Limpeza..."
        autoComplete="off"
        error={error}
        errorTestId="cnae-error"
      />
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div className="absolute z-10 mt-1 w-full bg-[var(--surface-0)] border border-[var(--border)] rounded-lg shadow-lg max-h-48 overflow-y-auto">
          {filteredSuggestions.map((s) => (
            <button
              key={s.code}
              onClick={() => {
                onChange(`${s.code} — ${s.label}`);
                setShowSuggestions(false);
              }}
              className="w-full px-3 py-2 text-left text-sm hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="font-mono text-[var(--brand-blue)]">{s.code}</span>
              <span className="text-[var(--ink-secondary)] ml-2">{s.label}</span>
            </button>
          ))}
        </div>
      )}
      <p className="text-xs text-[var(--ink-secondary)] mt-1">
        Aceita CNAE (ex: 4781-4/00) ou texto livre (ex: "Uniformes escolares")
      </p>
    </div>
  );
}

// ============================================================================
// Value Range Selector (AC9)
// ============================================================================

function ValueRangeSelector({
  valorMin,
  valorMax,
  onChangeMin,
  onChangeMax,
}: {
  valorMin: number;
  valorMax: number;
  onChangeMin: (v: number) => void;
  onChangeMax: (v: number) => void;
}) {
  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(val);

  return (
    <div>
      <Label>Faixa de valor ideal dos contratos</Label>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-xs">Valor mínimo</Label>
          <select
            value={valorMin}
            onChange={(e) => onChangeMin(parseInt(e.target.value))}
            className="w-full min-h-[44px] px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)]"
          >
            <option value={0}>Sem limite</option>
            {VALUE_PRESETS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
        <div>
          <Label className="text-xs">Valor máximo</Label>
          <select
            value={valorMax}
            onChange={(e) => onChangeMax(parseInt(e.target.value))}
            className="w-full min-h-[44px] px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)]"
          >
            <option value={0}>Sem limite</option>
            {VALUE_PRESETS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
      </div>
      {valorMin > 0 && valorMax > 0 && valorMax < valorMin && (
        <p className="text-xs text-[var(--error)] mt-1">
          Valor máximo deve ser maior que o mínimo
        </p>
      )}
      <div className="text-xs text-[var(--ink-secondary)] mt-2">
        {valorMin > 0 || valorMax > 0
          ? `Faixa: ${valorMin > 0 ? formatCurrency(valorMin) : "Sem mínimo"} — ${valorMax > 0 ? formatCurrency(valorMax) : "Sem máximo"}`
          : "Todas as faixas de valor"}
      </div>
    </div>
  );
}

// ============================================================================
// Step 1: Qual é o seu negócio? (AC7, AC8)
// ============================================================================

function StepOne({
  data,
  onChange,
  errors,
  onBlur,
}: {
  data: OnboardingData;
  onChange: (partial: Partial<OnboardingData>) => void;
  errors: Record<string, { message?: string }>;
  onBlur: (field: string) => void;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--ink)] mb-1">Qual é o seu negócio?</h2>
        <p className="text-sm text-[var(--ink-secondary)]">
          Informe seu segmento para encontrarmos oportunidades relevantes
        </p>
      </div>

      <CNAEInput
        value={data.cnae}
        onChange={(cnae) => onChange({ cnae })}
        onBlur={() => onBlur("cnae")}
        error={errors.cnae?.message}
      />

      <div>
        <Label required htmlFor="objetivo_principal">Qual é seu objetivo principal?</Label>
        <textarea
          id="objetivo_principal"
          value={data.objetivo_principal}
          onChange={(e) => onChange({ objetivo_principal: e.target.value.slice(0, 200) })}
          onBlur={() => onBlur("objetivo_principal")}
          placeholder="Ex: Encontrar oportunidades de uniformes escolares acima de R$ 100.000 em São Paulo"
          rows={3}
          className={`w-full px-3 py-2.5 rounded-lg border bg-[var(--surface-0)] text-sm text-[var(--ink)] placeholder:text-[var(--ink-secondary)] focus:ring-2 focus:ring-[var(--brand-blue)]/30 focus:border-[var(--brand-blue)] transition-all resize-none ${
            errors.objetivo_principal ? "border-[var(--error)]" : "border-[var(--border)]"
          }`}
          maxLength={200}
          aria-invalid={!!errors.objetivo_principal}
          aria-describedby={errors.objetivo_principal ? "objetivo-error" : undefined}
        />
        {errors.objetivo_principal && (
          <p id="objetivo-error" className="text-xs text-[var(--error)] mt-1" role="alert" data-testid="objetivo-error">
            {errors.objetivo_principal.message}
          </p>
        )}
        <p className="text-xs text-[var(--ink-secondary)] mt-1 text-right">
          {data.objetivo_principal.length}/200
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Step 2: Onde você atua? (AC9)
// ============================================================================

function StepTwo({
  data,
  onChange,
  errors,
}: {
  data: OnboardingData;
  onChange: (partial: Partial<OnboardingData>) => void;
  errors: Record<string, { message?: string }>;
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
        <h2 className="text-xl font-semibold text-[var(--ink)] mb-1">Onde você atua e qual valor ideal?</h2>
        <p className="text-sm text-[var(--ink-secondary)]">
          Selecione estados e faixa de valor para encontrar oportunidades compatíveis
        </p>
      </div>

      {/* UFs de atuação */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <Label required>Estados de atuação <span className="font-normal text-ink-secondary">({data.ufs_atuacao.length} selecionados)</span></Label>
          <div className="flex gap-2">
            <button onClick={selectAll} className="text-xs text-[var(--brand-blue)] hover:underline">
              Todos
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
                  className={`text-sm font-medium mb-1.5 min-h-[44px] px-3 py-2 rounded-lg transition-colors ${
                    allSelected
                      ? "text-[var(--brand-blue)] bg-[var(--brand-blue)]/10"
                      : someSelected
                      ? "text-[var(--ink)] bg-[var(--surface-1)]"
                      : "text-[var(--ink-secondary)]"
                  }`}
                  data-testid={`region-button-${region}`}
                >
                  {region}
                </button>
                <div className="flex flex-wrap gap-1.5">
                  {ufs.map((uf) => (
                    <button
                      key={uf}
                      onClick={() => toggleUf(uf)}
                      className={`min-h-[44px] min-w-[44px] px-3 py-2 text-sm rounded-lg border transition-colors ${
                        data.ufs_atuacao.includes(uf)
                          ? "border-[var(--brand-blue)] bg-[var(--brand-blue)] text-white"
                          : "border-[var(--border)] text-[var(--ink-secondary)] hover:border-[var(--ink-secondary)]"
                      }`}
                      title={UF_NAMES[uf]}
                      data-testid={`uf-button-${uf}`}
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

      {errors.ufs_atuacao && (
        <p className="text-xs text-[var(--error)] mt-1" role="alert" data-testid="ufs-error">
          {errors.ufs_atuacao.message}
        </p>
      )}

      {/* Value Range */}
      <ValueRangeSelector
        valorMin={data.faixa_valor_min}
        valorMax={data.faixa_valor_max}
        onChangeMin={(v) => onChange({ faixa_valor_min: v })}
        onChangeMax={(v) => onChange({ faixa_valor_max: v })}
      />
      {errors.faixa_valor_max && (
        <p className="text-xs text-[var(--error)] mt-1" role="alert" data-testid="valor-error">
          {errors.faixa_valor_max.message}
        </p>
      )}
    </div>
  );
}

// ============================================================================
// Step 3: Confirmação + Primeira Análise (AC10, AC15)
// ============================================================================

function StepThree({
  data,
  isAnalyzing,
}: {
  data: OnboardingData;
  isAnalyzing: boolean;
}) {
  const formatCurrency = (val: number) => {
    if (val === 0) return "Sem limite";
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(val);
  };

  // Extract display name from CNAE string
  const cnaeDisplay = data.cnae.includes("—")
    ? data.cnae.split("—")[1]?.trim() || data.cnae
    : data.cnae;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--ink)] mb-1">Pronto para começar</h2>
        <p className="text-sm text-[var(--ink-secondary)]">
          Vamos encontrar suas primeiras oportunidades agora. Isso leva ~15 segundos.
        </p>
      </div>

      <div className="space-y-4 p-4 rounded-lg bg-[var(--surface-1)] border border-[var(--border)]">
        <div>
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Segmento</div>
          <div className="text-sm font-medium text-[var(--ink)]">{cnaeDisplay}</div>
        </div>
        {data.objetivo_principal && (
          <div>
            <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Objetivo</div>
            <div className="text-sm text-[var(--ink)]">{data.objetivo_principal}</div>
          </div>
        )}
        <div>
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Estados de atuação</div>
          <div className="flex flex-wrap gap-1 mt-1">
            {data.ufs_atuacao.length === 27 ? (
              <span className="text-sm text-[var(--ink)]">Todos os estados</span>
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
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Faixa de valor</div>
          <div className="text-sm text-[var(--ink)]">
            {formatCurrency(data.faixa_valor_min)} — {formatCurrency(data.faixa_valor_max)}
          </div>
        </div>
      </div>

      {isAnalyzing && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--brand-blue)]/5 border border-[var(--brand-blue)]/20">
          <div className="w-5 h-5 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-[var(--brand-blue)]">Analisando oportunidades...</p>
            <p className="text-xs text-[var(--ink-secondary)]">Configurando seu perfil e iniciando análise automática</p>
          </div>
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
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [existingContext, setExistingContext] = useState<Record<string, unknown> | null>(null);

  const [data, setData] = useState<OnboardingData>({
    cnae: "",
    objetivo_principal: "",
    ufs_atuacao: [],
    faixa_valor_min: 100_000,   // Default R$ 100k
    faixa_valor_max: 500_000,   // Default R$ 500k
    porte_empresa: "EPP",       // Default for backward compat
    experiencia_licitacoes: "INICIANTE",
  });

  // react-hook-form for step 1
  const step1Form = useForm<OnboardingStep1Data>({
    resolver: zodResolver(onboardingStep1Schema),
    mode: "onBlur",
    defaultValues: { cnae: "", objetivo_principal: "" },
  });

  // react-hook-form for step 2
  const step2Form = useForm<OnboardingStep2Data>({
    resolver: zodResolver(onboardingStep2Schema),
    mode: "onChange",
    defaultValues: { ufs_atuacao: [], faixa_valor_min: 100_000, faixa_valor_max: 500_000 },
  });

  const updateData = useCallback((partial: Partial<OnboardingData>) => {
    setData((prev) => {
      const next = { ...prev, ...partial };
      // Sync react-hook-form values
      if ("cnae" in partial) step1Form.setValue("cnae", next.cnae, { shouldValidate: step1Form.formState.isSubmitted });
      if ("objetivo_principal" in partial) step1Form.setValue("objetivo_principal", next.objetivo_principal, { shouldValidate: step1Form.formState.isSubmitted });
      if ("ufs_atuacao" in partial) step2Form.setValue("ufs_atuacao", next.ufs_atuacao, { shouldValidate: true });
      if ("faixa_valor_min" in partial) step2Form.setValue("faixa_valor_min", next.faixa_valor_min, { shouldValidate: true });
      if ("faixa_valor_max" in partial) step2Form.setValue("faixa_valor_max", next.faixa_valor_max, { shouldValidate: true });
      return next;
    });
  }, [step1Form, step2Form]);

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
          const ctx = res.context_data;
          const loadedData = {
            cnae: ctx.cnae || "",
            objetivo_principal: ctx.objetivo_principal || "",
            ufs_atuacao: ctx.ufs_atuacao || [],
            faixa_valor_min: ctx.faixa_valor_min ?? 100_000,
            faixa_valor_max: ctx.faixa_valor_max ?? 500_000,
            porte_empresa: ctx.porte_empresa || "EPP",
            experiencia_licitacoes: ctx.experiencia_licitacoes || "INICIANTE",
          };
          setData((prev) => ({ ...prev, ...loadedData }));
          // Sync react-hook-form
          step1Form.reset({ cnae: loadedData.cnae, objetivo_principal: loadedData.objetivo_principal });
          step2Form.reset({ ufs_atuacao: loadedData.ufs_atuacao, faixa_valor_min: loadedData.faixa_valor_min, faixa_valor_max: loadedData.faixa_valor_max });
        }
      })
      .catch(() => {});
  }, [session?.access_token]);

  // Validation per step — uses value checks for button state, zod for inline errors
  const canProceed = (): boolean => {
    if (currentStep === 0) {
      return data.cnae.trim().length > 0 && data.objetivo_principal.trim().length > 0;
    }
    if (currentStep === 1) {
      if (data.ufs_atuacao.length === 0) return false;
      if (data.faixa_valor_min > 0 && data.faixa_valor_max > 0 && data.faixa_valor_max < data.faixa_valor_min) return false;
      return true;
    }
    return true;
  };

  const submitAndAnalyze = async () => {
    if (!session?.access_token) return;
    setIsAnalyzing(true);

    try {
      // 1. Save profile context (backward compatible)
      const profilePayload: Record<string, unknown> = {
        ufs_atuacao: data.ufs_atuacao,
        porte_empresa: data.porte_empresa,
        experiencia_licitacoes: data.experiencia_licitacoes,
        cnae: data.cnae,
        objetivo_principal: data.objetivo_principal,
        ticket_medio_desejado: data.faixa_valor_max || null,
      };
      if (data.faixa_valor_min > 0) profilePayload.faixa_valor_min = data.faixa_valor_min;
      if (data.faixa_valor_max > 0) profilePayload.faixa_valor_max = data.faixa_valor_max;

      const profileRes = await fetch("/api/profile-context", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(profilePayload),
      });

      if (!profileRes.ok) throw new Error("Erro ao salvar perfil");

      // Cache locally
      safeSetItem("smartlic-profile-context", JSON.stringify(profilePayload));
      safeSetItem("smartlic-onboarding-completed", "true");

      // 2. Start first analysis
      const analysisRes = await fetch("/api/first-analysis", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          cnae: data.cnae,
          objetivo_principal: data.objetivo_principal,
          ufs: data.ufs_atuacao,
          faixa_valor_min: data.faixa_valor_min > 0 ? data.faixa_valor_min : null,
          faixa_valor_max: data.faixa_valor_max > 0 ? data.faixa_valor_max : null,
        }),
      });

      if (!analysisRes.ok) {
        // If first analysis fails, still redirect (graceful degradation)
        toast.success("Perfil salvo! Redirecionando...");
        router.push(`/buscar?ufs=${data.ufs_atuacao.join(",")}`);
        return;
      }

      const { search_id } = await analysisRes.json();

      // 3. Redirect to search with auto flag
      toast.success("Perfil salvo! Analisando suas oportunidades...");
      router.push(`/buscar?auto=true&search_id=${search_id}`);
    } catch {
      toast.error("Erro ao configurar perfil. Tente novamente.");
      setIsAnalyzing(false);
    }
  };

  const handleSkip = () => {
    router.push("/buscar");
  };

  const nextStep = async () => {
    if (currentStep === 0) {
      // Trigger zod validation for step 1
      step1Form.setValue("cnae", data.cnae);
      step1Form.setValue("objetivo_principal", data.objetivo_principal);
      const valid = await step1Form.trigger();
      if (!valid) return;
      setCurrentStep(1);
    } else if (currentStep === 1) {
      // Trigger zod validation for step 2
      step2Form.setValue("ufs_atuacao", data.ufs_atuacao);
      step2Form.setValue("faixa_valor_min", data.faixa_valor_min);
      step2Form.setValue("faixa_valor_max", data.faixa_valor_max);
      const valid = await step2Form.trigger();
      if (!valid) return;
      setCurrentStep(2);
    } else {
      submitAndAnalyze();
    }
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

  return (
    <div className="min-h-screen bg-[var(--surface-0)] flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-[var(--ink)]">
            {existingContext ? "Atualizar Perfil Estratégico" : "Configure seu Perfil Estratégico"}
          </h1>
          <p className="text-sm text-[var(--ink-secondary)] mt-1">
            Em 3 passos vamos encontrar suas primeiras oportunidades
          </p>
        </div>

        {/* Card */}
        <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-xl p-6 shadow-sm">
          <ProgressBar currentStep={currentStep} totalSteps={3} />

          {/* Steps */}
          {currentStep === 0 && (
            <StepOne
              data={data}
              onChange={updateData}
              errors={step1Form.formState.errors as Record<string, { message?: string }>}
              onBlur={(field) => step1Form.trigger(field as keyof OnboardingStep1Data)}
            />
          )}
          {currentStep === 1 && (
            <StepTwo
              data={data}
              onChange={updateData}
              errors={step2Form.formState.errors as Record<string, { message?: string }>}
            />
          )}
          {currentStep === 2 && <StepThree data={data} isAnalyzing={isAnalyzing} />}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-4 border-t border-[var(--border)]">
            <div>
              {currentStep > 0 ? (
                <button
                  onClick={prevStep}
                  disabled={isAnalyzing}
                  className="min-h-[44px] px-4 py-2 text-sm text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors disabled:opacity-40"
                  data-testid="btn-voltar"
                >
                  Voltar
                </button>
              ) : (
                <button
                  onClick={handleSkip}
                  className="min-h-[44px] px-4 py-2 text-sm text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
                  data-testid="btn-pular"
                >
                  Pular por agora
                </button>
              )}
            </div>
            <div className="flex items-center gap-3">
              {currentStep < 2 && (
                <button
                  onClick={handleSkip}
                  className="min-h-[44px] px-4 py-2 text-sm text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
                  data-testid="btn-pular-alt"
                >
                  Pular por agora
                </button>
              )}
              <button
                onClick={nextStep}
                disabled={!canProceed() || isAnalyzing}
                className="min-h-[44px] px-6 py-2.5 rounded-lg bg-[var(--brand-blue)] text-white text-sm font-medium
                           disabled:opacity-40 hover:bg-[var(--brand-blue-hover)] transition-colors"
                data-testid="btn-continuar"
              >
                {currentStep === 2
                  ? isAnalyzing
                    ? "Analisando..."
                    : "Ver Minhas Oportunidades"
                  : "Continuar"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
