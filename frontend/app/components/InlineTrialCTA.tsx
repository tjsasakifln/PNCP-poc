'use client';

import Link from 'next/link';

interface Props {
  /** Mixpanel `page` property (e.g. 'cnpj', 'orgao') */
  page: 'cnpj' | 'orgao';
  /**
   * Tracked source on the consultoria URL (e.g. 'cnpj-page', 'orgao-page').
   * Becomes `?source=<source>` and is the primary attribution vector.
   */
  source: string;
  /**
   * Optional extra query param appended after `source`.
   * For `/cnpj/[cnpj]` use `{ orgao: cnpj }`; for `/orgaos/[slug]` use `{ slug }`.
   */
  extraParam?: { name: string; value: string };
}

/**
 * Inline CONFENGE CTA on programmatic SEO pages (/cnpj/[cnpj], /orgaos/[slug]).
 * Complementary, NOT a paywall — content above remains fully accessible.
 */
export default function InlineTrialCTA({ page, source, extraParam }: Props) {
  const params = new URLSearchParams({ source });
  if (extraParam) {
    params.set(extraParam.name, extraParam.value);
  }
  const href = `/consultoria-b2g?${params.toString()}`;

  const handleClick = () => {
    if (typeof window !== 'undefined' && window.mixpanel) {
      window.mixpanel.track('cta_click', { page, position: 'inline' });
    }
  };

  return (
    <section
      aria-label="Diagnóstico CONFENGE"
      className="my-10 rounded-xl border border-blue-200 bg-blue-50 p-6 text-center sm:p-8"
    >
      <h2 className="text-xl font-bold text-gray-900 sm:text-2xl">
        Monitore contratos deste órgão — diagnóstico CONFENGE
      </h2>
      <p className="mx-auto mt-2 max-w-xl text-sm text-gray-600 sm:text-base">
        A CONFENGE interpreta o dado público e opera a decisão comercial. Sem conta. Sem trial.
      </p>
      <Link
        href={href}
        onClick={handleClick}
        className="mt-5 inline-block rounded-xl bg-green-600 px-8 py-3 text-center font-bold text-white shadow-lg transition-colors hover:bg-green-700 sm:w-auto"
      >
        Pedir um diagnóstico à CONFENGE →
      </Link>
    </section>
  );
}
