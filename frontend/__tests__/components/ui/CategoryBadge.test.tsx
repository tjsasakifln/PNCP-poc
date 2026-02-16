/**
 * GTM-005: CategoryBadge Tests
 */

import { render, screen } from '@testing-library/react';
import { CategoryBadge } from '@/app/components/ui/CategoryBadge';
import type { CategoryId } from '@/lib/data/analysisExamples';

describe('CategoryBadge', () => {
  const categories: CategoryId[] = [
    'uniformes',
    'facilities',
    'epi',
    'elevadores',
    'saude',
  ];

  categories.forEach((category) => {
    it(`renders badge for ${category}`, () => {
      render(<CategoryBadge category={category} />);
      const badge = screen.getByText(
        new RegExp(category === 'epi' ? 'EPI' : category, 'i')
      );
      expect(badge).toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    const { container } = render(
      <CategoryBadge category="uniformes" className="mt-4" />
    );
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('mt-4');
  });

  it('renders as inline-flex span', () => {
    render(<CategoryBadge category="epi" />);
    const badge = screen.getByText('EPI');
    expect(badge.tagName).toBe('SPAN');
  });
});
