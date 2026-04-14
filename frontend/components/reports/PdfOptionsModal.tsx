"use client";

import { useState, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import FocusTrap from "focus-trap-react";

export interface PdfOptionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (options: { clientName: string; maxItems: number }) => void;
  isGenerating: boolean;
  sectorName: string;
  totalResults: number;
}

const ITEM_OPTIONS = [10, 20, 50] as const;
type ItemOption = (typeof ITEM_OPTIONS)[number];

const overlayVariants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

const cardVariants = {
  initial: { opacity: 0, scale: 0.95, y: 8 },
  animate: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.95, y: 8 },
};

const transition = { duration: 0.2, ease: "easeOut" as const };

export default function PdfOptionsModal({
  isOpen,
  onClose,
  onGenerate,
  isGenerating,
  sectorName,
  totalResults,
}: PdfOptionsModalProps) {
  const [clientName, setClientName] = useState("");
  const [maxItems, setMaxItems] = useState<ItemOption>(20);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus the text input when modal opens
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => inputRef.current?.focus(), 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Escape key closes modal
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isGenerating) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, isGenerating, onClose]);

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isGenerating) {
      onClose();
    }
  };

  const handleGenerate = () => {
    onGenerate({ clientName: clientName.trim(), maxItems });
  };

  const effectiveDefault: ItemOption =
    totalResults >= 20 ? 20 : totalResults >= 10 ? 10 : 10;

  // Initialise maxItems to the best available default when modal opens
  useEffect(() => {
    if (isOpen) {
      setMaxItems(effectiveDefault);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <FocusTrap
          focusTrapOptions={{
            escapeDeactivates: !isGenerating,
            onDeactivate: onClose,
            allowOutsideClick: true,
            returnFocusOnDeactivate: true,
            tabbableOptions: { displayCheck: "none" },
          }}
        >
        <motion.div
          key="pdf-modal-overlay"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          variants={overlayVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={transition}
          onClick={handleOverlayClick}
          aria-modal="true"
          role="dialog"
          aria-labelledby="pdf-modal-title"
          aria-describedby="pdf-modal-desc"
        >
          <motion.div
            id="pdf-modal-card"
            key="pdf-modal-card"
            className="bg-surface-0 border border-DEFAULT rounded-modal shadow-xl w-full max-w-md"
            variants={cardVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ ...transition, duration: 0.25 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between px-6 pt-6 pb-4 border-b border-DEFAULT">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-full bg-brand-blue-subtle flex items-center justify-center flex-shrink-0"
                  aria-hidden="true"
                >
                  <svg
                    className="w-5 h-5 text-brand-navy"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.75}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <div>
                  <h2
                    id="pdf-modal-title"
                    className="text-base font-semibold text-ink leading-tight"
                  >
                    Gerar Relatório PDF
                  </h2>
                  <p className="text-xs text-ink-muted mt-0.5">
                    Diagnóstico de Oportunidades em Licitações
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                disabled={isGenerating}
                className="p-1.5 rounded-button text-ink-muted hover:bg-surface-1 hover:text-ink transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Fechar modal"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-5">
              {/* Sector context */}
              <div className="flex items-center gap-2 px-3 py-2 bg-surface-1 rounded-input">
                <svg
                  className="w-3.5 h-3.5 text-ink-muted flex-shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                  />
                </svg>
                <span className="text-xs text-ink-secondary">
                  Setor:{" "}
                  <span className="font-medium text-ink">{sectorName}</span>
                  {totalResults > 0 && (
                    <span className="text-ink-muted ml-1">
                      — {totalResults.toLocaleString("pt-BR")} resultado
                      {totalResults !== 1 ? "s" : ""}
                    </span>
                  )}
                </span>
              </div>

              {/* Nome da empresa */}
              <div>
                <label
                  htmlFor="pdf-client-name"
                  className="block text-sm font-medium text-ink mb-1.5"
                >
                  Nome da empresa{" "}
                  <span className="text-ink-muted font-normal">(opcional)</span>
                </label>
                <input
                  ref={inputRef}
                  id="pdf-client-name"
                  type="text"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  placeholder="Ex: Empresa ABC Ltda"
                  maxLength={120}
                  disabled={isGenerating}
                  autoComplete="organization"
                  className="w-full px-3 py-2.5 rounded-button border border-DEFAULT bg-surface-0
                             text-sm text-ink placeholder:text-ink-muted
                             focus:outline-none focus:ring-2 focus:ring-brand-blue
                             disabled:opacity-50 disabled:cursor-not-allowed transition-shadow"
                />
                <p className="mt-1 text-xs text-ink-muted">
                  Aparece na capa e no rodapé do relatório.
                </p>
              </div>

              {/* Número de oportunidades */}
              <div>
                <fieldset>
                  <legend className="text-sm font-medium text-ink mb-2.5">
                    Número de oportunidades
                  </legend>
                  <div className="flex gap-2" role="group" aria-label="Selecione o número de oportunidades">
                    {ITEM_OPTIONS.map((option) => {
                      const isSelected = maxItems === option;
                      return (
                        <label
                          key={option}
                          className={[
                            "flex-1 flex items-center justify-center px-3 py-2.5 rounded-button border cursor-pointer",
                            "text-sm font-medium transition-colors select-none",
                            isGenerating
                              ? "border-DEFAULT text-ink-muted opacity-40 cursor-not-allowed"
                              : isSelected
                              ? "border-brand-navy bg-brand-navy text-white"
                              : "border-DEFAULT text-ink bg-surface-0 hover:bg-surface-1",
                          ].join(" ")}
                        >
                          <input
                            type="radio"
                            name="pdf-max-items"
                            value={option}
                            checked={isSelected}
                            disabled={isGenerating}
                            onChange={() => setMaxItems(option)}
                            className="sr-only"
                            aria-label={`${option} oportunidades`}
                          />
                          {option}
                        </label>
                      );
                    })}
                  </div>
                  <p className="mt-1.5 text-xs text-ink-muted">
                    O relatório incluirá até o número selecionado de oportunidades.
                  </p>
                </fieldset>
              </div>
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 pb-6">
              <button
                type="button"
                onClick={onClose}
                disabled={isGenerating}
                className="flex-1 px-4 py-2.5 rounded-button border border-DEFAULT
                           text-sm text-ink bg-surface-0
                           hover:bg-surface-1 transition-colors
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating || totalResults === 0}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-button
                           bg-brand-navy text-white text-sm font-medium
                           hover:opacity-90 transition-opacity
                           disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label={isGenerating ? "Gerando PDF, aguarde..." : "Gerar PDF"}
              >
                {isGenerating ? (
                  <>
                    <svg
                      className="w-4 h-4 animate-spin flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    <span>Gerando...</span>
                  </>
                ) : (
                  <>
                    <svg
                      className="w-4 h-4 flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <span>Gerar PDF</span>
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
        </FocusTrap>
      )}
    </AnimatePresence>
  );
}
