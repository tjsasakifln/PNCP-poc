import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';

// Mock window.scrollTo (not implemented in jsdom)
Object.defineProperty(window, 'scrollTo', { value: jest.fn(), writable: true });

// Mock next/link
jest.mock('next/link', () => {
  return function MockLink({ children, href, onClick }: { children: React.ReactNode; href: string; onClick?: () => void }) {
    return <a href={href} onClick={onClick}>{children}</a>;
  };
});

import MobileMenu from '../../components/layout/MobileMenu';

describe('MobileMenu', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    user: null,
    scrollToSection: jest.fn(),
  };

  let pushStateSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.width = '';
    document.body.removeAttribute('data-mobile-menu-open');
    pushStateSpy = jest.spyOn(window.history, 'pushState').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    pushStateSpy.mockRestore();
    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.width = '';
    document.body.removeAttribute('data-mobile-menu-open');
  });

  // ========================================
  // EXISTING TESTS (updated for new behavior)
  // ========================================

  // AC2: Menu opens from right
  it('renders slide-out panel when isOpen is true', () => {
    render(<MobileMenu {...defaultProps} />);
    expect(screen.getByTestId('mobile-menu-panel')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<MobileMenu {...defaultProps} isOpen={false} />);
    expect(screen.queryByTestId('mobile-menu-panel')).not.toBeInTheDocument();
  });

  // Navigation links
  it('includes Home, Licitações, Consultoria links', () => {
    render(<MobileMenu {...defaultProps} />);
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Licitações')).toBeInTheDocument();
    expect(screen.getByText('Consultoria')).toBeInTheDocument();
  });

  it('shows Entrar and Diagnóstico CONFENGE for unauthenticated users', () => {
    render(<MobileMenu {...defaultProps} user={null} />);
    expect(screen.getByText('Entrar')).toBeInTheDocument();
    expect(screen.getByText('Diagnóstico CONFENGE')).toBeInTheDocument();
  });

  it('shows Ir para Busca for authenticated users', () => {
    render(<MobileMenu {...defaultProps} user={{ email: 'test@test.com' }} />);
    expect(screen.getByText('Ir para Busca')).toBeInTheDocument();
    expect(screen.queryByText('Entrar')).not.toBeInTheDocument();
  });

  // Overlay closes menu
  it('calls onClose when overlay is clicked', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.click(screen.getByTestId('mobile-menu-overlay'));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  // Close button
  it('calls onClose when close button is clicked', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.click(screen.getByTestId('mobile-menu-close'));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  // Nav links close menu
  it('calls onClose when a nav link is clicked', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.click(screen.getByText('Home'));
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('calls onClose when a regular nav link is clicked', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.click(screen.getByText('Consultoria'));
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  // Escape key
  it('closes on Escape key', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  // AC2: Body scroll lock — position:fixed approach (updated)
  it('locks body scroll when open using position:fixed', () => {
    render(<MobileMenu {...defaultProps} isOpen={true} />);
    expect(document.body.style.position).toBe('fixed');
    expect(document.body.style.width).toBe('100%');
  });

  it('unlocks body scroll on unmount', () => {
    const { unmount } = render(<MobileMenu {...defaultProps} isOpen={true} />);
    unmount();
    expect(document.body.style.position).toBe('');
    expect(document.body.style.top).toBe('');
    expect(document.body.style.width).toBe('');
  });

  // Accessibility
  it('has proper aria attributes', () => {
    render(<MobileMenu {...defaultProps} />);
    const panel = screen.getByTestId('mobile-menu-panel');
    expect(panel).toHaveAttribute('role', 'dialog');
    expect(panel).toHaveAttribute('aria-modal', 'true');
  });

  it('close button has aria-label', () => {
    render(<MobileMenu {...defaultProps} />);
    expect(screen.getByLabelText('Fechar menu')).toBeInTheDocument();
  });

  // AC5: WCAG touch targets — close button >= 48px (updated from 44px)
  it('close button has min-h-[48px] min-w-[48px] touch targets', () => {
    render(<MobileMenu {...defaultProps} />);
    const closeBtn = screen.getByTestId('mobile-menu-close');
    expect(closeBtn.className).toContain('min-h-[48px]');
    expect(closeBtn.className).toContain('min-w-[48px]');
  });

  // ========================================
  // NEW TESTS (AC7)
  // ========================================

  // AC5: "Fechar" text on close button
  it('close button shows "Fechar" text', () => {
    render(<MobileMenu {...defaultProps} />);
    const closeBtn = screen.getByTestId('mobile-menu-close');
    expect(closeBtn).toHaveTextContent('Fechar');
  });

  // AC6: data-mobile-menu-open attribute
  it('sets data-mobile-menu-open attribute when open', () => {
    render(<MobileMenu {...defaultProps} isOpen={true} />);
    expect(document.body.getAttribute('data-mobile-menu-open')).toBe('true');
  });

  it('removes data-mobile-menu-open attribute on unmount', () => {
    const { unmount } = render(<MobileMenu {...defaultProps} isOpen={true} />);
    expect(document.body.getAttribute('data-mobile-menu-open')).toBe('true');
    unmount();
    expect(document.body.hasAttribute('data-mobile-menu-open')).toBe(false);
  });

  // AC3/AC7: Back button (History API) closes menu
  it('pushes history state when menu opens', () => {
    render(<MobileMenu {...defaultProps} isOpen={true} />);
    expect(pushStateSpy).toHaveBeenCalledWith({ mobileMenu: true }, '');
  });

  it('closes menu on popstate event (back button)', () => {
    render(<MobileMenu {...defaultProps} isOpen={true} />);
    act(() => {
      window.dispatchEvent(new PopStateEvent('popstate'));
    });
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('does not push history state when menu is closed', () => {
    render(<MobileMenu {...defaultProps} isOpen={false} />);
    expect(pushStateSpy).not.toHaveBeenCalled();
  });

  // AC3: History API cleanup on unmount
  it('cleans up popstate listener on unmount', () => {
    const removeListenerSpy = jest.spyOn(window, 'removeEventListener');
    const { unmount } = render(<MobileMenu {...defaultProps} isOpen={true} />);
    unmount();
    expect(removeListenerSpy).toHaveBeenCalledWith('popstate', expect.any(Function));
    removeListenerSpy.mockRestore();
  });

  // AC7: Scroll lock removed on unexpected unmount
  it('removes scroll lock on unexpected unmount while still open', () => {
    const { unmount } = render(<MobileMenu {...defaultProps} isOpen={true} />);
    expect(document.body.style.position).toBe('fixed');
    unmount();
    expect(document.body.style.position).toBe('');
    expect(document.body.getAttribute('data-mobile-menu-open')).toBeNull();
  });

  // AC7: Timeout de seguranca emite warning
  it('emits console.warn after 10s without interaction', () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    render(<MobileMenu {...defaultProps} isOpen={true} />);

    // Advance time to trigger the interval (fires at 5s intervals, checks >10s elapsed)
    act(() => {
      jest.advanceTimersByTime(15_000);
    });

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('Menu open >10s without interaction')
    );
    warnSpy.mockRestore();
  });

  it('emits stuck state warning after 15s without interaction', () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    render(<MobileMenu {...defaultProps} isOpen={true} />);

    // Advance to 20s so elapsed > 15000
    act(() => {
      jest.advanceTimersByTime(20_000);
    });

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('Scroll lock active >15s')
    );
    warnSpy.mockRestore();
  });

  // AC7: Overlay without backdrop-blur
  it('overlay does not use backdrop-blur', () => {
    render(<MobileMenu {...defaultProps} />);
    const overlay = screen.getByTestId('mobile-menu-overlay');
    expect(overlay.className).not.toContain('backdrop-blur');
  });

  it('overlay uses bg-black/60 for opaque background', () => {
    render(<MobileMenu {...defaultProps} />);
    const overlay = screen.getByTestId('mobile-menu-overlay');
    expect(overlay.className).toContain('bg-black/60');
  });
});
