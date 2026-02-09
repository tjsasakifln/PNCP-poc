/**
 * STORY-174: Animation utilities index
 *
 * Centralized exports for all animation utilities.
 * Import from this file for cleaner imports.
 *
 * @example
 * import { useScrollAnimation, fadeInUp, EASE_OUT_CUBIC } from '@/lib/animations';
 */

// Scroll animation hooks
export {
  useScrollAnimation,
  useStaggeredScrollAnimation,
  useScrollProgress,
} from './scrollAnimations';

// Framer Motion variants
export {
  fadeInUp,
  fadeIn,
  scaleIn,
  slideInLeft,
  slideInRight,
  lift,
  tilt3D,
  glow,
  staggerContainer,
  staggerContainerFast,
  counterVariant,
  underlineHover,
  rotateIn,
  bounceIn,
} from './framerVariants';

// Easing curves and presets
export {
  EASE_OUT_CUBIC,
  EASE_OUT_EXPO,
  EASE_OUT_CIRC,
  EASE_IN_CUBIC,
  EASE_IN_EXPO,
  EASE_IN_OUT_CUBIC,
  EASE_IN_OUT_EXPO,
  EASE_IN_OUT_CIRC,
  EASE_OUT_BACK,
  EASE_OUT_QUINT,
  SPRING_SMOOTH,
  SPRING_BOUNCY,
  SPRING_GENTLE,
  SPRING_SNAPPY,
  DURATION,
  STAGGER,
  ANIMATION_PRESETS,
  getEasingCSS,
} from './easing';
