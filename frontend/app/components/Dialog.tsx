"use client";

import { useEffect, useRef, useCallback, type ReactNode } from "react";

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  /** Additional CSS classes for the dialog panel */
  className?: string;
  /** Whether clicking the backdrop closes the dialog (default: true) */
  closeOnBackdropClick?: boolean;
  /** Unique ID prefix for ARIA attributes (auto-generated if omitted) */
  id?: string;
}

/**
 * Accessible dialog component with focus trap, ARIA attributes, and Escape handling.
 *
 * Based on UpgradeModal.tsx pattern, extracted for reuse across the app.
 * Resolves WCAG 2.4.3 (Focus Order) and 4.1.2 (Name/Role/Value).
 *
 * @example
 * <Dialog isOpen={show} onClose={() => setShow(false)} title="Save Search">
 *   <p>Dialog content here</p>
 * </Dialog>
 */
export function Dialog({
  isOpen,
  onClose,
  title,
  children,
  className = "",
  closeOnBackdropClick = true,
  id = "dialog",
}: DialogProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<Element | null>(null);

  // Capture the element that opened the dialog so we can restore focus
  useEffect(() => {
    if (isOpen) {
      triggerRef.current = document.activeElement;
    }
  }, [isOpen]);

  // Focus the panel when it opens
  useEffect(() => {
    if (isOpen && panelRef.current) {
      panelRef.current.focus();
    }
  }, [isOpen]);

  // Restore focus to trigger element on close
  useEffect(() => {
    if (!isOpen && triggerRef.current instanceof HTMLElement) {
      triggerRef.current.focus();
      triggerRef.current = null;
    }
  }, [isOpen]);

  // Escape key handler (capture phase to intercept before other listeners)
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape, true);
    return () => document.removeEventListener("keydown", handleEscape, true);
  }, [isOpen, onClose]);

  // Body scroll lock
  useEffect(() => {
    if (!isOpen) return;

    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [isOpen]);

  // Focus trap: Tab/Shift+Tab cycle within modal
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key !== "Tab" || !panelRef.current) return;

      const focusable = panelRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea, input:not([disabled]), select, [tabindex]:not([tabindex="-1"])'
      );

      if (focusable.length === 0) {
        e.preventDefault();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first || document.activeElement === panelRef.current) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    []
  );

  if (!isOpen) return null;

  const titleId = `${id}-title`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in"
      onClick={closeOnBackdropClick ? onClose : undefined}
      aria-modal="true"
      role="dialog"
      aria-labelledby={titleId}
    >
      <div
        ref={panelRef}
        className={`bg-surface-0 rounded-card shadow-xl w-full p-6 animate-fade-in-up ${className}`}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
        tabIndex={-1}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 id={titleId} className="text-lg font-semibold text-ink">
            {title}
          </h3>
          <button
            onClick={onClose}
            type="button"
            className="p-1 text-ink-muted hover:text-ink hover:bg-surface-1 rounded-full transition-colors"
            aria-label="Fechar"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
