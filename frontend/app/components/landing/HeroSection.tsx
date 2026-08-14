'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { GradientButton } from '@/app/components/ui/GradientButton';
import { useScrollAnimation } from '@/lib/animations';
import { fadeInUp, staggerContainer } from '@/lib/animations';
import { hero } from '@/lib/copy/valueProps';
import { trackCTAClick } from '@/lib/analytics-events';
import HeroFounderStrip from './HeroFounderStrip';
import HeroTrustSignals from './HeroTrustSignals';
import FundadoresCountdown from './FundadoresCountdown';
import LoomPlaceholder from './LoomPlaceholder';

interface HeroSectionProps {
  className?: string;
}

const HERO_SCREENSHOT_BLUR =
  'data:image/webp;base64,UklGRk4AAABXRUJQVlA4IEIAAADQAgCdASoUAA0ALvmczmclLy8vDwD4SzgGWWK505WAAP7wLrgqjz50IhRgDbeGwhDdH55pOuyAD9i3oi0FuVjIAAA=';

/**
 * STORY-174 AC1: Hero Section Redesign - Premium SaaS Aesthetic
 * SAB-006 AC2/AC5: Removed stats badges (consolidated into StatsSection), CTA above fold
 * DEBT-125: 50/50 layout with annotated product screenshot
 * REPO-006: Copymasters consensus v1 — B2G intelligence positioning
 * REPO-007: Founding disclaimer below CTAs
 * COPY-LANDING-004 (#1003): Beachhead anti-assessor + trust signals 2026
 *  - V1 headline: "Pare de pagar R$3.000/mês ao assessor que copia o PNCP"
 *  - CTA primário: "Pedir um diagnóstico à CONFENGE →" + sub "Sem cartão. Cancele em 1 clique."
 *  - CTA secundário: ancoragem Plano Fundadores R$997
 *  - Founder-led visível: nome + cargo + LinkedIn (Schema.org Person já em StructuredData.tsx)
 *  - Trust signals 2026: founder + changelog + roadmap + 60d garantia (substitui "Sem dados fabricados")
 *
 * Sub-componentes (refactor estrutural #1017 — LOC gate):
 *  - HeroFounderStrip: avatar + nome + cargo + LinkedIn
 *  - HeroTrustSignals: 4 trust signals 2026
 */
