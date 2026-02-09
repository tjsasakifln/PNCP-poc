'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
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
            Encontre Oportunidades Relevantes
          </span>
          <br />
          <span className="text-gradient">
            em 3 Minutos, Não em 8 Horas
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
          Algoritmos inteligentes filtram milhares de licitações de múltiplas fontes
          <br className="hidden sm:block" />
          para entregar apenas o que importa para o seu negócio.
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
            Economize 10h/Semana Agora
          </GradientButton>

          {/* Secondary CTA with border fill animation */}
          <GradientButton
            variant="secondary"
            size="lg"
            glow={false}
            onClick={() => scrollToSection('como-funciona')}
          >
            Como funciona
            <svg
              role="img"
              aria-label="Ícone"
              className="w-4 h-4 ml-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </GradientButton>
        </motion.div>

        {/* Stats badges with glassmorphism */}
        <motion.div
          className="mt-12 flex flex-wrap items-center justify-center gap-4"
          variants={fadeInUp}
        >
          <StatsBadge icon="⚡" value="160x" label="Mais Rápido" delay={0} />
          <StatsBadge icon="🎯" value="95%" label="de Precisão" delay={0.1} />
          <StatsBadge icon="🌍" value="PNCP + 27" label="Portais" delay={0.2} />
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
    ? value // Keep "PNCP + 27" as is
    : `${count}`;

  // Determine if icon is a component or string emoji (backward compatibility)
  const isComponent = typeof icon === 'function';

  return (
    <motion.div ref={ref} variants={scaleIn} transition={{ delay }}>
      <GlassCard
        hoverable={true}
        variant="subtle"
        className="
          inline-flex
          items-center
          gap-2
          px-4
          py-2
          rounded-full
          text-sm
          min-w-[140px]
          justify-center
        "
      >
        {isComponent ? (
          React.createElement(icon as React.ComponentType<any>, {
            className: 'w-5 h-5 text-brand-blue flex-shrink-0',
            strokeWidth: 2,
            'aria-label': label,
            role: 'img',
          })
        ) : (
          <span className="text-lg" role="img" aria-label={label}>
            {icon}
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
