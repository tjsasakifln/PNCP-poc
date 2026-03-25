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
  { href: '/blog', label: 'Blog' },
  { href: '/sobre', label: 'Sobre' },
  { href: '#suporte', label: 'Suporte' },
];

export default function MobileMenu({ isOpen, onClose, user, scrollToSection }: MobileMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const scrollYRef = useRef(0);
  const lastInteractionRef = useRef<number>(Date.now());

  // Track user interactions for safety timeout (AC2)
  useEffect(() => {
    if (!isOpen) return;
    const updateInteraction = () => { lastInteractionRef.current = Date.now(); };
    document.addEventListener('touchstart', updateInteraction);
    document.addEventListener('click', updateInteraction);
    document.addEventListener('keydown', updateInteraction);
    return () => {
      document.removeEventListener('touchstart', updateInteraction);
      document.removeEventListener('click', updateInteraction);
      document.removeEventListener('keydown', updateInteraction);
    };
  }, [isOpen]);

  // AC2: Robust body scroll lock with position:fixed
  useEffect(() => {
    if (isOpen) {
      scrollYRef.current = window.scrollY;
      document.body.style.position = 'fixed';
      document.body.style.top = `-${scrollYRef.current}px`;
      document.body.style.width = '100%';
      document.body.setAttribute('data-mobile-menu-open', 'true');
    }
    return () => {
      const wasLocked = document.body.style.position === 'fixed';
      document.body.style.position = '';
      document.body.style.top = '';
      document.body.style.width = '';
      document.body.removeAttribute('data-mobile-menu-open');
      if (wasLocked) {
        window.scrollTo(0, scrollYRef.current);
      }
    };
  }, [isOpen]);

  // AC2: Safety timeout — warn if menu open without interaction
  useEffect(() => {
    if (!isOpen) return;
    lastInteractionRef.current = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - lastInteractionRef.current;
      if (elapsed > 10_000) {
        console.warn('[MobileMenu] Menu open >10s without interaction');
      }
      if (elapsed > 15_000) {
        console.warn('[MobileMenu] Scroll lock active >15s — potential stuck state');
      }
    }, 5_000);
    return () => clearInterval(interval);
  }, [isOpen]);

  // AC6: Fallback emergency — check 500ms after close
  useEffect(() => {
    if (isOpen) return;
    const timeoutId = setTimeout(() => {
      if (document.body.style.position === 'fixed' || document.body.hasAttribute('data-mobile-menu-open')) {
        console.warn('[MobileMenu] Emergency fallback: removing stuck scroll lock');
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        document.body.removeAttribute('data-mobile-menu-open');
      }
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [isOpen]);

  // AC3: History API integration — back button closes menu
  useEffect(() => {
    if (!isOpen) return;
    window.history.pushState({ mobileMenu: true }, '');
    const handlePopState = () => {
      onClose();
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [isOpen, onClose]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // AC5: Focus trap — keep Tab within menu panel
  useEffect(() => {
    if (!isOpen || !menuRef.current) return;
    const panel = menuRef.current;
    const focusableSelector = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const focusable = Array.from(panel.querySelectorAll<HTMLElement>(focusableSelector));
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleTab);
    const closeBtn = panel.querySelector<HTMLElement>('[data-testid="mobile-menu-close"]');
    closeBtn?.focus();

    return () => document.removeEventListener('keydown', handleTab);
  }, [isOpen]);

  if (!isOpen) return null;

  const handleNavClick = (link: NavLink) => {
    if (link.sectionId && scrollToSection) {
      scrollToSection(link.sectionId);
    }
    onClose();
  };

  return (
    <>
      {/* Overlay backdrop — AC4: opaque, no blur */}
      <div
        className="fixed inset-0 z-40 bg-black/60 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
        data-testid="mobile-menu-overlay"
      />

      {/* Slide-out panel from right */}
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
        {/* Close button — AC5: 48px touch target + "Fechar" label */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
          <span className="text-lg font-bold text-[var(--ink)]">
            SmartLic<span className="text-[var(--brand-blue)]">.tech</span>
          </span>
          <button
            onClick={onClose}
            className="min-h-[48px] min-w-[48px] flex items-center gap-1.5 justify-center rounded-lg
                       text-[var(--ink-secondary)] hover:text-[var(--ink)] hover:bg-[var(--surface-1)]
                       transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]"
            aria-label="Fechar menu"
            data-testid="mobile-menu-close"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            <span className="text-xs font-medium">Fechar</span>
          </button>
        </div>

        {/* Navigation links */}
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

        {/* Auth buttons */}
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
                Entrar
              </Link>
              <Link
                href="/signup?source=header-cta-mobile"
                onClick={onClose}
                className="block w-full min-h-[44px] px-4 py-3 text-center text-base font-semibold
                           bg-[var(--brand-navy)] hover:bg-[var(--brand-blue-hover)] text-white rounded-lg
                           transition-all focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
              >
                Comece Gratis
              </Link>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
