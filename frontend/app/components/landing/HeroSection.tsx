'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Zap, Target, Globe, ChevronDown } from 'lucide-react';
import { GradientButton } from '@/app/components/ui/GradientButton';
import { GlassCard } from '@/app/components/ui/GlassCard';
import { useScrollAnimation } from '@/lib/animations';
import { fadeInUp, staggerContainer, scaleIn } from '@/lib/animations';

interface HeroSectionProps {
  className?: string;
}

/**
 * STORY-174 AC1: Hero Section Redesign - Premium SaaS Aesthetic
 *
 * Features:
 * - Gradient text headline (background-clip: text)
 * - Animated CTAs (gradient + glow effect)
 * - Glassmorphism stats badges with counter animation
 * - Subtle gradient mesh background
 * - Scroll-triggered animations (fade-in + slide-up)
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
        py-20 sm:py-32
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
            Saiba Onde Investir
          </span>
          <br />
          <span className="text-gradient">
            para Ganhar Mais Licitações
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
          Inteligência que avalia oportunidades, prioriza o que importa
          <br className="hidden sm:block" />
          e guia suas decisões. Avaliação objetiva, não busca genérica.
        </motion.p>

        {/* CTA Buttons */}
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
            Descobrir minhas oportunidades
          </GradientButton>

          {/* Secondary CTA with border fill animation */}
          <GradientButton
            variant="secondary"
            size="lg"
            glow={false}
            onClick={() => scrollToSection('como-funciona')}
          >
            Como funciona
            <ChevronDown size={20} className="ml-2 transition-transform" aria-hidden="true" />
          </GradientButton>
        </motion.div>

        {/* Stats badges with glassmorphism */}
        <motion.div
          className="mt-12 flex flex-wrap items-center justify-center gap-4"
          variants={fadeInUp}
        >
          <StatsBadge icon={Target} value="15" label="setores especializados" delay={0} />
          <StatsBadge icon={Zap} value="1000+" label="regras de filtragem" delay={0.1} />
          <StatsBadge icon={Globe} value="27" label="estados cobertos" delay={0.2} />
        </motion.div>
      </motion.div>
    </section>
  );
}

/**
 * Stats Badge Component - Glassmorphism card with counter animation
 */
interface StatsBadgeProps {
  icon: React.ComponentType<any> | string; // Lucide component or legacy emoji string
  value: string;
  label: string;
  delay: number;
}

function StatsBadge({ icon, value, label, delay }: StatsBadgeProps) {
  const { ref, isVisible } = useScrollAnimation(0.1);
  const [count, setCount] = useState(0);

  // Counter animation for numbers
  useEffect(() => {
    if (!isVisible) return;

    // Extract numeric part from value (e.g., "160x" -> 160, "95%" -> 95)
    const numericValue = parseInt(value.match(/\d+/)?.[0] || '0');

    if (numericValue === 0) return;

    const duration = 1000; // 1 second
    const steps = 30;
    const increment = numericValue / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= numericValue) {
        setCount(numericValue);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [isVisible, value]);

  // Format value with counter
  const displayValue = value.includes('%')
    ? `${count}%`
    : value.includes('x')
    ? `${count}x`
    : value.includes('+')
    ? value // Keep original value as is
    : `${count}`;

  // Determine if icon is a component or string emoji (backward compatibility)
  const isComponent = typeof icon !== 'string';
  const IconComponent = isComponent ? (icon as React.ComponentType<any>) : null;

  return (
    <motion.div ref={ref} variants={scaleIn} transition={{ delay }}>
      <GlassCard
        hoverable={true}
        variant="subtle"
        className="
          group
          inline-flex
          items-center
          gap-2
          px-4
          py-2
          rounded-full
          text-sm
          min-w-[140px]
          justify-center
          cursor-default
        "
      >
        {isComponent && IconComponent ? (
          <IconComponent
            className={`
              w-6 h-6 flex-shrink-0
              text-brand-blue
              transition-all duration-300
              group-hover:scale-110
              ${label.includes('Rápido') ? 'group-hover:rotate-6' : ''}
              ${label.includes('Precisão') ? 'group-hover:scale-125' : ''}
              ${label.includes('Portais') ? 'group-hover:-rotate-6' : ''}
            `}
            strokeWidth={2}
            aria-label={label}
            role="img"
          />
        ) : (
          <span className="text-lg" role="img" aria-label={label}>
            {icon as string}
          </span>
        )}
        <div className="flex flex-col items-start">
          <span className="text-ink font-bold tabular-nums">
            {displayValue}
          </span>
          <span className="text-ink-muted text-xs font-medium">
            {label}
          </span>
        </div>
      </GlassCard>
    </motion.div>
  );
}
