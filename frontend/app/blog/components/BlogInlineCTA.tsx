import Link from 'next/link';
import { getCtaByIntent } from '@/lib/cta-intent';
import type { CtaPageType, CtaConfig } from '@/lib/cta-intent';
import { CtaIntent } from '@/components/cta/CtaIntent';

/**
 * MKT-001 AC3: Inline CTA inserted at ~40% of blog post content.
 *
 * CRO-CTA-000: Accepts intent-based CTA via `pageType` or full override via
 * `ctaConfig`. Defaults to legacy behaviour when neither is passed.
 *
 * UTM: utm_source=blog&utm_medium=cta&utm_content=[slug]
 */

interface BlogInlineCTAProps {
  slug: string;
  campaign?: 'b2g' | 'consultorias' | 'guias' | 'contratos' | 'subcontratacao';
  ctaHref?: string;
  ctaText?: string;
  ctaMessage?: string;
  /** CRO-CTA-000: Page type for intent-based CTA */
  pageType?: CtaPageType;
  /** CRO-CTA-000: Full CTA config override (takes precedence over pageType) */
  ctaConfig?: CtaConfig;
}

/**
 * Blog inline CTA banner.
 *
 * Copy rules:
 * - ctaMessage ≤ 12 words (ideally ≤ 8)
 * - ctaText ≤ 4 words
 */
export default function BlogInlineCTA({
  slug,
  campaign = 'b2g',
  ctaHref,
  ctaText,
  ctaMessage,
  pageType,
  ctaConfig,
}: BlogInlineCTAProps) {
  // Priority 1: Direct CtaConfig override
  if (ctaConfig) {
    return <CtaIntent config={ctaConfig} variant="inline" />;
  }

  // Priority 2: Intent-based with explicit page type
  if (pageType) {
    const config = getCtaByIntent(pageType, { slug });
    return <CtaIntent config={config} variant="inline" />;
  }

  // Priority 3: Legacy fallback
  const defaultHref = `/signup?source=blog&article=${slug}&utm_source=blog&utm_medium=cta&utm_content=${slug}&utm_campaign=${campaign}`;
  const href = ctaHref
    ? `${ctaHref}?utm_source=blog&utm_medium=cta&utm_content=${slug}&utm_campaign=${campaign}`
    : defaultHref;

  return (
    <div className="not-prose my-8 sm:my-10 bg-brand-blue-subtle/50 dark:bg-brand-navy/10 rounded-lg p-4 sm:p-5 border border-brand-blue/15 flex flex-col sm:flex-row items-center gap-3 sm:gap-4">
      <p className="text-sm sm:text-base text-ink font-medium text-center sm:text-left flex-1">
        {ctaMessage || 'dado público verificável \u2014 sem cartão de crédito'}
      </p>
      <Link
        href={href}
        className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2 rounded-button text-sm transition-all hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap"
      >
        {ctaText || 'Pedir um diagnóstico à CONFENGE'}
      </Link>
    </div>
  );
}
