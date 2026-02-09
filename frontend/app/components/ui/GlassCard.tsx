'use client';

import { ReactNode } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  variant?: 'default' | 'subtle' | 'strong';
}

/**
 * STORY-174: Premium glassmorphism card component
 *
 * Features:
 * - Backdrop blur effect (glassmorphism)
 * - Gradient borders
 * - Hover lift animation (optional)
 * - Layered shadows for depth
 * - Variants for different intensities
 *
 * @example
 * <GlassCard hoverable={true} variant="default">
 *   <h3>Card Title</h3>
 *   <p>Card content</p>
 * </GlassCard>
 */
export function GlassCard({
  children,
  className = '',
  hoverable = true,
  variant = 'default'
}: GlassCardProps) {
  // Variant-specific styles
  const variantStyles = {
    default: 'bg-white/70 dark:bg-gray-800/70 border-white/20 dark:border-gray-700/30',
    subtle: 'bg-white/50 dark:bg-gray-800/50 border-white/10 dark:border-gray-700/20',
    strong: 'bg-white/90 dark:bg-gray-800/90 border-white/30 dark:border-gray-700/40',
  };

  const hoverAnimation: HTMLMotionProps<'div'>['whileHover'] = hoverable ? {
    y: -8,
    scale: 1.02,
    boxShadow: 'var(--shadow-xl)',
  } : undefined;

  return (
    <motion.div
      className={`
        backdrop-blur-md
        ${variantStyles[variant]}
        border
        rounded-3xl
        p-8
        shadow-glass
        transition-shadow
        duration-300
        ${hoverable ? 'cursor-pointer' : ''}
        ${className}
      `}
      whileHover={hoverAnimation}
      transition={{
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1], // cubic-bezier(0.4, 0, 0.2, 1)
      }}
    >
      {children}
    </motion.div>
  );
}
