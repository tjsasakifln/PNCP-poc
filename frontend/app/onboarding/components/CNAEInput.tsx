"use client";

import { useState, useEffect, useRef } from "react";
import { Input } from "../../../components/ui/Input";
import { Label } from "../../../components/ui/Label";
import { CNAE_SUGGESTIONS } from "./types";

export function CNAEInput({
  value,
  onChange,
  onBlur,
  error,
}: {
  value: string;
  onChange: (val: string) => void;
  onBlur?: () => void;
  error?: string;
}) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState(CNAE_SUGGESTIONS.slice());
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const query = value.toLowerCase().trim();
    if (!query) {
      setFilteredSuggestions(CNAE_SUGGESTIONS.slice());
      return;
    }
    setFilteredSuggestions(
      CNAE_SUGGESTIONS.filter(
        (s) => s.code.toLowerCase().includes(query) || s.label.toLowerCase().includes(query)
      )
    );
  }, [value]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={wrapperRef} className="relative">
      <Label required>Segmento / CNAE</Label>
      <Input
        id="cnae"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        onFocus={() => setShowSuggestions(true)}
        placeholder="Ex: Comércio de uniformes, 4781, Limpeza..."
        autoComplete="off"
        error={error}
        errorTestId="cnae-error"
      />
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div className="absolute z-10 mt-1 w-full bg-[var(--surface-0)] border border-[var(--border)] rounded-lg shadow-lg max-h-48 overflow-y-auto">
          {filteredSuggestions.map((s) => (
            <button
              key={s.code}
              onClick={() => {
                onChange(`${s.code} — ${s.label}`);
                setShowSuggestions(false);
              }}
              className="w-full px-3 py-2 text-left text-sm hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="font-mono text-[var(--brand-blue)]">{s.code}</span>
              <span className="text-[var(--ink-secondary)] ml-2">{s.label}</span>
            </button>
          ))}
        </div>
      )}
      <p className="text-xs text-[var(--ink-secondary)] mt-1">
        Aceita CNAE (ex: 4781-4/00) ou texto livre (ex: &quot;Uniformes escolares&quot;)
      </p>
    </div>
  );
}
