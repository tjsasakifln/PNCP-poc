'use client';

/**
 * STORY-BIZ-002: upsell banner shown to trial users whose CNAE marks them as
 * a consultancy (divisions 70.2 / 74.9 / 82.9). Dismiss persists in
 * localStorage for 7 days — after that the banner re-shows so users have
 * another chance to evaluate the Consultoria plan before their trial ends.
 */

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRecommendedPlan } from '../hooks/useRecommendedPlan';
import { useAnalytics } from '../hooks/useAnalytics';

const DISMISS_KEY = 'consultoria_banner_dismissed_ts';
const DISMISS_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

interface ConsultoriaUpsellBannerProps {
  /**
   * Whether the current user is still in trial. Banner only renders for
   * trial users — paid subscribers already selected a plan.
   */
  isTrialing: boolean;
}

function isRecentlyDismissed(): boolean {
  if (typeof window === 'undefined') return true;
  try {
    const ts = window.localStorage.getItem(DISMISS_KEY);
    if (!ts) return false;
    const n = Number(ts);
    if (!Number.isFinite(n)) return false;
    return Date.now() - n < DISMISS_TTL_MS;
  } catch {
    return false;
  }
}

export default function ConsultoriaUpsellBanner({ isTrialing }: ConsultoriaUpsellBannerProps) {
  const { data, loading } = useRecommendedPlan();
  const { trackEvent } = useAnalytics();
  const [dismissed, setDismissed] = useState(true);

  useEffect(() => {
    setDismissed(isRecentlyDismissed());
  }, []);

  const shouldShow =
    isTrialing && !loading && !dismissed && data?.plan_key === 'consultoria' && data.reason === 'cnae_consultoria';

  useEffect(() => {
    if (shouldShow) {
      trackEvent('consultoria_upsell_viewed', { surface: 'banner' });
    }
  }, [shouldShow, trackEvent]);

  if (!shouldShow) return null;

  function handleDismiss() {
    try {
      window.localStorage.setItem(DISMISS_KEY, String(Date.now()));
    } catch {
      // localStorage full / disabled — best effort
    }
    setDismissed(true);
    trackEvent('consultoria_upsell_dismissed', { surface: 'banner' });
  }

  function handleClick() {
    trackEvent('consultoria_upsell_clicked', { cta_label: 'ver_detalhes' });
  }

  return (
    <div
      role="region"
      aria-label="Oferta plano Consultoria"
      className="flex flex-col sm:flex-row items-start sm:items-center gap-3 bg-indigo-50 border border-indigo-200 text-indigo-900 px-4 py-3 rounded mb-4"
    >
      <div className="flex-1 text-sm leading-relaxed">
        <strong>Você é uma consultoria.</strong>{' '}
        Com o plano Consultoria você atende até 20 CNPJs de clientes por R$ 997/mês — economia de 60% vs múltiplas
        licenças Pro.{' '}
        <Link
          href="/planos?highlight=consultoria"
          onClick={handleClick}
          className="font-medium text-indigo-700 hover:underline"
        >
          Ver detalhes →
        </Link>
      </div>
      <button
        type="button"
        onClick={handleDismiss}
        aria-label="Dispensar oferta"
        className="text-indigo-500 hover:text-indigo-700 text-sm px-2 py-1"
      >
        Dispensar
      </button>
    </div>
  );
}
