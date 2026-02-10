/**
 * Tests for client-side term validation
 *
 * Tests the validation logic that mirrors backend filter.py:validate_terms()
 * to provide instant user feedback before search execution.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock Next.js modules
jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/buscar',
}));

jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line jsx-a11y/alt-text, @next/next/no-img-element
    return <img {...props} />;
  },
}));

// Mock the search page component
// We'll test the validation logic in isolation
describe('Term Validation', () => {
  const MIN_LENGTH = 4;
  const STOPWORDS_PT = new Set([
    'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas',
    'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas',
    'por', 'pelo', 'pela', 'pelos', 'pelas', 'para', 'pra', 'pro',
    'com', 'sem', 'sob', 'sobre', 'entre', 'ate', 'desde', 'apos',
    'perante', 'contra', 'ante',
    'ao', 'aos', 'num', 'numa', 'nuns', 'numas',
    'e', 'ou', 'mas', 'porem', 'que', 'se', 'como', 'quando', 'porque', 'pois',
  ]);

  const stripAccents = (s: string): string => {
    return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  };

  const isStopword = (word: string): boolean => {
    return STOPWORDS_PT.has(stripAccents(word.toLowerCase()));
  };

  interface TermValidation {
    valid: string[];
    ignored: string[];
    reasons: Record<string, string>;
  }

  const validateTermsClientSide = (terms: string[]): TermValidation => {
    const valid: string[] = [];
    const ignored: string[] = [];
    const reasons: Record<string, string> = {};

    terms.forEach(term => {
      const cleaned = term.trim().toLowerCase();

      // VALIDAÇÃO 1: Termo vazio
      if (!cleaned) {
        ignored.push(term);
        reasons[term] = 'Termo vazio ou apenas espaços';
        return;
      }

      // VALIDAÇÃO 2: Stopword (apenas single-word terms)
      const words = cleaned.split(/\s+/);
      if (words.length === 1 && isStopword(cleaned)) {
        ignored.push(term);
        reasons[term] = 'Palavra comum não indexada (stopword)';
        return;
      }

      // VALIDAÇÃO 3: Comprimento mínimo (apenas single-word terms)
      if (words.length === 1 && cleaned.length < MIN_LENGTH) {
        ignored.push(term);
        reasons[term] = `Muito curto (mínimo ${MIN_LENGTH} caracteres)`;
        return;
      }

      // VALIDAÇÃO 4: Caracteres especiais perigosos
      const hasInvalidChars = !Array.from(cleaned).every(c =>
        /[a-z0-9\s\-áéíóúàèìòùâêîôûãõñç]/i.test(c)
      );
      if (hasInvalidChars) {
        ignored.push(term);
        reasons[term] = 'Contém caracteres especiais não permitidos';
        return;
      }

      // Termo válido
      valid.push(term);
    });

    return { valid, ignored, reasons };
  };

  describe('validateTermsClientSide', () => {
    it('should accept valid single-word terms', () => {
      const result = validateTermsClientSide(['uniforme', 'fardamento', 'jaleco']);

      expect(result.valid).toEqual(['uniforme', 'fardamento', 'jaleco']);
      expect(result.ignored).toEqual([]);
    });

    it('should accept valid multi-word phrases', () => {
      const result = validateTermsClientSide(['uniforme escolar', 'terraplenagem de vias']);

      expect(result.valid).toEqual(['uniforme escolar', 'terraplenagem de vias']);
      expect(result.ignored).toEqual([]);
    });

    it('should reject empty terms', () => {
      const result = validateTermsClientSide(['uniforme', '', '  ']);

      expect(result.valid).toEqual(['uniforme']);
      expect(result.ignored).toEqual(['', '  ']);
      expect(result.reasons['']).toContain('vazio');
    });

    it('should reject single-word stopwords', () => {
      const result = validateTermsClientSide(['uniforme', 'de', 'para', 'com']);

      expect(result.valid).toEqual(['uniforme']);
      expect(result.ignored).toEqual(['de', 'para', 'com']);
      expect(result.reasons['de']).toContain('stopword');
    });

    it('should accept multi-word phrases containing stopwords', () => {
      const result = validateTermsClientSide(['serviço de limpeza', 'material para escritório']);

      expect(result.valid).toEqual(['serviço de limpeza', 'material para escritório']);
      expect(result.ignored).toEqual([]);
    });

    it('should reject terms shorter than MIN_LENGTH (single-word only)', () => {
      const result = validateTermsClientSide(['abc', 'uniforme']);

      expect(result.valid).toEqual(['uniforme']);
      expect(result.ignored).toEqual(['abc']);
      expect(result.reasons['abc']).toContain('curto');
      expect(result.reasons['abc']).toContain('4');
    });

    it('should accept multi-word phrases with short words', () => {
      const result = validateTermsClientSide(['via de acesso', 'ar condicionado']);

      // Multi-word phrases are NOT subject to min length check
      expect(result.valid).toEqual(['via de acesso', 'ar condicionado']);
      expect(result.ignored).toEqual([]);
    });

    it('should reject terms with special characters', () => {
      const result = validateTermsClientSide(['uniforme', 'termo@inválido', 'termo#especial']);

      expect(result.valid).toEqual(['uniforme']);
      expect(result.ignored).toEqual(['termo@inválido', 'termo#especial']);
      expect(result.reasons['termo@inválido']).toContain('caracteres especiais');
    });

    it('should accept terms with hyphens and accents', () => {
      const result = validateTermsClientSide(['pré-moldado', 'café-com-leite', 'João']);

      expect(result.valid).toEqual(['pré-moldado', 'café-com-leite', 'João']);
      expect(result.ignored).toEqual([]);
    });

    it('should handle mixed valid and invalid terms', () => {
      const result = validateTermsClientSide([
        'uniforme',
        'de',
        'abc',
        'terraplenagem',
        'para',
        'levantamento topográfico'
      ]);

      expect(result.valid).toEqual(['uniforme', 'terraplenagem', 'levantamento topográfico']);
      expect(result.ignored).toEqual(['de', 'abc', 'para']);
      expect(result.reasons['de']).toContain('stopword');
      expect(result.reasons['abc']).toContain('curto');
      expect(result.reasons['para']).toContain('stopword');
    });

    it('should handle case insensitivity', () => {
      const result = validateTermsClientSide(['UNIFORME', 'De', 'Para']);

      expect(result.valid).toEqual(['UNIFORME']);
      expect(result.ignored).toEqual(['De', 'Para']);
    });

    it('should strip accents for stopword detection', () => {
      const result = validateTermsClientSide(['após', 'até', 'uniforme']);

      // 'após' normalizes to 'apos' which is in STOPWORDS_PT
      expect(result.valid).toEqual(['uniforme']);
      expect(result.ignored).toContain('após');
    });
  });

  describe('Real-world query scenarios', () => {
    it('should validate typical construction terms', () => {
      const result = validateTermsClientSide([
        'terraplenagem',
        'pavimentação',
        'drenagem',
        'sinalização'
      ]);

      expect(result.valid.length).toBe(4);
      expect(result.ignored.length).toBe(0);
    });

    it('should validate facilities management terms', () => {
      const result = validateTermsClientSide([
        'limpeza',
        'conservação',
        'jardinagem',
        'portaria'
      ]);

      expect(result.valid.length).toBe(4);
      expect(result.ignored.length).toBe(0);
    });

    it('should validate IT procurement terms', () => {
      const result = validateTermsClientSide([
        'servidor',
        'notebook',
        'licença de software',
        'infraestrutura de rede'
      ]);

      expect(result.valid.length).toBe(4);
      expect(result.ignored.length).toBe(0);
    });

    it('should handle user attempting to search with only stopwords', () => {
      const result = validateTermsClientSide(['de', 'para', 'com', 'em']);

      expect(result.valid.length).toBe(0);
      expect(result.ignored.length).toBe(4);
      // UI should disable search button when valid.length === 0
    });

    it('should handle user input with trailing/leading spaces', () => {
      const result = validateTermsClientSide([
        '  uniforme  ',
        '\tjaleco\t',
        '  terraplenagem'
      ]);

      // Validation uses trim(), so all should be valid
      expect(result.valid.length).toBe(3);
      expect(result.ignored.length).toBe(0);
    });
  });
});
