/**
 * UX-344 + SAB-006 — Landing Page: Accessible Counters
 * Verifies aria-labels on animated/static counters so screen readers
 * read the correct final values (not the animation start value "0").
 *
 * SAB-006: HeroSection stats badges removed (consolidated into StatsSection).
 * Only StatsSection counters remain.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';

// ---- Mocks ----

// Mock framer-motion — pass through children
jest.mock('framer-motion', () => {
  const React = require('react');
  const motion = new Proxy(
    {},
    {
      get: (_target: unknown, prop: string) =>
        React.forwardRef(
          (
            { children, ...props }: { children?: React.ReactNode; [key: string]: unknown },
            ref: React.Ref<HTMLElement>
          ) => {
            const safe: Record<string, unknown> = {};
            for (const [k, v] of Object.entries(props)) {
              if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') {
                safe[k] = v;
              }
            }
            return React.createElement(prop, { ...safe, ref }, children);
          }
        ),
    }
  );
  return { motion, AnimatePresence: ({ children }: { children: React.ReactNode }) => children };
});

// Mock animations lib — always visible so counters render immediately
jest.mock('../lib/animations', () => ({
  useScrollAnimation: () => ({ ref: { current: null }, isVisible: true }),
  fadeInUp: {},
  staggerContainer: {},
  scaleIn: {},
}));

// Mock GradientButton
jest.mock('../app/components/ui/GradientButton', () => ({
  GradientButton: ({ children }: { children: React.ReactNode }) => (
    <button>{children}</button>
  ),
}));

// Mock useInView for StatsSection
jest.mock('../app/hooks/useInView', () => ({
  useInView: () => ({ ref: { current: null }, isInView: true }),
}));

// ---- Imports (after mocks) ----
import StatsSection from '../app/components/landing/StatsSection';

// ---- Tests ----

describe('UX-344 + SAB-006 — Landing Page Accessible Counters', () => {
  describe('AC2: StatsSection counters have aria-label with final values', () => {
    it('renders aria-label="15 setores especializados"', () => {
      render(<StatsSection />);
      expect(
        screen.getByRole('text', { name: '15 setores especializados' })
      ).toBeInTheDocument();
    });

    it('renders aria-label="87% de editais descartados"', () => {
      render(<StatsSection />);
      expect(
        screen.getByRole('text', { name: '87% de editais descartados' })
      ).toBeInTheDocument();
    });

    it('renders aria-label="1000+ regras de filtragem"', () => {
      render(<StatsSection />);
      expect(
        screen.getByRole('text', { name: '1000+ regras de filtragem' })
      ).toBeInTheDocument();
    });

    it('renders aria-label="27 estados cobertos"', () => {
      render(<StatsSection />);
      expect(
        screen.getByRole('text', { name: '27 estados cobertos' })
      ).toBeInTheDocument();
    });
  });

  describe('AC2+AC4: StatsSection values are aria-hidden', () => {
    it('hides number divs from screen readers', () => {
      const { container } = render(<StatsSection />);
      const hiddenEls = container.querySelectorAll('[aria-hidden="true"]');
      // 4 stat cards × 2 inner divs (number + label) = 8 aria-hidden elements
      expect(hiddenEls.length).toBeGreaterThanOrEqual(8);
    });
  });
});
