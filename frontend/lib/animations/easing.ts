/**
 * STORY-174: Custom easing curves
 *
 * Premium easing functions for smooth, natural motion.
 * Based on industry-standard curves from Linear, Notion, Stripe.
 */

/**
 * Custom cubic-bezier curves
 * Format: [x1, y1, x2, y2]
 *
 * Use these with Framer Motion transitions:
 * transition={{ duration: 0.6, ease: EASE_OUT_CUBIC }}
 */

// Ease Out curves (decelerating motion - feels natural)
export const EASE_OUT_CUBIC = [0.33, 1, 0.68, 1];  // Smooth deceleration
export const EASE_OUT_EXPO = [0.16, 1, 0.3, 1];    // Strong deceleration (premium feel)
export const EASE_OUT_CIRC = [0, 0.55, 0.45, 1];   // Circular deceleration

// Ease In curves (accelerating motion - use sparingly)
export const EASE_IN_CUBIC = [0.32, 0, 0.67, 0];   // Smooth acceleration
export const EASE_IN_EXPO = [0.7, 0, 0.84, 0];     // Strong acceleration

// Ease In-Out curves (symmetrical acceleration/deceleration)
export const EASE_IN_OUT_CUBIC = [0.65, 0, 0.35, 1];  // Standard smooth curve
export const EASE_IN_OUT_EXPO = [0.87, 0, 0.13, 1];   // Strong emphasis
export const EASE_IN_OUT_CIRC = [0.85, 0, 0.15, 1];   // Circular motion

// Special curves
export const EASE_OUT_BACK = [0.34, 1.56, 0.64, 1];   // Slight overshoot (playful)
export const EASE_OUT_QUINT = [0.22, 1, 0.36, 1];     // Extra smooth (Apple-like)

/**
 * Spring configurations
 * Use with Framer Motion's spring animations:
 * transition={{ type: 'spring', ...SPRING_SMOOTH }}
 */

export const SPRING_SMOOTH = {
  type: 'spring' as const,
  stiffness: 300,
  damping: 30,
};

export const SPRING_BOUNCY = {
  type: 'spring' as const,
  stiffness: 400,
  damping: 10,
};

export const SPRING_GENTLE = {
  type: 'spring' as const,
  stiffness: 200,
  damping: 40,
};

export const SPRING_SNAPPY = {
  type: 'spring' as const,
  stiffness: 500,
  damping: 25,
};

/**
 * Duration recommendations (ms)
 *
 * Based on Material Design and Apple Human Interface Guidelines:
 * - Micro-interactions: 100-200ms (hover effects, button presses)
 * - Simple transitions: 200-400ms (fade, scale)
 * - Complex transitions: 400-600ms (slide, multi-step animations)
 * - Page transitions: 600-800ms (route changes)
 */

export const DURATION = {
  INSTANT: 100,    // Micro-interactions (hover states)
  FAST: 200,       // Quick transitions (scale, fade)
  NORMAL: 300,     // Standard transitions (most animations)
  SLOW: 400,       // Complex transitions (slide, lift)
  SLOWER: 600,     // Page-level transitions
  SLOWEST: 800,    // Hero animations, emphasis
} as const;

/**
 * Stagger delays (ms)
 *
 * For sequential animations in lists/grids:
 */

export const STAGGER = {
  FAST: 50,        // Quick succession (small lists)
  NORMAL: 100,     // Standard stagger (most use cases)
  SLOW: 150,       // Deliberate reveal (emphasis)
  SLOWER: 200,     // Very deliberate (hero sections)
} as const;

/**
 * Helper: Get easing function for CSS
 *
 * @example
 * style={{ transition: `all ${DURATION.NORMAL}ms ${getEasingCSS(EASE_OUT_CUBIC)}` }}
 */
export function getEasingCSS(curve: number[]): string {
  return `cubic-bezier(${curve.join(', ')})`;
}

/**
 * Presets for common use cases
 */

export const ANIMATION_PRESETS = {
  // Hero section entrance
  hero: {
    duration: DURATION.SLOWER,
    ease: EASE_OUT_EXPO,
  },

  // Card hover lift
  cardHover: {
    duration: DURATION.NORMAL,
    ease: EASE_OUT_CUBIC,
  },

  // Button interactions
  button: {
    duration: DURATION.FAST,
    ease: EASE_OUT_CUBIC,
  },

  // Modal/drawer entrance
  modal: {
    duration: DURATION.SLOW,
    ease: EASE_OUT_CUBIC,
  },

  // Scroll-triggered animations
  scrollReveal: {
    duration: DURATION.SLOW,
    ease: EASE_OUT_CUBIC,
  },

  // 3D tilt effect
  tilt3D: {
    duration: DURATION.SLOW,
    ease: EASE_IN_OUT_CUBIC,
  },

  // Glow effect
  glow: {
    duration: DURATION.NORMAL,
    ease: 'easeOut',
  },
} as const;
