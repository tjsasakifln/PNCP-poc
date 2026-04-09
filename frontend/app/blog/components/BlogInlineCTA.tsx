import Link from 'next/link';

/**
 * MKT-001 AC3: Inline CTA inserted at ~40% of blog post content.
 *
 * Standardized inline CTA: "Teste grátis 14 dias — sem cartão de crédito"
 * UTM: utm_source=blog&utm_medium=cta&utm_content=[slug]
 */

interface BlogInlineCTAProps {
  slug: string;
  campaign?: 'b2g' | 'consultorias' | 'guias' | 'contratos';
  ctaHref?: string;
  ctaText?: string;
  ctaMessage?: string;
}

export default function BlogInlineCTA({
  slug,
  campaign = 'b2g',
  ctaHref,
  ctaText,
  ctaMessage,
}: BlogInlineCTAProps) {
  const defaultHref = `/signup?source=blog&article=${slug}&utm_source=blog&utm_medium=cta&utm_content=${slug}&utm_campaign=${campaign}`;
  const href = ctaHref
    ? `${ctaHref}?utm_source=blog&utm_medium=cta&utm_content=${slug}&utm_campaign=${campaign}`
    : defaultHref;

  return (
    <div className="not-prose my-8 sm:my-10 bg-brand-blue-subtle/50 dark:bg-brand-navy/10 rounded-lg p-4 sm:p-5 border border-brand-blue/15 flex flex-col sm:flex-row items-center gap-3 sm:gap-4">
      <p className="text-sm sm:text-base text-ink font-medium text-center sm:text-left flex-1">
        {ctaMessage || 'Teste grátis 14 dias \u2014 sem cartão de crédito'}
      </p>
      <Link
        href={href}
        className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2 rounded-button text-sm transition-all hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap"
      >
        {ctaText || 'Comece Agora'}
      </Link>
    </div>
  );
}
