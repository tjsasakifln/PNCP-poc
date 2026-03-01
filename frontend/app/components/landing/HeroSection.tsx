'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { GradientButton } from '@/app/components/ui/GradientButton';
import { useScrollAnimation } from '@/lib/animations';
import { fadeInUp, staggerContainer } from '@/lib/animations';

interface HeroSectionProps {
  className?: string;
}

/**
 * STORY-174 AC1: Hero Section Redesign - Premium SaaS Aesthetic
 * SAB-006 AC2/AC5: Removed stats badges (consolidated into StatsSection), CTA above fold
 */
export default function HeroSection({ className = '' }: HeroSectionProps) {
  const { ref, isVisible } = useScrollAnimation(0.1);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <section
      ref={ref}
      className={`
        relative
        max-w-landing
        mx-auto
        px-4 sm:px-6 lg:px-8
        py-16 sm:py-24
        overflow-hidden
        ${className}
      `}
    >
      {/* Background gradient mesh */}
      <div
        className="absolute inset-0 -z-10 opacity-40"
        style={{
          background: `
            radial-gradient(circle at 20% 50%, var(--brand-blue-subtle) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, var(--brand-blue-subtle) 0%, transparent 40%)
          `,
        }}
      />

      <motion.div
        className="text-center max-w-4xl mx-auto"
        variants={staggerContainer}
        initial="hidden"
        animate={isVisible ? 'visible' : 'hidden'}
      >
        {/* Headline with gradient text */}
        <motion.h1
          className="
            text-4xl sm:text-5xl lg:text-6xl
            font-display
            font-black
            tracking-tighter
            leading-[1.1]
          "
          variants={fadeInUp}
        >
          <span className="text-ink">
            Pare de perder dinheiro
          </span>
          <br />
          <span className="text-gradient">
            com licitações erradas.
          </span>
        </motion.h1>

        {/* Subheadline with delayed fade-in */}
        <motion.p
          className="
            text-lg sm:text-xl
            text-ink-secondary
            mt-6
            font-medium
            leading-relaxed
            max-w-2xl
            mx-auto
          "
          variants={fadeInUp}
        >
          O SmartLic analisa cada edital contra o perfil da sua empresa. Elimina o que não faz sentido. Entrega só o que tem chance real de retorno — com justificativa objetiva.
        </motion.p>

        {/* CTA Buttons — AC5: Primary CTA visible above the fold */}
        <motion.div
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10"
          variants={fadeInUp}
        >
          {/* Primary CTA with gradient + glow */}
          <GradientButton
            variant="primary"
            size="lg"
            glow={true}
            onClick={() => window.location.href = '/signup?source=landing-cta'}
          >
            Ver oportunidades para meu setor
          </GradientButton>

          {/* Secondary CTA — scroll to Como Funciona */}
          <GradientButton
            variant="secondary"
            size="lg"
            glow={false}
            onClick={() => scrollToSection('como-funciona')}
          >
            Ver como funciona
            <ChevronDown size={20} className="ml-2 transition-transform" aria-hidden="true" />
          </GradientButton>
        </motion.div>

        {/* AC7: Trust indicators */}
        <motion.div
          className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-ink-muted"
          variants={fadeInUp}
        >
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Fontes oficiais verificadas
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Critérios objetivos, não opinião
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Sem dados fabricados
          </span>
        </motion.div>
      </motion.div>
    </section>
  );
}
