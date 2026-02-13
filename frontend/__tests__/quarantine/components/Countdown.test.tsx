import React from 'react';
import { render, screen, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  Countdown,
  CountdownStatic,
  daysUntil,
  calculateTimeRemaining,
  formatCountdown,
} from '@/app/components/Countdown';

describe('Countdown', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders without crashing', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000); // 1 day from now
    render(<Countdown targetDate={futureDate} />);
    expect(screen.getByRole('timer')).toBeInTheDocument();
  });

  it('shows days remaining when > 1 day', () => {
    const futureDate = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000); // 3 days
    render(<Countdown targetDate={futureDate} />);
    expect(screen.getByText(/3 dias/)).toBeInTheDocument();
  });

  it('shows "1 dia" for exactly 1 day', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    render(<Countdown targetDate={futureDate} />);
    expect(screen.getByText(/1 dia/)).toBeInTheDocument();
  });

  it('shows hours and minutes when < 24 hours', () => {
    const futureDate = new Date(Date.now() + 5 * 60 * 60 * 1000 + 30 * 60 * 1000); // 5h 30min
    render(<Countdown targetDate={futureDate} />);
    expect(screen.getByText(/5h 30min/)).toBeInTheDocument();
  });

  it('shows "Encerrado" when expired', () => {
    const pastDate = new Date(Date.now() - 1000);
    render(<Countdown targetDate={pastDate} />);
    expect(screen.getByText('Encerrado')).toBeInTheDocument();
  });

  it('shows "Encerra hoje!" when < 12 hours', () => {
    const futureDate = new Date(Date.now() + 5 * 60 * 60 * 1000); // 5 hours
    render(<Countdown targetDate={futureDate} />);
    expect(screen.getByText(/Encerra hoje!/)).toBeInTheDocument();
  });

  it('shows "Urgente!" when < 3 hours', () => {
    const futureDate = new Date(Date.now() + 2 * 60 * 60 * 1000); // 2 hours
    render(<Countdown targetDate={futureDate} />);
    expect(screen.getByText(/Urgente!/)).toBeInTheDocument();
  });

  it('accepts label prop', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    render(<Countdown targetDate={futureDate} label="Tempo restante:" />);
    expect(screen.getByText('Tempo restante:')).toBeInTheDocument();
  });

  it('hides icon when showIcon is false', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    const { container } = render(
      <Countdown targetDate={futureDate} showIcon={false} />
    );
    const svg = container.querySelector('svg');
    expect(svg).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    const { container } = render(
      <Countdown targetDate={futureDate} className="custom-class" />
    );
    const timer = screen.getByRole('timer');
    expect(timer).toHaveClass('custom-class');
  });

  it('calls onExpire when countdown reaches zero', () => {
    const mockOnExpire = jest.fn();
    const nearFutureDate = new Date(Date.now() + 100); // 100ms from now

    render(<Countdown targetDate={nearFutureDate} onExpire={mockOnExpire} />);

    act(() => {
      jest.advanceTimersByTime(200);
    });

    expect(mockOnExpire).toHaveBeenCalled();
  });

  it('accepts ISO string as targetDate', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    render(<Countdown targetDate={futureDate.toISOString()} />);
    expect(screen.getByRole('timer')).toBeInTheDocument();
  });

  it('updates countdown every second when close to expiry', () => {
    const futureDate = new Date(Date.now() + 30 * 1000); // 30 seconds

    render(<Countdown targetDate={futureDate} />);

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(screen.getByRole('timer')).toBeInTheDocument();
  });

  it('supports small size', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    render(<Countdown targetDate={futureDate} size="sm" />);
    const timer = screen.getByRole('timer');
    expect(timer).toHaveClass('text-xs');
  });

  it('supports medium size (default)', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    render(<Countdown targetDate={futureDate} size="md" />);
    const timer = screen.getByRole('timer');
    expect(timer).toHaveClass('text-sm');
  });

  it('supports large size', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    render(<Countdown targetDate={futureDate} size="lg" />);
    const timer = screen.getByRole('timer');
    expect(timer).toHaveClass('text-base');
  });

  it('has proper ARIA attributes', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    render(<Countdown targetDate={futureDate} />);
    const timer = screen.getByRole('timer');
    expect(timer).toHaveAttribute('aria-live', 'polite');
    expect(timer).toHaveAttribute('aria-label');
  });
});

