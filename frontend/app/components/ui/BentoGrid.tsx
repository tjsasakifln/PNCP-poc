'use client';

import { ReactNode } from 'react';

interface BentoGridProps {
  children: ReactNode;
  variant?: 'default' | 'compact' | 'wide';
  className?: string;
}

/**
 * STORY-174: Bento grid layout component (asymmetric grid)
 *
 * Features:
 * - Responsive asymmetric grid layout
 * - Desktop: 4-column complex grid with varied sizes
 * - Tablet: 2-column simplified grid
 * - Mobile: Single column stack
 * - Variants for different layouts
 *
 * Usage:
 * Wrap child elements with this grid. Children can use Tailwind's
 * col-span and row-span utilities for asymmetric sizing.
 *
 * @example
 * <BentoGrid>
 *   <GlassCard className="lg:col-span-2 lg:row-span-2">Large</GlassCard>
 *   <GlassCard className="lg:col-span-1">Medium</GlassCard>
 *   <GlassCard className="lg:col-span-1">Medium</GlassCard>
 *   <GlassCard className="lg:col-span-4">Full width</GlassCard>
 * </BentoGrid>
 */
export function BentoGrid({
  children,
  variant = 'default',
  className = ''
}: BentoGridProps) {
  // Variant-specific grid configurations
  const variantStyles = {
    // Standard bento grid: 4 columns, auto rows
    default: `
      grid-cols-1
      md:grid-cols-2
      lg:grid-cols-4
      lg:auto-rows-fr
      gap-6
      lg:gap-6
    `,
    // Compact: tighter spacing
    compact: `
      grid-cols-1
      md:grid-cols-2
      lg:grid-cols-4
      lg:auto-rows-fr
      gap-4
      lg:gap-4
    `,
    // Wide: more horizontal space
    wide: `
      grid-cols-1
      md:grid-cols-3
      lg:grid-cols-6
      lg:auto-rows-fr
      gap-6
      lg:gap-8
    `,
  };

  return (
    <div
      className={`
        grid
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

/**
 * BentoGridItem - Helper component for grid items with predefined sizes
 */
interface BentoGridItemProps {
  children: ReactNode;
  size?: 'small' | 'medium' | 'large' | 'wide' | 'tall' | 'hero';
  className?: string;
}

export function BentoGridItem({
  children,
  size = 'medium',
  className = ''
}: BentoGridItemProps) {
  // Predefined size configurations
  const sizeStyles = {
    small: 'lg:col-span-1 lg:row-span-1',       // 1x1
    medium: 'lg:col-span-2 lg:row-span-1',      // 2x1
    large: 'lg:col-span-2 lg:row-span-2',       // 2x2
    wide: 'lg:col-span-3 lg:row-span-1',        // 3x1
    tall: 'lg:col-span-1 lg:row-span-2',        // 1x2
    hero: 'lg:col-span-4 lg:row-span-2',        // 4x2 (full width, double height)
  };

  return (
    <div className={`${sizeStyles[size]} ${className}`}>
      {children}
    </div>
  );
}
