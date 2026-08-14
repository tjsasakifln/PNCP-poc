import Link from 'next/link';
import { getUfPrep } from '@/lib/programmatic';
import { getCtaByIntent } from '@/lib/cta-intent';
import type { CtaPageType, CtaConfig } from '@/lib/cta-intent';
import { CtaIntent } from '@/components/cta/CtaIntent';
import ZeroEditalsCTA from './ZeroEditalsCTA';

/**
 * MKT-002 AC6: Contextual CTA component for programmatic SEO pages.
 *
 * CRO-CTA-000: Supports the intent-based CTA system. Pass `pageType` to
 * derive CTA config via getCtaByIntent(), or pass `ctaConfig` directly
 * for full control. When neither is passed, defaults to CONFENGE diagnostic.
 *
 * Variants:
 * - inline: Inserted mid-content (compact)
 * - final: Bottom of page (prominent, full-width)
 *
 * Props personalize CTA text with sector, UF, and edital count.
 * UTM params: utm_source=blog&utm_medium=programmatic&utm_content={slug}
 */

interface BlogCTAProps {
  variant: 'inline' | 'final';
  setor?: string;
  uf?: string;
  /** 2-letter UF code (e.g. "BA") — used to determine the correct preposition */
  ufCode?: string;
  count?: number;
  slug: string;
  /** Zero-editais: contract statistics to show when count === 0 */
  contractsCount?: number;
  contractsTotalValue?: number;
  contractsAvgValue?: number;
  /** CRO-CTA-000: Page type for intent-based CTA derivation */
  pageType?: CtaPageType;
  /** CRO-CTA-000: Full CTA config override (takes precedence over pageType) */
  ctaConfig?: CtaConfig;
}

function buildHref(slug: string): string {
  return `/consultoria-b2g?source=blog&utm_source=blog&utm_medium=programmatic&utm_content=${encodeURIComponent(slug)}`;
}

function buildCTAText(setor?: string, uf?: string, ufCode?: string, count?: number): string {
  const parts: string[] = [];

  if (count && count > 0) {
    parts.push(`Veja todas as ${count} licitações`);
  } else {
    parts.push('Veja todas as licitações');
  }

  if (setor) {
    parts[0] += ` de ${setor}`;
  }

  if (uf) {
    parts[0] += ` ${getUfPrep(ufCode)} ${uf}`;
  }

  parts.push('dado público verificável');
  return parts.join(' — ');
}

// ---------------------------------------------------------------------------
// Legacy inline CTA (kept for backward compat when pageType/ctaConfig absent)
// ---------------------------------------------------------------------------

function LegacyInlineCTA({ setor, uf, ufCode, count, slug }: Omit<BlogCTAProps, 'variant'>) {
  const text = buildCTAText(setor, uf, ufCode, count);
  const href = buildHref(slug);

  return (
    <div className="not-prose my-8 sm:my-10 bg-brand-blue-subtle/50 rounded-lg p-4 sm:p-5 border border-brand-blue/15 flex flex-col sm:flex-row items-center gap-3 sm:gap-4">
      <p className="text-sm sm:text-base text-ink font-medium text-center sm:text-left flex-1">
        {text}
      </p>
      <Link
        href={href}
        className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2 rounded-button text-sm transition-all hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap"
      >
        Comece Agora
      </Link>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Legacy final CTA (kept for backward compat when pageType/ctaConfig absent)
// ---------------------------------------------------------------------------

function LegacyFinalCTA({ setor, uf, ufCode, count, slug, contractsCount, contractsTotalValue, contractsAvgValue }: Omit<BlogCTAProps, 'variant'>) {
  const href = buildHref(slug);
  const prep = uf ? ` ${getUfPrep(ufCode)} ${uf}` : '';

  // AC6: zero-editais → renderiza ZeroEditalsCTA com dados de contratos
  if (!count && (contractsCount ?? 0) > 0 && setor && ufCode && uf) {
    return (
      <ZeroEditalsCTA
        setor={setor}
        uf={uf}
        ufCode={ufCode}
        slug={slug}
        contractsCount={contractsCount!}
        contractsTotalValue={contractsTotalValue!}
        contractsAvgValue={contractsAvgValue}
      />
    );
  }

  return (
    <div className="not-prose mt-12 mb-8 bg-gradient-to-br from-brand-navy to-brand-blue rounded-xl p-6 sm:p-8 text-white text-center">
      <h3 className="text-xl sm:text-2xl font-bold mb-3">
        {count && count > 0
          ? `${count} licitações${setor ? ` de ${setor}` : ''}${prep} esperando sua análise`
          : `Licitações${setor ? ` de ${setor}` : ''}${prep} esperando sua análise`}
      </h3>
      <p className="text-white/80 mb-6 max-w-xl mx-auto">
        Filtre por viabilidade real, receba alertas automáticos e exporte relatórios.
        Dado público verificável. Diagnóstico com a CONFENGE.
      </p>
      <Link
        href={href}
        className="inline-block bg-white text-brand-navy font-semibold px-6 py-3 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98]"
      >
        Pedir um diagnóstico à CONFENGE
      </Link>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Intent-based CTA wrappers
// ---------------------------------------------------------------------------

function IntentInlineCTA({ pageType, setor, uf, ufCode, count, slug }: {
  pageType: CtaPageType;
  setor?: string;
  uf?: string;
  ufCode?: string;
  count?: number;
  slug: string;
}) {
  const config = getCtaByIntent(pageType, { setor, uf, ufCode, count, slug });
  return <CtaIntent config={config} variant="inline" />;
}

function IntentFinalCTA({ pageType, setor, uf, ufCode, count, slug, totalValue }: {
  pageType: CtaPageType;
  setor?: string;
  uf?: string;
  ufCode?: string;
  count?: number;
  slug: string;
  totalValue?: number;
}) {
  const config = getCtaByIntent(pageType, { setor, uf, ufCode, count, slug, totalValue });
  return <CtaIntent config={config} variant="hero" />;
}

// ---------------------------------------------------------------------------
// Exported component
// ---------------------------------------------------------------------------

/**
 * BlogCTA component.
 *
 * CRO-CTA-000 priority:
 * 1. ctaConfig prop -> direct render via CtaIntent
 * 2. pageType prop -> derive via getCtaByIntent -> render via CtaIntent
 * 3. neither -> CONFENGE diagnostic destination
 */
export default function BlogCTA({ variant, pageType, ctaConfig, ...rest }: BlogCTAProps) {
  // Priority 1: Direct CtaConfig override
  if (ctaConfig) {
    return <CtaIntent config={ctaConfig} variant={variant === 'inline' ? 'inline' : 'hero'} />;
  }

  // Priority 2: Intent-based with explicit page type
  if (pageType) {
    if (variant === 'inline') {
      return <IntentInlineCTA pageType={pageType} {...rest} />;
    }
    return <IntentFinalCTA pageType={pageType} {...rest} />;
  }

  // Priority 3: Legacy fallback
  return variant === 'inline' ? <LegacyInlineCTA {...rest} /> : <LegacyFinalCTA {...rest} />;
}
