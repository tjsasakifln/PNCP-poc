/**
 * SmartLic Icon System - Lucide React
 *
 * Centralized icon exports for consistent usage across the application.
 * All icons are from Lucide (MIT License) - premium SaaS aesthetic.
 *
 * @see https://lucide.dev
 * @agent @dev (Felix) + @ux-design-expert (Uma)
 * @date 2026-02-09
 */

// ============================================================================
// CORE ICON EXPORTS
// ============================================================================

export {
  Zap,           // ⚡ Lightning/Speed
  Target,        // 🎯 Precision
  Globe,         // 🌍 Coverage/Multi-source
  Bot,           // 🤖 AI/Intelligence
  Search,        // 🔍 Search/Discovery
  CircleDollarSign, // 💰 Pricing
  CheckCircle2,  // ✅ Check/Approval
  LifeBuoy,      // 🛟 Support
  Sparkles,      // ✨ Interface/UX
  ShieldCheck,   // 🛡️ Security/Stability
} from 'lucide-react';

// ============================================================================
// ICON WRAPPER COMPONENT (Optional - for advanced customization)
// ============================================================================

import { LucideProps } from 'lucide-react';
import React from 'react';

export interface IconProps extends LucideProps {
  /**
   * Visual variant for color theming
   */
  variant?: 'primary' | 'success' | 'muted' | 'gradient';

  /**
   * Accessibility label (required for icon-only elements)
   */
  label?: string;
}

/**
 * Icon Wrapper Component
 *
 * Provides consistent styling and accessibility for Lucide icons.
 * Use this when you need variant-based coloring or aria-labels.
 *
 * @example
 * ```tsx
 * <Icon
 *   icon={Zap}
 *   variant="primary"
 *   label="160x faster speed"
 *   className="w-6 h-6"
 * />
 * ```
 */
export const Icon: React.FC<
  IconProps & { icon: React.ComponentType<LucideProps> }
> = ({ icon: IconComponent, variant = 'primary', label, className = '', ...props }) => {
  const variantClasses = {
    primary: 'text-brand-blue',
    success: 'text-success',
    muted: 'text-ink-muted',
    gradient: 'text-gradient',
  };

  return (
    <IconComponent
      className={`${variantClasses[variant]} ${className}`}
      aria-label={label}
      role={label ? 'img' : undefined}
      {...props}
    />
  );
};

// ============================================================================
// DESIGN SYSTEM CONSTANTS
// ============================================================================

/**
 * Standard icon sizes for consistent usage
 */
export const ICON_SIZES = {
  xs: 'w-3 h-3',      // 12px - inline text
  sm: 'w-4 h-4',      // 16px - small buttons
  md: 'w-5 h-5',      // 20px - default (comparison table)
  lg: 'w-6 h-6',      // 24px - hero stats badges
  xl: 'w-8 h-8',      // 32px - value prop cards
  '2xl': 'w-10 h-10', // 40px - large featured elements
} as const;

/**
 * Standard stroke widths for visual hierarchy
 */
export const STROKE_WIDTHS = {
  thin: 1.5,    // Subtle, secondary elements
  normal: 2,    // Default (most icons)
  thick: 2.5,   // Emphasis, hover states
} as const;

// ============================================================================
// USAGE GUIDELINES
// ============================================================================

/**
 * Icon Usage Patterns:
 *
 * 1. **Hero Stats Badges** (large, prominent)
 *    - Size: lg (w-6 h-6)
 *    - Stroke: normal (2)
 *    - Example: <Zap className="w-6 h-6" strokeWidth={2} />
 *
 * 2. **Value Props Cards** (glassmorphism cards)
 *    - Size: xl (w-8 h-8)
 *    - Stroke: normal (2)
 *    - Example: <Target className="w-8 h-8" strokeWidth={2} />
 *
 * 3. **Comparison Table** (iconic but compact)
 *    - Size: md (w-5 h-5)
 *    - Stroke: normal (2)
 *    - Example: <Globe className="w-5 h-5" strokeWidth={2} />
 *
 * 4. **With Animations** (Framer Motion)
 *    ```tsx
 *    <motion.div whileHover={{ scale: 1.1 }}>
 *      <Zap className="w-6 h-6" strokeWidth={2} />
 *    </motion.div>
 *    ```
 *
 * 5. **Accessibility** (always provide labels for icon-only elements)
 *    ```tsx
 *    <Zap
 *      className="w-5 h-5"
 *      aria-label="Velocidade 160x mais rápida"
 *      role="img"
 *    />
 *    ```
 */
