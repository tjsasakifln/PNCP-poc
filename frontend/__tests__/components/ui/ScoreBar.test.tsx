/**
 * GTM-005: ScoreBar Tests
 */

import { render, screen } from '@testing-library/react';
import { ScoreBar } from '@/app/components/ui/ScoreBar';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, style, ...rest }: Record<string, unknown>) => (
      <div className={className as string} style={style as React.CSSProperties} data-testid="score-bar-fill">
        {children as React.ReactNode}
      </div>
    ),
  },
}));

describe('ScoreBar', () => {
  it('renders with label by default', () => {
    render(<ScoreBar score={8.5} />);
    expect(screen.getByText('8.5')).toBeInTheDocument();
  });

  it('hides label when showLabel is false', () => {
    render(<ScoreBar score={8.5} showLabel={false} />);
    expect(screen.queryByText('8.5')).not.toBeInTheDocument();
  });

  it('renders the bar track', () => {
    const { container } = render(<ScoreBar score={7.0} />);
    // The track is a rounded-full bg-gray-200 div
    const track = container.querySelector('.bg-gray-200');
    expect(track).toBeInTheDocument();
  });

  it('applies green color for high scores (>= 7.5)', () => {
    render(<ScoreBar score={8.5} />);
    const label = screen.getByText('8.5');
    expect(label.className).toContain('emerald');
  });

  it('applies amber color for medium scores (5-7.4)', () => {
    render(<ScoreBar score={5.2} />);
    const label = screen.getByText('5.2');
    expect(label.className).toContain('amber');
  });

  it('applies red color for low scores (< 5)', () => {
    render(<ScoreBar score={4.8} />);
    const label = screen.getByText('4.8');
    expect(label.className).toContain('red');
  });

  it('accepts custom className', () => {
    const { container } = render(<ScoreBar score={7.0} className="mt-2" />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain('mt-2');
  });

  it('respects custom maxScore', () => {
    render(<ScoreBar score={5.0} maxScore={5} />);
    // Score 5/5 = 100%, should be green
    const label = screen.getByText('5.0');
    expect(label).toBeInTheDocument();
  });
});
