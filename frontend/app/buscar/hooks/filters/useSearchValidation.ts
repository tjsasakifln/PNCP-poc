"use client";

import { useState, useEffect } from "react";
import type { ValidationErrors } from "../../../../app/types";
import { isStopword } from "../../../../lib/constants/stopwords";

export interface TermValidation {
  valid: string[];
  ignored: string[];
  reasons: Record<string, string>;
}

export function validateTermsClientSide(terms: string[]): TermValidation {
  const MIN_LENGTH = 4;
  const valid: string[] = [];
  const ignored: string[] = [];
  const reasons: Record<string, string> = {};

  terms.forEach(term => {
    const cleaned = term.trim().toLowerCase();
    if (!cleaned) { ignored.push(term); reasons[term] = "Termo vazio ou apenas espaços"; return; }
    const words = cleaned.split(/\s+/);
    if (words.length === 1 && isStopword(cleaned)) { ignored.push(term); reasons[term] = "Palavra comum não indexada (stopword)"; return; }
    if (words.length === 1 && cleaned.length < MIN_LENGTH) { ignored.push(term); reasons[term] = `Muito curto (mínimo ${MIN_LENGTH} caracteres)`; return; }
    const hasInvalidChars = !Array.from(cleaned).every(c => /[a-z0-9\s\-áéíóúàèìòùâêîôûãõñç]/i.test(c));
    if (hasInvalidChars) { ignored.push(term); reasons[term] = "Contém caracteres especiais não permitidos"; return; }
    valid.push(term);
  });

  return { valid, ignored, reasons };
}

interface UseSearchValidationParams {
  ufsSelecionadas: Set<string>;
  dataInicial: string;
  dataFinal: string;
  searchMode: "setor" | "termos";
  termosArray: string[];
  valorValid: boolean;
}

interface UseSearchValidationReturn {
  validationErrors: ValidationErrors;
  termValidation: TermValidation | null;
  canSearch: boolean;
  updateTermValidation: (terms: string[]) => void;
  addTerms: (newTerms: string[], clearResult: () => void) => string[];
  removeTerm: (termToRemove: string, clearResult: () => void) => string[];
}

export function useSearchValidation(
  params: UseSearchValidationParams,
): UseSearchValidationReturn {
  const { ufsSelecionadas, dataInicial, dataFinal, searchMode, termosArray, valorValid } = params;
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [termValidation, setTermValidation] = useState<TermValidation | null>(null);

  function validateForm(): ValidationErrors {
    const errors: ValidationErrors = {};
    if (ufsSelecionadas.size === 0) errors.ufs = "Selecione pelo menos um estado";
    if (dataFinal < dataInicial) errors.date_range = "Data final deve ser maior ou igual à data inicial";
    return errors;
  }

  const canSearch =
    Object.keys(validateForm()).length === 0 &&
    (searchMode === "setor" || (termosArray.length > 0 && (!termValidation || termValidation.valid.length > 0))) &&
    valorValid;

  useEffect(() => { setValidationErrors(validateForm()); }, [ufsSelecionadas, dataInicial, dataFinal]);

  const updateTermValidation = (terms: string[]) => {
    if (searchMode === "termos" && terms.length > 0) setTermValidation(validateTermsClientSide(terms));
    else setTermValidation(null);
  };

  useEffect(() => {
    if (searchMode === "termos") updateTermValidation(termosArray);
    else setTermValidation(null);
  }, [searchMode, termosArray]);

  const addTerms = (newTerms: string[], clearResult: () => void): string[] => {
    const updated = [...termosArray, ...newTerms.filter(t => !termosArray.includes(t))];
    updateTermValidation(updated);
    clearResult();
    return updated;
  };

  const removeTerm = (termToRemove: string, clearResult: () => void): string[] => {
    const updated = termosArray.filter(t => t !== termToRemove);
    updateTermValidation(updated);
    clearResult();
    return updated;
  };

  return { validationErrors, termValidation, canSearch, updateTermValidation, addTerms, removeTerm };
}
