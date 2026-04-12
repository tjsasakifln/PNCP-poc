import Link from 'next/link';
import { getUfPrep } from '@/lib/programmatic';

/**
 * MKT-002 AC6: Contextual CTA component for programmatic SEO pages.
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
}

function buildHref(slug: string): string {
  return `/signup?source=blog&utm_source=blog&utm_medium=programmatic&utm_content=${encodeURIComponent(slug)}`;
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

  parts.push('teste grátis 14 dias');
  return parts.join(' — ');
}

function InlineCTA({ setor, uf, ufCode, count, slug }: Omit<BlogCTAProps, 'variant'>) {
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

function FinalCTA({ setor, uf, ufCode, count, slug }: Omit<BlogCTAProps, 'variant'>) {
  const href = buildHref(slug);
  const prep = uf ? ` ${getUfPrep(ufCode)} ${uf}` : '';

  return (
    <div className="not-prose mt-12 mb-8 bg-gradient-to-br from-brand-navy to-brand-blue rounded-xl p-6 sm:p-8 text-white text-center">
      <h3 className="text-xl sm:text-2xl font-bold mb-3">
        {count && count > 0
          ? `${count} licitações${setor ? ` de ${setor}` : ''}${prep} esperando sua análise`
          : `Licitações${setor ? ` de ${setor}` : ''}${prep} esperando sua análise`}
      </h3>
      <p className="text-white/80 mb-6 max-w-xl mx-auto">
        Filtre por viabilidade real, receba alertas automáticos e exporte relatórios.
        Teste grátis 14 dias — sem cartão de crédito.
      </p>
      <Link
        href={href}
        className="inline-block bg-white text-brand-navy font-semibold px-6 py-3 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98]"
      >
        Começar Teste Grátis
      </Link>
    </div>
  );
}

export default function BlogCTA({ variant, ...rest }: BlogCTAProps) {
  return variant === 'inline' ? <InlineCTA {...rest} /> : <FinalCTA {...rest} />;
}
