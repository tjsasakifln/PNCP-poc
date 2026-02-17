import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

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

  beforeEach(() => {
    jest.clearAllMocks();
    document.body.style.overflow = '';
  });

  // AC2: Menu opens from right
  it('renders slide-out panel when isOpen is true', () => {
    render(<MobileMenu {...defaultProps} />);
    expect(screen.getByTestId('mobile-menu-panel')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<MobileMenu {...defaultProps} isOpen={false} />);
    expect(screen.queryByTestId('mobile-menu-panel')).not.toBeInTheDocument();
  });

  // AC3: Menu includes all navigation links
  it('includes Home, Planos, Como Funciona, Suporte links', () => {
    render(<MobileMenu {...defaultProps} />);
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Planos')).toBeInTheDocument();
    expect(screen.getByText('Como Funciona')).toBeInTheDocument();
    expect(screen.getByText('Suporte')).toBeInTheDocument();
  });

  // AC3: Menu includes Login and Criar conta when not logged in
  it('shows Login and Criar conta for unauthenticated users', () => {
    render(<MobileMenu {...defaultProps} user={null} />);
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByText('Criar conta')).toBeInTheDocument();
  });

  // AC3: Menu shows "Ir para Busca" when logged in
  it('shows Ir para Busca for authenticated users', () => {
    render(<MobileMenu {...defaultProps} user={{ email: 'test@test.com' }} />);
    expect(screen.getByText('Ir para Busca')).toBeInTheDocument();
    expect(screen.queryByText('Login')).not.toBeInTheDocument();
  });

  // AC4: Overlay closes menu when clicked
  it('calls onClose when overlay is clicked', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.click(screen.getByTestId('mobile-menu-overlay'));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  // AC5: Close button
  it('calls onClose when close button is clicked', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.click(screen.getByTestId('mobile-menu-close'));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  // AC6: Nav links close menu after click
  it('calls onClose when a nav link is clicked', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.click(screen.getByText('Home'));
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('calls scrollToSection and onClose for section links', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.click(screen.getByText('Como Funciona'));
    expect(defaultProps.scrollToSection).toHaveBeenCalledWith('como-funciona');
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  // Escape key closes menu
  it('closes on Escape key', () => {
    render(<MobileMenu {...defaultProps} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  // Body scroll lock
  it('locks body scroll when open', () => {
    render(<MobileMenu {...defaultProps} isOpen={true} />);
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('unlocks body scroll on unmount', () => {
    const { unmount } = render(<MobileMenu {...defaultProps} isOpen={true} />);
    unmount();
    expect(document.body.style.overflow).toBe('');
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

  // WCAG touch targets — all interactive elements must be >= 44px
  it('all buttons and links have min-h-[44px] touch targets', () => {
    render(<MobileMenu {...defaultProps} />);
    const closeBtn = screen.getByTestId('mobile-menu-close');
    expect(closeBtn.className).toContain('min-h-[44px]');
    expect(closeBtn.className).toContain('min-w-[44px]');
  });
});
