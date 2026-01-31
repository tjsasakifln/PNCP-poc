"use client";

import { useState, useRef, useEffect } from "react";
import { useTheme, THEMES, type ThemeId } from "./ThemeProvider";

/**
 * Theme toggle component with preview on hover
 * Issue #116 - Dark mode preview before selection
 */
export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const [previewTheme, setPreviewTheme] = useState<ThemeId | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const previewTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setPreviewTheme(null);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      if (previewTimeoutRef.current) {
        clearTimeout(previewTimeoutRef.current);
      }
    };
  }, []);

  // Apply preview theme temporarily
  const handlePreview = (themeId: ThemeId) => {
    if (previewTimeoutRef.current) {
      clearTimeout(previewTimeoutRef.current);
    }

    setPreviewTheme(themeId);

    // Apply preview with temporary CSS class
    const themeConfig = THEMES.find(t => t.id === themeId);
    if (themeConfig) {
      document.documentElement.style.setProperty('--preview-canvas', themeConfig.canvas);
      document.documentElement.style.setProperty('--preview-ink', themeConfig.ink);
    }
  };

  const handlePreviewEnd = () => {
    // Delay clearing preview to allow smooth transition
    previewTimeoutRef.current = setTimeout(() => {
      setPreviewTheme(null);
      document.documentElement.style.removeProperty('--preview-canvas');
      document.documentElement.style.removeProperty('--preview-ink');
    }, 100);
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        type="button"
        aria-label="Alternar tema"
        aria-expanded={open}
        className="flex items-center gap-2 px-3 py-2 rounded-button border border-strong
                   bg-surface-0 text-ink-secondary
                   hover:border-accent transition-colors text-sm"
      >
        <span
          className="w-4 h-4 rounded-full border border-strong"
          style={{ backgroundColor: THEMES.find(t => t.id === theme)?.preview }}
        />
        <span className="hidden sm:inline">{THEMES.find(t => t.id === theme)?.label}</span>
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 rounded-card border border-strong
                        bg-surface-elevated shadow-sm z-50 overflow-hidden animate-fade-in">
          {/* Preview tooltip */}
          {previewTheme && (
            <div className="px-3 py-2 bg-brand-blue-subtle border-b border-strong">
              <p className="text-xs text-ink-secondary">
                Prévia: <span className="font-semibold text-ink">{THEMES.find(t => t.id === previewTheme)?.label}</span>
              </p>
            </div>
          )}

          {THEMES.map(t => (
            <button
              key={t.id}
              onClick={() => { setTheme(t.id); setOpen(false); setPreviewTheme(null); }}
              onMouseEnter={() => handlePreview(t.id)}
              onMouseLeave={handlePreviewEnd}
              type="button"
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm text-left
                         hover:bg-surface-1 transition-colors
                         ${theme === t.id ? "bg-brand-blue-subtle font-semibold" : ""}
                         ${previewTheme === t.id ? "ring-2 ring-brand-blue ring-inset" : ""}`}
              title={`Passe o mouse para prévia de ${t.label}`}
            >
              <span
                className="w-5 h-5 rounded-full border flex-shrink-0"
                style={{
                  backgroundColor: t.preview,
                  borderColor: theme === t.id ? "#116dff" : "var(--border-strong)",
                }}
              />
              <span className="text-ink flex-1">{t.label}</span>

              {/* Preview indicator */}
              {previewTheme === t.id && theme !== t.id && (
                <svg className="w-4 h-4 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}

              {/* Current theme indicator */}
              {theme === t.id && (
                <svg className="w-4 h-4 text-brand-blue" fill="currentColor" viewBox="0 0 20 20" aria-label="Tema selecionado">
                  <title>Tema selecionado</title>
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}

          {/* Help text */}
          <div className="px-4 py-2 bg-surface-1 border-t border-strong">
            <p className="text-xs text-ink-muted">
              Passe o mouse para visualizar
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
