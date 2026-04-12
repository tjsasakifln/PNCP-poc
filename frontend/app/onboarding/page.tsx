"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "../components/AuthProvider";
import { toast } from "sonner";
import { safeSetItem } from "../../lib/storage";
import { useAnalytics } from "../../hooks/useAnalytics";
import { getDaysInTrial } from "../../lib/analytics-helpers";
import {
  onboardingStep1Schema,
  onboardingStep2Schema,
  type OnboardingStep1Data,
  type OnboardingStep2Data,
} from "../../lib/schemas/forms";

import { OnboardingProgress } from "./components/OnboardingProgress";
import { OnboardingStep1 } from "./components/OnboardingStep1";
import { OnboardingStep2 } from "./components/OnboardingStep2";
import { OnboardingStep3 } from "./components/OnboardingStep3";
import type { OnboardingData } from "./components/types";

// ============================================================================
// Main Onboarding Page
// ============================================================================

export default function OnboardingPage() {
  const router = useRouter();
  const { user, session, loading: authLoading } = useAuth();
  const { trackEvent } = useAnalytics();
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
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
    setAnalysisError(null);

    // Zero-churn P1 §6.1: 30s timeout for first analysis
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30_000);

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
        signal: controller.signal,
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
        signal: controller.signal,
      });

      if (!analysisRes.ok) {
        // Zero-churn P1 §6.1: Detect trial expired (403)
        if (analysisRes.status === 403) {
          setAnalysisError("trial_expired");
          setIsAnalyzing(false);
          return;
        }
        // Other errors: still redirect with graceful degradation
        toast.success("Perfil salvo! Redirecionando...");
        router.push(`/buscar?ufs=${data.ufs_atuacao.join(",")}`);
        return;
      }

      const { search_id } = await analysisRes.json();

      // 3. Redirect to search with auto flag
      toast.success("Perfil salvo! Analisando suas oportunidades...");
      router.push(`/buscar?auto=true&search_id=${search_id}`);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setAnalysisError("timeout");
      } else {
        toast.error("Erro ao configurar perfil. Tente novamente.");
        setAnalysisError("generic");
      }
      setIsAnalyzing(false);
    } finally {
      clearTimeout(timeout);
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
      trackEvent('onboarding_step_completed', {
        step: 1,
        total_steps: 3,
        cnae: data.cnae,
        objetivo_principal: data.objetivo_principal,
        days_in_trial: getDaysInTrial(user?.created_at),
      });
      setCurrentStep(1);
    } else if (currentStep === 1) {
      // Trigger zod validation for step 2
      step2Form.setValue("ufs_atuacao", data.ufs_atuacao);
      step2Form.setValue("faixa_valor_min", data.faixa_valor_min);
      step2Form.setValue("faixa_valor_max", data.faixa_valor_max);
      const valid = await step2Form.trigger();
      if (!valid) return;
      trackEvent('onboarding_step_completed', {
        step: 2,
        total_steps: 3,
        ufs_count: data.ufs_atuacao.length,
        faixa_valor_min: data.faixa_valor_min,
        faixa_valor_max: data.faixa_valor_max,
        days_in_trial: getDaysInTrial(user?.created_at),
      });
      setCurrentStep(2);
    } else {
      trackEvent('onboarding_step_completed', {
        step: 3,
        total_steps: 3,
        days_in_trial: getDaysInTrial(user?.created_at),
      });
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
          <OnboardingProgress currentStep={currentStep} totalSteps={3} />

          {/* Steps */}
          {currentStep === 0 && (
            <OnboardingStep1
              data={data}
              onChange={updateData}
              errors={step1Form.formState.errors as Record<string, { message?: string }>}
              onBlur={(field) => step1Form.trigger(field as keyof OnboardingStep1Data)}
            />
          )}
          {currentStep === 1 && (
            <OnboardingStep2
              data={data}
              onChange={updateData}
              errors={step2Form.formState.errors as Record<string, { message?: string }>}
            />
          )}
          {currentStep === 2 && (
            <OnboardingStep3
              data={data}
              isAnalyzing={isAnalyzing}
              error={analysisError}
              onGoBack={() => { setAnalysisError(null); setCurrentStep(1); }}
            />
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-4 border-t border-[var(--border)]">
            <div>
              {currentStep > 0 && (
                <button
                  onClick={prevStep}
                  disabled={isAnalyzing}
                  className="min-h-[44px] px-4 py-2 text-sm text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors disabled:opacity-40"
                  data-testid="btn-voltar"
                >
                  Voltar
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
