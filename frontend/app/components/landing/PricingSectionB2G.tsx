'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { GradientButton } from '@/app/components/ui/GradientButton';
import { pricingB2G } from '@/lib/copy/b2gIntelCopy';
import { useLandingAnimation, fadeInUp, staggerContainer } from '@/lib/animations';

/**
 * REPO-COMMS #1289: Seção de Pricing — placeholder até REPO-TIER-COMMAND
 * Mostra tiers atuais, sem alterar lógica de billing
 *
 * Usa useLandingAnimation (scroll trigger + prefers-reduced-motion).
 */
export default function PricingSectionB2G() {
  const { ref, shouldAnimate } = useLandingAnimation();

  return (
    <section
      ref={ref}
      id={pricingB2G.sectionId}
      className="relative max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28"
    >
      <motion.div
        className="text-center mb-16"
        variants={staggerContainer}
        initial="hidden"
        animate={shouldAnimate ? 'visible' : 'hidden'}
      >
        <motion.h2
          className="text-3xl sm:text-4xl font-display font-bold tracking-tight text-[var(--ink)]"
          variants={fadeInUp}
        >
          {pricingB2G.headline}
        </motion.h2>
        <motion.p
          className="text-lg text-[var(--ink-secondary)] mt-4 max-w-xl mx-auto leading-relaxed"
          variants={fadeInUp}
        >
          {pricingB2G.subheadline}
        </motion.p>
      </motion.div>

      <motion.div
        className="flex flex-col items-center gap-6"
        variants={staggerContainer}
        initial="hidden"
        animate={shouldAnimate ? 'visible' : 'hidden'}
      >
        <motion.div variants={fadeInUp}>
          <Link href="/consultoria-b2g" data-testid="pricing-cta">
            <GradientButton variant="primary" size="lg" glow={true}>
              Ver planos
            </GradientButton>
          </Link>
        </motion.div>

        <motion.p
          className="text-xs text-[var(--ink-muted)] max-w-md text-center"
          variants={fadeInUp}
        >
          {pricingB2G.note}
        </motion.p>
      </motion.div>
    </section>
  );
}
