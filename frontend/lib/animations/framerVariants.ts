import { Variants } from 'framer-motion';

/**
 * STORY-174: Framer Motion animation variants
 *
 * Pre-defined animation variants for consistent motion design.
 * All variants use custom easing curves for premium feel.
 */

// Custom easing curves (matching easing.ts)
const EASE_OUT_EXPO = [0.16, 1, 0.3, 1] as const;
const EASE_OUT_CUBIC = [0.33, 1, 0.68, 1] as const;
const EASE_IN_OUT_CUBIC = [0.65, 0, 0.35, 1] as const;

/**
 * Fade In + Slide Up
 * Use for: Hero content, section headings, cards on scroll
 */
export const fadeInUp: Variants = {
  hidden: {
    opacity: 0,
    y: 24,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: EASE_OUT_CUBIC,
    },
  },
};

/**
 * Fade In (simple)
 * Use for: Background elements, overlays
 */
export const fadeIn: Variants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.4,
      ease: 'easeOut',
    },
  },
};

/**
 * Scale In
 * Use for: Modals, tooltips, badges
 */
export const scaleIn: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.95,
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.3,
      ease: EASE_OUT_EXPO,
    },
  },
};

/**
 * Slide In from Left
 * Use for: Sidebar navigation, mobile menus
 */
export const slideInLeft: Variants = {
  hidden: {
    x: -100,
    opacity: 0,
  },
  visible: {
    x: 0,
    opacity: 1,
    transition: {
      duration: 0.5,
      ease: EASE_OUT_CUBIC,
    },
  },
};

/**
 * Slide In from Right
 * Use for: Notification panels, side drawers
 */
export const slideInRight: Variants = {
  hidden: {
    x: 100,
    opacity: 0,
  },
  visible: {
    x: 0,
    opacity: 1,
    transition: {
      duration: 0.5,
      ease: EASE_OUT_CUBIC,
    },
  },
};

/**
 * Lift (hover effect)
 * Use for: Card hover states, button interactions
 */
export const lift: Variants = {
  initial: {
    y: 0,
    boxShadow: 'var(--shadow-md)',
  },
  hover: {
    y: -8,
    boxShadow: 'var(--shadow-xl)',
    transition: {
      duration: 0.3,
      ease: EASE_OUT_CUBIC,
    },
  },
};

/**
 * 3D Tilt (hover effect)
 * Use for: Sector cards, product cards
 */
export const tilt3D: Variants = {
  initial: {
    rotateX: 0,
    rotateY: 0,
  },
  hover: {
    rotateX: 5,
    rotateY: 5,
    transition: {
      duration: 0.4,
      ease: EASE_IN_OUT_CUBIC,
    },
  },
};

/**
 * Glow (hover effect)
 * Use for: CTA buttons, primary actions
 */
export const glow: Variants = {
  initial: {
    boxShadow: 'var(--shadow-md)',
  },
  hover: {
    boxShadow: 'var(--shadow-glow)',
    transition: {
      duration: 0.3,
      ease: 'easeOut',
    },
  },
};

/**
 * Stagger Container
 * Use for: Lists, grids with sequential animations
 *
 * @example
 * <motion.div variants={staggerContainer} initial="hidden" animate="visible">
 *   <motion.div variants={fadeInUp}>Item 1</motion.div>
 *   <motion.div variants={fadeInUp}>Item 2</motion.div>
 * </motion.div>
 */
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1, // 100ms delay between children
      delayChildren: 0.2,   // Start after 200ms
    },
  },
};

/**
 * Stagger Container (fast)
 * Use for: Quick sequential animations
 */
export const staggerContainerFast: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05, // 50ms delay
      delayChildren: 0.1,
    },
  },
};

/**
 * Number Counter Animation
 * Use for: Stats badges, metrics displays
 *
 * Note: Requires custom component with AnimatedNumber
 * (See AC1 hero stats badges implementation)
 */
export const counterVariant: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.8,
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.5,
      ease: EASE_OUT_EXPO,
    },
  },
};

/**
 * Underline Animation (hover)
 * Use for: Footer links, navigation links
 *
 * Note: Requires pseudo-element with scaleX transform
 */
export const underlineHover: Variants = {
  initial: {
    scaleX: 0,
  },
  hover: {
    scaleX: 1,
    transition: {
      duration: 0.3,
      ease: EASE_OUT_CUBIC,
    },
  },
};

/**
 * Rotate In
 * Use for: Icons, checkmarks, decorative elements
 */
export const rotateIn: Variants = {
  hidden: {
    opacity: 0,
    rotate: -90,
    scale: 0.5,
  },
  visible: {
    opacity: 1,
    rotate: 0,
    scale: 1,
    transition: {
      duration: 0.5,
      ease: EASE_OUT_EXPO,
    },
  },
};

/**
 * Bounce In
 * Use for: Success states, notifications
 */
export const bounceIn: Variants = {
  hidden: {
    opacity: 0,
    scale: 0,
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 200,
      damping: 10,
    },
  },
};
