"use client";

/**
 * STORY-442 / STORY-4.2: Guided tour interativo para /buscar
 *
 * Migrado de Shepherd.js para o componente Tour customizado com WCAG 2.1 AA
 * (role="dialog", aria-modal="false", aria-live="polite", focus-trap-react).
 *
 * Ativa automaticamente na primeira visita pós-onboarding (AC1).
 * 5 passos: Busca → Score de Viabilidade → Resumo IA → Pipeline → Export (AC2).
 * Botão "Pular" em todos os passos (AC3).
 * Estado salvo em localStorage key: smartlic_buscar_tour_completed (AC4).
 * Mixpanel: tour_started, tour_step_completed, tour_completed, tour_skipped (AC6).
 */

import { useEffect, useState, useRef } from "react";
import { Tour } from "../../../components/tour/Tour";
import { GUIDED_TOUR_STEPS } from "../constants/tour-steps";
import { useAnalytics } from "../../../hooks/useAnalytics";
import { safeGetItem, safeSetItem } from "../../../lib/storage";

/** AC4: chave canônica do tour guiado */
export const GUIDED_TOUR_STORAGE_KEY = "smartlic_buscar_tour_completed";

/** Verifica se o onboarding inicial foi concluído ou dispensado */
function isOnboardingDone(): boolean {
  return (
    safeGetItem("smartlic_onboarding_completed") === "true" ||
    safeGetItem("smartlic_onboarding_dismissed") === "true"
  );
}

export function GuidedTour() {
  const { trackEvent } = useAnalytics();
  const trackEventRef = useRef(trackEvent);
  trackEventRef.current = trackEvent;

  const [active, setActive] = useState(false);

  // AC1: ativar automaticamente apenas se onboarding concluído e tour não feito
  useEffect(() => {
    if (!isOnboardingDone()) return;
    if (safeGetItem(GUIDED_TOUR_STORAGE_KEY) === "true") return;

    const timer = setTimeout(() => {
      setActive(true);
      trackEventRef.current("tour_started", { tour: "buscar_guided" });
    }, 600);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // AC5: reiniciar tour via URL param ?restart_tour=1
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("restart_tour") !== "1") return;

    // Limpar param da URL sem reload
    const url = new URL(window.location.href);
    url.searchParams.delete("restart_tour");
    window.history.replaceState({}, "", url.toString());

    const timer = setTimeout(() => {
      setActive(true);
      trackEventRef.current("tour_started", { tour: "buscar_guided", source: "restart" });
    }, 600);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Tour
      tourId="buscar_guided"
      steps={GUIDED_TOUR_STEPS}
      active={active}
      storageKey={GUIDED_TOUR_STORAGE_KEY}
      onComplete={(stepsSeen) => {
        safeSetItem(GUIDED_TOUR_STORAGE_KEY, "true");
        setActive(false);
        trackEventRef.current("tour_completed", {
          tour: "buscar_guided",
          steps_seen: stepsSeen,
        });
      }}
      onSkip={(skippedAtStep) => {
        safeSetItem(GUIDED_TOUR_STORAGE_KEY, "true");
        setActive(false);
        trackEventRef.current("tour_skipped", {
          tour: "buscar_guided",
          skipped_at_step: skippedAtStep,
        });
      }}
      onStepChange={(index) => {
        // AC6: tour_step_completed ao avançar
        trackEventRef.current("tour_step_completed", {
          tour: "buscar_guided",
          step_index: index,
          step_title: GUIDED_TOUR_STEPS[index]?.title ?? "",
        });
      }}
    />
  );
}
