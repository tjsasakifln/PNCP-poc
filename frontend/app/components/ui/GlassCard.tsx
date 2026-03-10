'use client';

import { ReactNode } from 'react';

type GlassVariant = 'default' | 'subtle' | 'strong' | 'result' | 'pricing' | 'feature';
type GemAccent = 'sapphire' | 'emerald' | 'amethyst' | 'ruby';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  variant?: GlassVariant;
  gemAccent?: GemAccent;
  role?: string;
  'aria-label'?: string;
}

const variantStyles: Record<GlassVariant, string> = {
  default: 'backdrop-blur-md bg-white/70 dark:bg-gray-800/70 border-white/20 dark:border-gray-700/30',
  subtle: 'backdrop-blur-md bg-white/50 dark:bg-gray-800/50 border-white/10 dark:border-gray-700/20',
  strong: 'backdrop-blur-md bg-white/90 dark:bg-gray-800/90 border-white/30 dark:border-gray-700/40',
  result: 'backdrop-blur-lg bg-white/60 dark:bg-gray-900/50 border-white/20 dark:border-white/10',
  pricing: 'backdrop-blur-xl bg-white/50 dark:bg-gray-900/40 border-white/25 dark:border-white/15',
  feature: 'backdrop-blur-md bg-gradient-to-br from-white/60 to-white/30 dark:from-gray-800/60 dark:to-gray-900/30 border-white/20 dark:border-gray-700/30',
};

const gemShadowClass: Record<GemAccent, string> = {
  sapphire: 'shadow-gem-sapphire',
  emerald: 'shadow-gem-emerald',
  amethyst: 'shadow-gem-amethyst',
  ruby: 'shadow-gem-ruby',
};

/**
 * GTM-006: Premium glassmorphism card component with gem accents
 *
 * Variants (by glass intensity):
 *   subtle < default < result < pricing < feature (gradient)
 *
 * Gem accents apply colored shadows for contextual meaning:
 *   sapphire = action/CTA, emerald = success, amethyst = premium, ruby = urgency
 */
export function GlassCard({
  children,
  className = '',
  hoverable = true,
  variant = 'default',
  gemAccent,
  role,
  'aria-label': ariaLabel,
}: GlassCardProps) {
  return (
    <div
      className={`
        ${variantStyles[variant]}
        border
        rounded-3xl
        p-8
        shadow-glass
        transition-all
        duration-300
        ease-[cubic-bezier(0.4,0,0.2,1)]
        ${hoverable ? 'hover:-translate-y-2 hover:scale-[1.02] hover:shadow-xl cursor-pointer' : ''}
        ${gemAccent ? gemShadowClass[gemAccent] : ''}
        ${className}
      `}
      role={role}
      aria-label={ariaLabel}
    >
      {children}
    </div>
  );
}
