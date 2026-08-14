'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { SECTORS } from '@/lib/sectors';
import { UF_NAMES } from '@/lib/programmatic';

interface SeoBannerCtaProps {
  setor: string;
  uf?: string;
}

/**
 * SeoBannerCta — Banner CTA for SEO programmatic pages.
 *
 * COPY-COP-006 (#1127): Shows a contextual banner on SEO pages
 * inviting non-authenticated users to sign up.
 *
 * Template: "Buscando editais de {SETOR} em {UF}?
 *            O SmartLic encontra automaticamente para você."
 *
 * Only renders for non-authenticated users.
 */
export default function SeoBannerCta({ setor, uf }: SeoBannerCtaProps) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        setIsAuthenticated(!!session?.user);
      } catch {
        setIsAuthenticated(false);
      }
    };
    checkAuth();
  }, []);

  // Don't render while checking auth (avoid flash)
  // Don't render for authenticated users
  if (isAuthenticated === null || isAuthenticated) return null;

  const sector = SECTORS.find(
    (s) => s.slug === setor || s.id === setor,
  );
  const sectorName = sector?.name || setor;

  let heading: string;
  if (uf && UF_NAMES[uf.toUpperCase()]) {
    heading = `Buscando editais de ${sectorName} em ${UF_NAMES[uf.toUpperCase()]}?`;
  } else {
    heading = `Buscando editais de ${sectorName}?`;
  }

  const ctaLabel = uf
    ? `Ver editais de ${sectorName} em ${UF_NAMES[uf.toUpperCase()]}`
    : `Ver oportunidades do meu setor`;

  const utmSource = uf
    ? `seo-banner-${setor}-${uf.toLowerCase()}`
    : `seo-banner-${setor}`;

  return (
    <section className="max-w-5xl mx-auto px-4 py-8">
      <div className="rounded-xl bg-gradient-to-br from-brand-navy to-brand-blue p-6 sm:p-8 text-white">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-lg sm:text-xl font-bold mb-1">{heading}</h3>
            <p className="text-white/80 text-sm">
              O SmartLic encontra automaticamente para você. Análise com IA, score de
              viabilidade e alertas por email.
            </p>
          </div>
          <Link
            href={`/consultoria-b2g?source=${utmSource}`}
            className="inline-flex items-center px-6 py-3 bg-white text-brand-navy font-bold
                       rounded-lg hover:bg-gray-100 transition-colors whitespace-nowrap text-sm"
          >
            {ctaLabel} →
          </Link>
        </div>
        <p className="mt-3 text-xs text-white/60">
          sem login, dado verificável. Resultado em 3 minutos.
        </p>
      </div>
    </section>
  );
}
