'use client';

/**
 * CONV-002 (#1311): OpportunitySignalsPanel — shared component for transactional
 * landing pages.
 *
 * Renders up to 5 business opportunity signal cards with contextual CTAs.
 * Each signal shows an icon, label, value, and supporting description.
 *
 * Fires Mixpanel events:
 *   - `opportunity_signal_view` on mount (once per render)
 *   - `opportunity_cta_click` on primary CTA click
 *
 * CTA rule (CRO-CTA-000): NEVER SaaS trial or pricing CTAs as primary CTA.
 * The CTA must continue the visitor's search intent.
 */

import { useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { trackPseoEvent, type PseoSourceTemplate } from '@/lib/analytics/pseo';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SignalItem {
  /** Emoji icon representing the signal (e.g. '💰', '🏛️'). */
  icon: string;
  /** Short label (e.g. "Valor total contratado"). */
  label: string;
  /** Primary value (e.g. "R$ 2,5 mi"). */
  value: string;
  /** Supporting text (e.g. "em 48 contratos nos últimos 24 meses"). */
  description: string;
}

export interface CtaAction {
  /** Primary button label (max 5 words, ideally <= 4). */
  label: string;
  /** Primary button href. */
  href: string;
  /** Optional secondary button text (lighter visual weight). */
  secondaryLabel?: string;
  /** Optional secondary button href. */
  secondaryHref?: string;
}

export interface OpportunitySignalsPanelProps {
  /** Array of signal items (max 5 rendered). */
  signals: SignalItem[];
  /** CTA configuration for the action buttons. */
  cta: CtaAction;
  /** Template identifier for Mixpanel attribution (e.g. 'fornecedor_page'). */
  sourceTemplate: PseoSourceTemplate;
  /** Entity identifier for analytics (CNPJ, slug, etc.). */
  entityId?: string;
  /** Sector slug for analytics. */
  setor?: string;
  /** UF code for analytics. */
  uf?: string;
  /** Optional heading override. Default: "Sinais de Oportunidade". */
  heading?: string;
  /** Optional subheading shown below the heading. */
  subheading?: string;
  /** When true, renders in compact variant (fewer columns, tighter spacing). */
  compact?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function OpportunitySignalsPanel({
  signals,
  cta,
  sourceTemplate,
  entityId,
  setor,
  uf,
  heading = 'Sinais de Oportunidade',
  subheading,
  compact = false,
}: OpportunitySignalsPanelProps) {
  // Limit to max 5 signals (CONV-002 #1311 requirement)
  const displaySignals = signals.slice(0, 5);

  // Fire view event only once on mount
  const viewFiredRef = useRef(false);
  useEffect(() => {
    if (viewFiredRef.current) return;
    viewFiredRef.current = true;
    trackPseoEvent('opportunity_signal_view', {
      source_template: sourceTemplate,
      entity_id: entityId,
      setor,
      uf,
      signal_count: displaySignals.length,
      page_url: typeof window !== 'undefined' ? window.location.href : undefined,
    });
  }, [sourceTemplate, entityId, setor, uf, displaySignals.length]);

  const handleCtaClick = useCallback(() => {
    trackPseoEvent('opportunity_cta_click', {
      source_template: sourceTemplate,
      entity_id: entityId,
      setor,
      uf,
      destination_url: cta.href,
      page_url: typeof window !== 'undefined' ? window.location.href : undefined,
    });
  }, [sourceTemplate, entityId, setor, uf, cta.href]);

  if (displaySignals.length === 0) return null;

  return (
    <section
      className={`rounded-xl border border-blue-100 bg-gradient-to-br from-blue-50 to-white ${compact ? 'p-4' : 'p-6'}`}
    >
      {/* Heading */}
      <div className="mb-4">
        <h2 className={`font-bold text-gray-900 ${compact ? 'text-base' : 'text-lg'}`}>
          {heading}
        </h2>
        {subheading && (
          <p className="text-sm text-gray-500 mt-0.5">{subheading}</p>
        )}
      </div>

      {/* Signal Cards — 1col mobile, 2/3 cols desktop */}
      <div
        className={`grid gap-3 ${
          compact
            ? 'grid-cols-1 sm:grid-cols-2'
            : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
        }`}
      >
        {displaySignals.map((signal, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-lg bg-white p-3 shadow-sm border border-gray-100"
          >
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-50 text-lg"
              aria-hidden="true"
            >
              {signal.icon}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                {signal.label}
              </p>
              <p className="text-sm font-bold text-gray-900 mt-0.5">
                {signal.value}
              </p>
              <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                {signal.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* CTA Row */}
      <div className={`flex flex-col sm:flex-row gap-3 ${compact ? 'mt-4' : 'mt-5'}`}>
        <Link
          href={cta.href}
          onClick={handleCtaClick}
          className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors min-h-[44px]"
          data-testid="opportunity-cta-primary"
        >
          {cta.label} →
        </Link>
        {cta.secondaryLabel && cta.secondaryHref && (
          <Link
            href={cta.secondaryHref}
            className="inline-flex items-center justify-center rounded-lg border border-gray-300 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors min-h-[44px]"
            data-testid="opportunity-cta-secondary"
          >
            {cta.secondaryLabel}
          </Link>
        )}
      </div>
    </section>
  );
}
