'use client';

import { useRef, useEffect, useState, type ReactNode } from 'react';

interface AnimateOnScrollProps {
  children: ReactNode;
  /** IntersectionObserver threshold (0-1). Default: 0.2 */
  threshold?: number;
  /** CSS class applied before element is visible */
  hiddenClass?: string;
  /** CSS class applied once element is visible */
  visibleClass?: string;
  /** HTML tag to render. Default: 'div' */
  as?: 'div' | 'section' | 'article';
  /** Additional className passed through */
  className?: string;
  /** Only trigger once (default: true) */
  once?: boolean;
  /** Transition delay in ms (maps to style.transitionDelay) */
  delay?: number;
  /** data-testid pass-through */
  'data-testid'?: string;
  /** id pass-through */
  id?: string;
}

/**
 * Lightweight client island for scroll-triggered CSS transitions.
 * Wraps static RSC children with an IntersectionObserver that toggles classes.
 *
 * Usage:
 *   <AnimateOnScroll hiddenClass="opacity-0 translate-y-4" visibleClass="opacity-100 translate-y-0">
 *     <StaticContent />
 *   </AnimateOnScroll>
 */
export default function AnimateOnScroll({
  children,
  threshold = 0.2,
  hiddenClass = 'opacity-0 translate-y-4',
  visibleClass = 'opacity-100 translate-y-0',
  as: Tag = 'div',
  className = '',
  once = true,
  delay,
  'data-testid': dataTestId,
  id,
}: AnimateOnScrollProps) {
  const ref = useRef<HTMLElement>(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // Respect reduced motion preference
    const prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches;

    if (prefersReducedMotion) {
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          if (once) {
            observer.unobserve(element);
          }
        } else if (!once) {
          setIsInView(false);
        }
      },
      { threshold }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [once, threshold]);

  return (
    <Tag
      ref={ref as React.RefObject<HTMLDivElement>}
      className={`transition-all duration-500 ${isInView ? visibleClass : hiddenClass} ${className}`}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
      data-testid={dataTestId}
      id={id}
    >
      {children}
    </Tag>
  );
}