export default function HeroSection({ className = '' }: HeroSectionProps) {
  const { ref, isVisible } = useScrollAnimation(0.1);

  return (
    <section
      ref={ref}
      className={`
        relative
        max-w-landing
        mx-auto
        px-4 sm:px-6 lg:px-8
        py-20 sm:py-28
        overflow-hidden
        ${className}
      `}
    >
      {/* Background gradient mesh */}
      {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: radial-gradient uses CSS custom properties (--brand-blue-subtle) not expressible in Tailwind */}
      <div
        className="absolute inset-0 -z-10 opacity-40"
        style={{
          background: `
            radial-gradient(circle at 20% 50%, var(--brand-blue-subtle) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, var(--brand-blue-subtle) 0%, transparent 40%)
          `,
        }}
      />

      {/* DEBT-125: 50/50 layout — text left, screenshot right (desktop) / stacked (mobile) */}
      <motion.div
        className="flex flex-col lg:flex-row items-center gap-12 lg:gap-16"
        variants={staggerContainer}
        initial="hidden"
        animate={isVisible ? 'visible' : 'hidden'}
      >
        {/* Left column — text content */}
        <div className="flex-1 text-center lg:text-left max-w-xl lg:max-w-none">
          {/* COPY-COP-004 (#1125): Beta badge — transparency badge before headline */}
          <motion.div
            className="inline-flex items-center gap-1.5 rounded-full border border-amber-300/50 bg-amber-50 dark:bg-amber-900/20 px-3 py-1 mb-4"
            variants={fadeInUp}
            data-testid="hero-beta-badge"
          >
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span className="text-xs font-semibold text-amber-700 dark:text-amber-300 tracking-wide uppercase">
              Beta
            </span>
          </motion.div>

          {/* Cialdini AC3 — Scarcity: Fundadores Countdown */}
          <FundadoresCountdown />

          {/* COPY-COP-002: Variante C — híbrida SEO-aware */}
          <motion.h1
            className="
              text-4xl sm:text-5xl lg:text-7xl
              font-display
              font-black
              tracking-tighter
              leading-[1.1]
            "
            variants={fadeInUp}
            data-testid="hero-headline"
          >
            <span className="text-ink">
              Máquina de receita previsível
            </span>{' '}
            <span className="text-gradient">
              para empresas B2G.
            </span>
          </motion.h1>

          {/* COPY-COP-002: Subtítulo — filtragem inteligente, elimina ruído */}
          <motion.p
            className="
              text-xl sm:text-2xl
              text-ink-secondary
              mt-6
              font-medium
              leading-relaxed
              max-w-2xl
              lg:max-w-lg
            "
            variants={fadeInUp}
            data-testid="hero-subheadline"
          >
            Veja editais que sua empresa perderia — e os que ela pode vencer.
          </motion.p>

          {/* Cialdini AC2 — Microcompromisso: baixo risco antes do CTA */}
          <motion.p
            className="text-sm text-ink-muted mt-8 mb-2 text-center lg:text-left"
            variants={fadeInUp}
            data-testid="hero-microcompromisso"
          >
            Consulta pública, sem login. A CONFENGE opera a decisão.
          </motion.p>

          {/* COPY-COP-005: Consistência — Microcompromisso antes do CTA principal */}
          <motion.div
            className="mt-6 text-center lg:text-left"
            variants={fadeInUp}
          >
            <Link
              href="/consultoria-b2g?source=hero-preview"
              className="text-sm text-brand-blue hover:text-brand-blue-hover underline-offset-2 hover:underline transition-colors"
              data-testid="hero-micro-commitment"
            >
              Quer saber quantos editais do seu setor est&atilde;o abertos agora?{' '}
              <span className="font-semibold whitespace-nowrap">Ver quantidade &rarr;</span>
            </Link>
          </motion.div>

          {/* CTA Buttons — AC5: Primary CTA visible above the fold */}
          <motion.div
            className="flex flex-col sm:flex-row items-center lg:items-start justify-center lg:justify-start gap-4 mt-6"
            variants={fadeInUp}
          >
            <div className="flex flex-col items-center lg:items-start gap-1">
              <Link
                href={hero.cta.primaryHref}
                data-testid="hero-cta-primary"
                onClick={() =>
                  trackCTAClick({
                    label: 'hero-primary',
                    source: 'hero',
                    destination: hero.cta.primaryHref,
                    cta_type: 'self-service',
                  })
                }
              >
                <GradientButton
                  variant="primary"
                  size="lg"
                  glow={true}
                >
                  {hero.cta.primary}
                </GradientButton>
              </Link>
              <span
                className="text-xs text-ink-muted"
                data-testid="hero-cta-primary-subtext"
              >
                {hero.cta.primarySubtext}
              </span>
            </div>

            <Link href={hero.cta.secondaryHref} data-testid="hero-cta-secondary">
              <GradientButton
                variant="secondary"
                size="lg"
                glow={false}
              >
                {hero.cta.secondary}
              </GradientButton>
            </Link>
          </motion.div>

          {/* COPY-COP-005: Escassez — Countdown Fundadores visível acima da dobra */}
          <motion.div
            className="mt-5 flex items-center justify-center lg:justify-start"
            variants={fadeInUp}
            data-testid="hero-scarcity-countdown"
          >
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-300/50 bg-amber-50 dark:bg-amber-900/20 px-3 py-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
              <span className="text-xs font-medium text-amber-700 dark:text-amber-300">
                Vagas do Plano Fundadores se encerram em 30/06 — <span className="font-bold">R$997 vitalício</span>
              </span>
            </span>
          </motion.div>

          {/* COPY-COP-003: Trust stats line — dados reais do datalink */}
          <motion.div
            className="mt-3 text-sm text-ink-muted text-center lg:text-left"
            variants={fadeInUp}
            data-testid="hero-trust-stats"
          >
            +2 milh&otilde;es de contratos monitorados &bull; 27 estados &bull; 15 setores
          </motion.div>

          <HeroFounderStrip />
          <HeroTrustSignals />

          {/* Cialdini AC5 — Liking/Video: Loom product tour placeholder */}
          <LoomPlaceholder />
        </div>

        {/* Right column — annotated product screenshot (DEBT-125 AC1-AC8) */}
        <motion.div
          className="flex-1 w-full lg:w-auto"
          variants={fadeInUp}
        >
          <div className="relative w-full max-w-2xl mx-auto lg:mx-0">
            {/* Browser chrome frame */}
            <div className="rounded-xl overflow-hidden shadow-xl ring-1 ring-black/5 dark:ring-white/10 dark:shadow-2xl">
              {/* Browser bar */}
              <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <div className="flex gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-red-400" />
                  <span className="w-3 h-3 rounded-full bg-yellow-400" />
                  <span className="w-3 h-3 rounded-full bg-green-400" />
                </div>
                <div className="flex-1 mx-4">
                  <div className="bg-white dark:bg-gray-700 rounded-md px-3 py-1 text-xs text-gray-500 dark:text-gray-400 text-center truncate">
                    smartlic.tech/buscar
                  </div>
                </div>
              </div>

              {/* Screenshot image — AC5: priority for LCP, AC6: descriptive alt, AC8: dark mode filter */}
              <Image
                src="/images/hero-screenshot.webp"
                alt="Tela de resultados do SmartLic mostrando classificacao por IA e analise de viabilidade"
                width={1280}
                height={800}
                priority={true}
                sizes="(max-width: 1024px) 100vw, 50vw"
                placeholder="blur"
                blurDataURL={HERO_SCREENSHOT_BLUR}
                className="w-full h-auto dark:brightness-[0.85] dark:contrast-[1.1]"
              />
            </div>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}
