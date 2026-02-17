'use client';

import { useEffect, useRef } from 'react';
import Link from 'next/link';

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  user: { email?: string } | null;
  scrollToSection?: (id: string) => void;
}

type NavLink =
  | { href: string; label: string; sectionId?: never }
  | { sectionId: string; label: string; href?: never };

const NAV_LINKS: NavLink[] = [
  { href: '/', label: 'Home' },
  { href: '/planos', label: 'Planos' },
  { sectionId: 'como-funciona', label: 'Como Funciona' },
  { href: '#suporte', label: 'Suporte' },
];

export default function MobileMenu({ isOpen, onClose, user, scrollToSection }: MobileMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  // Lock body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleNavClick = (link: NavLink) => {
    if (link.sectionId && scrollToSection) {
      scrollToSection(link.sectionId);
    }
    onClose();
  };

  return (
    <>
      {/* Overlay backdrop — AC4 */}
      <div
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
        data-testid="mobile-menu-overlay"
      />

      {/* Slide-out panel from right — AC2 */}
      <div
        ref={menuRef}
        role="dialog"
        aria-modal="true"
        aria-label="Menu de navegação"
        className="fixed top-0 right-0 z-50 h-full w-[280px] max-w-[80vw] bg-[var(--surface-0)] shadow-2xl
                   transform transition-transform duration-300 ease-out
                   animate-slide-in-right"
        data-testid="mobile-menu-panel"
      >
        {/* Close button — AC5 */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
          <span className="text-lg font-bold text-[var(--ink)]">
            SmartLic<span className="text-[var(--brand-blue)]">.tech</span>
          </span>
          <button
            onClick={onClose}
            className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg
                       text-[var(--ink-secondary)] hover:text-[var(--ink)] hover:bg-[var(--surface-1)]
                       transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]"
            aria-label="Fechar menu"
            data-testid="mobile-menu-close"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Navigation links — AC3, AC6 */}
        <nav className="p-4 space-y-1" aria-label="Menu principal">
          {NAV_LINKS.map((link) => {
            if (link.sectionId) {
              return (
                <button
                  key={link.label}
                  onClick={() => handleNavClick(link)}
                  className="w-full min-h-[44px] px-4 py-3 text-left text-base font-medium
                             text-[var(--ink)] hover:bg-[var(--surface-1)] rounded-lg transition-colors
                             focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]"
                >
                  {link.label}
                </button>
              );
            }
            return (
              <Link
                key={link.label}
                href={link.href!}
                onClick={onClose}
                className="block min-h-[44px] px-4 py-3 text-base font-medium
                           text-[var(--ink)] hover:bg-[var(--surface-1)] rounded-lg transition-colors
                           focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]"
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Auth buttons — AC3 */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[var(--border)] bg-[var(--surface-0)]">
          {user ? (
            <Link
              href="/buscar"
              onClick={onClose}
              className="block w-full min-h-[44px] px-4 py-3 text-center text-base font-semibold
                         bg-[var(--brand-navy)] hover:bg-[var(--brand-blue-hover)] text-white rounded-lg
                         transition-all focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
            >
              Ir para Busca
            </Link>
          ) : (
            <div className="space-y-2">
              <Link
                href="/login"
                onClick={onClose}
                className="block w-full min-h-[44px] px-4 py-3 text-center text-base font-semibold
                           text-[var(--brand-navy)] border border-[var(--brand-navy)] hover:bg-[var(--surface-1)]
                           rounded-lg transition-colors
                           focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]"
              >
                Login
              </Link>
              <Link
                href="/signup?source=landing-mobile"
                onClick={onClose}
                className="block w-full min-h-[44px] px-4 py-3 text-center text-base font-semibold
                           bg-[var(--brand-navy)] hover:bg-[var(--brand-blue-hover)] text-white rounded-lg
                           transition-all focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
              >
                Criar conta
              </Link>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
