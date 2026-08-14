'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { GradientButton } from '@/app/components/ui/GradientButton';
import { b2gHero } from '@/lib/copy/b2gIntelCopy';
import { usePrefersReducedMotion } from '@/lib/animations';

/**
 * REPO-COMMS #1289: Hero B2G Intelligence
 * Headline fixa + 3 sub-headlines rotativas + CTA "Ver em ação"
 * Dark theme — terminal de inteligência, sem referências a IA/monitoramento/alerta
 *
 * WCAG 2.1: Respeita prefers-reduced-motion (desabilita animações quando usuário solicita).
 * Acessibilidade: sub-headline rotativa usa aria-live="polite" para leitores de tela.
 */
export default function HeroB2GIntel() {
  const [subIndex, setSubIndex] = useState(0);
  const prefersReducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    if (prefersReducedMotion) return;

    let timer: ReturnType<typeof setInterval> | null = null;

    const startRotation = () => {
      timer = setInterval(() => {
        setSubIndex((prev) => (prev + 1) % b2gHero.subheadlines.length);
      }, 4000);
    };

    const stopRotation = () => {
      if (timer) clearInterval(timer);
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopRotation();
      } else {
        startRotation();
      }
    };

    startRotation();
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      stopRotation();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [prefersReducedMotion]);

  const fadeProps = prefersReducedMotion
    ? {} // sem animação
    : {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.6 },
      };

  return (
    <section className="relative max-w-landing mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-20 sm:pt-32 sm:pb-28 overflow-hidden">
      {/* Background grid texture */}
      <div
        className="absolute inset-0 -z-10 opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(var(--border) 1px, transparent 1px), linear-gradient(90deg, var(--border) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      {prefersReducedMotion ? (
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto">
          {/* Static content for reduced motion */}
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface-1)] px-4 py-1.5 mb-8">
            <span className="w-2 h-2 rounded-full bg-[var(--success)]" />
            <span className="text-sm font-medium text-[var(--ink-secondary)] tracking-wide">
              INTELIGÊNCIA PÚBLICA B2G
            </span>
          </div>

          <h1
            className="text-4xl sm:text-5xl lg:text-6xl font-display font-black tracking-tighter leading-[1.1] text-[var(--ink)]"
            data-testid="hero-b2g-headline"
          >
            {b2gHero.headline}
          </h1>

          <div className="h-20 sm:h-16 flex items-center justify-center mt-6">
            <p
              className="text-lg sm:text-xl text-[var(--ink-secondary)] max-w-xl font-medium leading-relaxed"
              data-testid="hero-b2g-subheadline"
            >
              {b2gHero.subheadlines[subIndex]}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-4 mt-8">
            <Link href={b2gHero.cta.primaryHref} data-testid="hero-b2g-cta-primary">
              <GradientButton variant="primary" size="lg" glow={true}>
                {b2gHero.cta.primary}
              </GradientButton>
            </Link>
            <Link
              href={b2gHero.cta.secondaryHref}
              className="text-sm font-medium text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
              data-testid="hero-b2g-cta-secondary"
            >
              {b2gHero.cta.secondary} →
            </Link>
          </div>

          <p className="text-xs text-[var(--ink-muted)] mt-6">
            {b2gHero.trustLine}
          </p>
        </div>
      ) : (
        <motion.div
          className="flex flex-col items-center text-center max-w-3xl mx-auto"
          {...fadeProps}
        >
          {/* Kicker */}
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface-1)] px-4 py-1.5 mb-8">
            <span className="w-2 h-2 rounded-full bg-[var(--success)]" />
            <span className="text-sm font-medium text-[var(--ink-secondary)] tracking-wide">
              INTELIGÊNCIA PÚBLICA B2G
            </span>
          </div>

          {/* Headline */}
          <h1
            className="text-4xl sm:text-5xl lg:text-6xl font-display font-black tracking-tighter leading-[1.1] text-[var(--ink)]"
            data-testid="hero-b2g-headline"
          >
            {b2gHero.headline}
          </h1>

          {/* Rotating sub-headline — aria-live para screen readers */}
          <div
            className="h-20 sm:h-16 flex items-center justify-center mt-6"
            aria-live="polite"
            aria-atomic="true"
          >
            <AnimatePresence mode="wait">
              <motion.p
                key={subIndex}
                className="text-lg sm:text-xl text-[var(--ink-secondary)] max-w-xl font-medium leading-relaxed"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3 }}
                data-testid="hero-b2g-subheadline"
              >
                {b2gHero.subheadlines[subIndex]}
              </motion.p>
            </AnimatePresence>
          </div>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row items-center gap-4 mt-8">
            <Link href={b2gHero.cta.primaryHref} data-testid="hero-b2g-cta-primary">
              <GradientButton variant="primary" size="lg" glow={true}>
                {b2gHero.cta.primary}
              </GradientButton>
            </Link>
            <Link
              href={b2gHero.cta.secondaryHref}
              className="text-sm font-medium text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
              data-testid="hero-b2g-cta-secondary"
            >
              {b2gHero.cta.secondary} →
            </Link>
          </div>

          {/* Trust line — sourced from copy library */}
          <p className="text-xs text-[var(--ink-muted)] mt-6">
            {b2gHero.trustLine}
          </p>
        </motion.div>
      )}
    </section>
  );
}
