import { useCallback } from 'react';
import { getCookieConsent } from '../app/components/CookieConsentBanner';

type ClarityWindow = Window & {
  clarity?: ((...args: unknown[]) => void) & { q?: unknown[] };
};

function hasAnalyticsConsent(): boolean {
  const consent = getCookieConsent();
  return consent?.analytics === true;
}

function callClarity(...args: unknown[]): void {
  if (typeof window === 'undefined') return;
  if (!hasAnalyticsConsent()) return;
  const win = window as ClarityWindow;
  win.clarity?.(...args);
}

/**
 * Hook para disparar eventos customizados no Microsoft Clarity.
 * Todos os métodos respeitam o consentimento LGPD (mesmo padrão do useAnalytics).
 *
 * @example
 * const { clarityEvent, claritySet, clarityIdentify } = useClarity();
 * clarityEvent('trial_paywall_shown');
 * claritySet('plan_type', 'free_trial');
 * clarityIdentify(userId);
 */
export function useClarity() {
  /**
   * Marca um evento customizado na linha do tempo da gravação.
   * Aparece como marker navegável no Clarity dashboard.
   */
  const clarityEvent = useCallback((name: string) => {
    callClarity('event', name);
  }, []);

  /**
   * Define uma tag de sessão filtrável no Clarity dashboard.
   * Ex: plan_type, is_trial, user_segment.
   */
  const claritySet = useCallback((key: string, value: string) => {
    callClarity('set', key, value);
  }, []);

  /**
   * Identifica o usuário na gravação — linka sessão ao userId no dashboard.
   * Deve ser chamado após autenticação confirmada.
   */
  const clarityIdentify = useCallback((userId: string, sessionId?: string) => {
    callClarity('identify', userId, sessionId ?? null, null, userId);
  }, []);

  return { clarityEvent, claritySet, clarityIdentify };
}
