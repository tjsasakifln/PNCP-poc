"use client";

/**
 * STORY-442: Guided tour interativo para /buscar
 *
 * Ativa automaticamente na primeira visita pós-onboarding (AC1).
 * 5 passos: Busca → Score de Viabilidade → Resumo IA → Pipeline → Export (AC2).
 * Botão "Pular" em todos os passos (AC3) — fornecido pelo useShepherdTour.
 * Estado salvo em localStorage key: smartlic_buscar_tour_completed (AC4).
 * Responsivo mobile/tablet/desktop (AC7).
 * Mixpanel: tour_started, tour_step_completed, tour_completed, tour_skipped (AC6).
 *
 * Retorna null — o tour é gerenciado pelo Shepherd.js sem renderizar DOM próprio.
 */

import { useEffect, useRef } from "react";
import { useShepherdTour } from "../../../hooks/useShepherdTour";
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

  // Índice do passo atual para tour_step_completed
  const currentStepIndexRef = useRef(0);

  const { startTour } = useShepherdTour({
    tourId: "buscar_guided",
    steps: GUIDED_TOUR_STEPS,
    onComplete: (stepsSeen) => {
      // AC4: marcar como concluído na chave canônica
      safeSetItem(GUIDED_TOUR_STORAGE_KEY, "true");
      // AC6
      trackEventRef.current("tour_completed", {
        tour: "buscar_guided",
        steps_seen: stepsSeen,
      });
    },
    onSkip: (stepsSeen) => {
      // AC4: também marcar como "visto" para não reiniciar
      safeSetItem(GUIDED_TOUR_STORAGE_KEY, "true");
      // AC6
      trackEventRef.current("tour_skipped", {
        tour: "buscar_guided",
        skipped_at_step: stepsSeen,
      });
    },
  });

  const startTourRef = useRef(startTour);
  startTourRef.current = startTour;

  useEffect(() => {
    // AC1: ativar automaticamente apenas se onboarding concluído e tour não feito
    if (!isOnboardingDone()) return;
    if (safeGetItem(GUIDED_TOUR_STORAGE_KEY) === "true") return;

    // Pequeno delay para garantir que os elementos do DOM estão prontos
    const timer = setTimeout(() => {
      startTourRef.current();

      // AC6: tour_started
      trackEventRef.current("tour_started", { tour: "buscar_guided" });

      // AC6: tour_step_completed por passo — hookear via Shepherd DOM events
      // useShepherdTour dispara 'show' internamente; usamos MutationObserver
      // para detectar mudança de step no DOM do Shepherd
      const observer = new MutationObserver(() => {
        const stepEl = document.querySelector(".shepherd-step");
        if (!stepEl) return;
        const stepId = stepEl.getAttribute("data-shepherd-step-id") ?? "";
        const stepIndex = GUIDED_TOUR_STEPS.findIndex((s) => s.id === stepId);
        if (stepIndex >= 0 && stepIndex !== currentStepIndexRef.current) {
          // AC6: tour_step_completed ao avançar para próximo passo
          trackEventRef.current("tour_step_completed", {
            tour: "buscar_guided",
            step_index: currentStepIndexRef.current,
            step_title: GUIDED_TOUR_STEPS[currentStepIndexRef.current]?.title ?? "",
          });
          currentStepIndexRef.current = stepIndex;
        }
      });
      observer.observe(document.body, { childList: true, subtree: true, attributes: true });

      return () => observer.disconnect();
    }, 600);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // AC5 suporte: expor função para reiniciar via URL param ?restart_tour=1
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("restart_tour") !== "1") return;

    // Limpar param da URL sem reload
    const url = new URL(window.location.href);
    url.searchParams.delete("restart_tour");
    window.history.replaceState({}, "", url.toString());

    // Iniciar o tour (a chave já foi removida pela página /conta)
    const timer = setTimeout(() => {
      startTourRef.current();
      trackEventRef.current("tour_started", { tour: "buscar_guided", source: "restart" });
    }, 600);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Não renderiza nada — o tour é visual do Shepherd.js
  return null;
}
