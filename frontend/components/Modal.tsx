"use client";

/**
 * Canonical accessible Modal component (STORY-2.6, WCAG 2.1 AA).
 *
 * Features: role="dialog"|"alertdialog", aria-modal, aria-labelledby, aria-describedby,
 * focus trap (focus-trap-react), ESC closes, overlay click closes (configurable),
 * body scroll lock, rendered via React Portal.
 *
 * Use this component for all new modals. Existing modals (CancelSubscription,
 * PaymentRecovery, DeepAnalysis) received surgical ARIA patches preserving layout.
 *
 * @param isOpen - Controls visibility of the modal
 * @param onClose - Called when ESC key pressed, overlay clicked, or close button clicked
 * @param title - Modal heading (rendered as h2, linked via aria-labelledby)
 * @param description - Optional subtitle (linked via aria-describedby)
 * @param children - Modal body content
 * @param size - Width constraint: "sm" | "md" | "lg" | "xl" (default: "md")
 * @param closeOnOverlayClick - Close when backdrop clicked (default: true)
 * @param closeOnEsc - Close on ESC key (default: true)
 * @param hideCloseButton - Hides the × button (default: false)
 * @param role - ARIA role: "dialog" | "alertdialog" (default: "dialog")
 * @param className - Extra classes for the inner card container
 * @param id - Custom ID (default: auto-generated via useId)
 *
 * @example
 * // Basic modal
 * <Modal isOpen={open} onClose={() => setOpen(false)} title="Confirmar exclusão">
 *   <p>Tem certeza?</p>
 *   <Button onClick={() => setOpen(false)}>Cancelar</Button>
 * </Modal>
 *
 * @example
 * // Alert dialog (for destructive actions)
 * <Modal
 *   isOpen={open}
 *   onClose={onClose}
 *   title="Excluir oportunidade"
 *   role="alertdialog"
 *   size="sm"
 * >
 *   <Button variant="destructive" onClick={handleDelete}>Excluir</Button>
 * </Modal>
 */

import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import FocusTrap from "focus-trap-react";
import { X } from "lucide-react";

export type ModalSize = "sm" | "md" | "lg" | "xl";
export type ModalRole = "dialog" | "alertdialog";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  size?: ModalSize;
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  hideCloseButton?: boolean;
  role?: ModalRole;
  /** Classes extras para o container interno (card) */
  className?: string;
  /** ID custom (default: gerado via useId) */
  id?: string;
}

const SIZE_CLASS: Record<ModalSize, string> = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-2xl",
};

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = "md",
  closeOnOverlayClick = true,
  closeOnEsc = true,
  hideCloseButton = false,
  role = "dialog",
  className = "",
  id,
}: ModalProps) {
  const [mounted, setMounted] = useState(false);
  const generatedId = useId();
  const modalId = id ?? generatedId;
  const titleId = `${modalId}-title`;
  const descId = `${modalId}-desc`;
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // ESC handler
  useEffect(() => {
    if (!isOpen || !closeOnEsc) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, closeOnEsc, onClose]);

  // Body scroll lock
  useEffect(() => {
    if (!isOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [isOpen]);

  if (!mounted || !isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlayClick && e.target === overlayRef.current) {
      onClose();
    }
  };

  return createPortal(
    <FocusTrap
      focusTrapOptions={{
        escapeDeactivates: false,
        clickOutsideDeactivates: false,
        allowOutsideClick: true,
        returnFocusOnDeactivate: true,
        fallbackFocus: `#${modalId}`,
        tabbableOptions: { displayCheck: "none" },
      }}
    >
      <div
        ref={overlayRef}
        onClick={handleOverlayClick}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto"
        data-testid="modal-overlay"
      >
        <div
          id={modalId}
          role={role}
          aria-modal="true"
          aria-labelledby={titleId}
          aria-describedby={description ? descId : undefined}
          tabIndex={-1}
          className={`relative w-full ${SIZE_CLASS[size]} rounded-lg bg-white dark:bg-gray-900 p-6 shadow-xl ${className}`}
        >
          <h2 id={titleId} className="text-lg font-semibold text-gray-900 dark:text-gray-100 pr-8">
            {title}
          </h2>
          {description && (
            <p id={descId} className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              {description}
            </p>
          )}
          {!hideCloseButton && (
            <button
              type="button"
              onClick={onClose}
              aria-label="Fechar modal"
              className="absolute right-4 top-4 rounded-md p-1 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-2"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          )}
          <div className="mt-4">{children}</div>
        </div>
      </div>
    </FocusTrap>,
    document.body
  );
}
