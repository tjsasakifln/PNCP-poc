'use client';

import { ReactNode, ButtonHTMLAttributes } from 'react';
import { motion } from 'framer-motion';

interface GradientButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  glow?: boolean;
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

/**
 * STORY-174: Premium gradient button component
 *
 * Features:
 * - Gradient background (brand colors)
 * - Glow effect on hover (optional)
 * - Scale transform on hover
 * - Multiple variants and sizes
 * - Smooth transitions
 *
 * @example
 * <GradientButton variant="primary" glow={true} onClick={handleClick}>
 *   Get Started
 * </GradientButton>
 */
export function GradientButton({
  children,
  variant = 'primary',
  size = 'md',
  glow = true,
  className = '',
  onClick,
  disabled,
  type = 'button',
}: GradientButtonProps) {
  // Variant-specific styles
  const variantStyles = {
    primary: `
      bg-gradient-to-r from-brand-blue to-brand-navy
      text-white
      hover:from-brand-blue-hover hover:to-brand-navy
      shadow-md hover:shadow-xl
      ${glow ? 'hover:shadow-glow' : ''}
    `,
    secondary: `
      bg-white dark:bg-gray-800
      text-brand-navy dark:text-brand-blue
      border-2 border-brand-blue
      hover:bg-brand-blue-subtle dark:hover:bg-brand-blue/10
      shadow-sm hover:shadow-md
    `,
  };

  // Size-specific styles
  const sizeStyles = {
    sm: 'px-4 py-2 text-sm rounded-lg',
    md: 'px-6 py-3 text-base rounded-xl',
    lg: 'px-8 py-4 text-lg rounded-xl',
  };

  return (
    <motion.button
      className={`
        font-semibold
        transition-all
        duration-300
        focus:outline-none
        focus:ring-4
        focus:ring-brand-blue/50
        focus:ring-offset-2
        disabled:opacity-50
        disabled:cursor-not-allowed
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{
        duration: 0.2,
        ease: 'easeOut',
      }}
      onClick={onClick}
      disabled={disabled}
      type={type}
    >
      {children}
    </motion.button>
  );
}