describe('CountdownStatic', () => {
  it('renders without crashing', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    render(<CountdownStatic targetDate={futureDate} />);
    expect(screen.getByText(/1 dia/)).toBeInTheDocument();
  });

  it('does not update in real-time', () => {
    jest.useFakeTimers();
    const futureDate = new Date(Date.now() + 60 * 1000); // 60 seconds
    const { container } = render(<CountdownStatic targetDate={futureDate} />);
    const initialText = container.textContent;

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    expect(container.textContent).toBe(initialText);
    jest.useRealTimers();
  });

  it('accepts all visual props', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    render(
      <CountdownStatic
        targetDate={futureDate}
        label="Test:"
        showIcon={false}
        size="lg"
        className="test-class"
      />
    );
    expect(screen.getByText('Test:')).toBeInTheDocument();
  });
});

describe('calculateTimeRemaining', () => {
  it('calculates days, hours, minutes, seconds correctly', () => {
    const futureDate = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 3 * 60 * 60 * 1000);
    const time = calculateTimeRemaining(futureDate);
    expect(time.days).toBe(2);
    expect(time.hours).toBe(3);
    expect(time.isExpired).toBe(false);
  });

  it('returns zero values when expired', () => {
    const pastDate = new Date(Date.now() - 1000);
    const time = calculateTimeRemaining(pastDate);
    expect(time.days).toBe(0);
    expect(time.hours).toBe(0);
    expect(time.minutes).toBe(0);
    expect(time.seconds).toBe(0);
    expect(time.isExpired).toBe(true);
  });
});

describe('formatCountdown', () => {
  it('formats days correctly', () => {
    const time = { days: 3, hours: 0, minutes: 0, seconds: 0, total: 1000, isExpired: false };
    expect(formatCountdown(time)).toBe('3 dias');
  });

  it('formats single day correctly', () => {
    const time = { days: 1, hours: 0, minutes: 0, seconds: 0, total: 1000, isExpired: false };
    expect(formatCountdown(time)).toBe('1 dia');
  });

  it('formats hours and minutes', () => {
    const time = { days: 0, hours: 5, minutes: 30, seconds: 0, total: 1000, isExpired: false };
    expect(formatCountdown(time)).toBe('5h 30min');
  });

  it('formats hours only', () => {
    const time = { days: 0, hours: 2, minutes: 0, seconds: 0, total: 1000, isExpired: false };
    expect(formatCountdown(time)).toBe('2h');
  });

  it('formats minutes only', () => {
    const time = { days: 0, hours: 0, minutes: 15, seconds: 0, total: 1000, isExpired: false };
    expect(formatCountdown(time)).toBe('15min');
  });

  it('formats seconds only', () => {
    const time = { days: 0, hours: 0, minutes: 0, seconds: 45, total: 1000, isExpired: false };
    expect(formatCountdown(time)).toBe('45s');
  });

  it('returns "Encerrado" when expired', () => {
    const time = { days: 0, hours: 0, minutes: 0, seconds: 0, total: 0, isExpired: true };
    expect(formatCountdown(time)).toBe('Encerrado');
  });
});

describe('daysUntil', () => {
  it('calculates days correctly', () => {
    const futureDate = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
    expect(daysUntil(futureDate)).toBe(3);
  });

  it('rounds up when hours remain', () => {
    const futureDate = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 5 * 60 * 60 * 1000);
    expect(daysUntil(futureDate)).toBe(3);
  });

  it('returns 0 for expired dates', () => {
    const pastDate = new Date(Date.now() - 1000);
    expect(daysUntil(pastDate)).toBe(0);
  });

  it('accepts ISO string', () => {
    const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000);
    expect(daysUntil(futureDate.toISOString())).toBe(1);
  });
});
