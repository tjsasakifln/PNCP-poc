/**
 * GTM-005: Analysis Examples Data Tests
 *
 * Validates curated data integrity, type safety, and utility functions.
 */

import {
  ANALYSIS_EXAMPLES,
  CATEGORY_META,
  DECISION_META,
  SECTION_COPY,
  formatCurrency,
  getScoreColor,
  type AnalysisExample,
  type DecisionType,
  type CategoryId,
} from '@/lib/data/analysisExamples';

describe('Analysis Examples Data', () => {
  // AC1: 3-5 real examples
  it('should have between 3 and 5 examples', () => {
    expect(ANALYSIS_EXAMPLES.length).toBeGreaterThanOrEqual(3);
    expect(ANALYSIS_EXAMPLES.length).toBeLessThanOrEqual(5);
  });

  // AC11: Static data (hardcoded array)
  it('should be a static array (not empty)', () => {
    expect(Array.isArray(ANALYSIS_EXAMPLES)).toBe(true);
    expect(ANALYSIS_EXAMPLES.length).toBe(5);
  });

  // AC2: Each card has structured analysis
  describe('each example has complete structure', () => {
    ANALYSIS_EXAMPLES.forEach((example) => {
      describe(`${example.id}`, () => {
        it('has required top-level fields', () => {
          expect(example.id).toBeTruthy();
          expect(example.title).toBeTruthy();
          expect(example.uf).toMatch(/^[A-Z]{2}$/);
          expect(example.value).toBeGreaterThan(0);
          expect(example.category).toBeTruthy();
        });

        it('has complete analysis section', () => {
          expect(example.analysis.timeline).toBeTruthy();
          expect(example.analysis.requirements).toBeTruthy();
          expect(example.analysis.competitiveness).toBeTruthy();
          expect(example.analysis.score).toBeGreaterThanOrEqual(0);
          expect(example.analysis.score).toBeLessThanOrEqual(10);
        });

        // AC4: Decisions are specific and actionable
        it('has complete decision section', () => {
          expect(example.decision.recommendation).toBeTruthy();
          expect(example.decision.justification).toBeTruthy();
          expect(['go', 'evaluate', 'no_go']).toContain(example.decision.type);
          // Justification should be actionable (at least 20 chars)
          expect(example.decision.justification.length).toBeGreaterThan(20);
        });

        it('has valid category reference', () => {
          expect(CATEGORY_META[example.category]).toBeDefined();
        });
      });
    });
  });

  // AC5: Zero fictional person testimonials
  it('should contain no fictional person names', () => {
    const bannedNames = [
      'Carlos Mendes',
      'Ana Paula Silva',
      'Roberto Santos',
      'Joao Silva',
      'Maria Santos',
      'Carlos Oliveira',
      'Ana Costa',
    ];

    const allText = ANALYSIS_EXAMPLES.map(
      (e) =>
        `${e.title} ${e.decision.recommendation} ${e.decision.justification}`
    ).join(' ');

    bannedNames.forEach((name) => {
      expect(allText.toLowerCase()).not.toContain(name.toLowerCase());
    });
  });

  // All unique IDs
  it('should have unique IDs', () => {
    const ids = ANALYSIS_EXAMPLES.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  // Categories cover multiple sectors
  it('should cover at least 3 different categories', () => {
    const categories = new Set(ANALYSIS_EXAMPLES.map((e) => e.category));
    expect(categories.size).toBeGreaterThanOrEqual(3);
  });

  // Decision types cover multiple outcomes
  it('should include at least 2 different decision types', () => {
    const types = new Set(ANALYSIS_EXAMPLES.map((e) => e.decision.type));
    expect(types.size).toBeGreaterThanOrEqual(2);
  });
});

describe('CATEGORY_META', () => {
  const categories: CategoryId[] = [
    'uniformes',
    'facilities',
    'epi',
    'elevadores',
    'saude',
  ];

  categories.forEach((cat) => {
    it(`has metadata for ${cat}`, () => {
      const meta = CATEGORY_META[cat];
      expect(meta.label).toBeTruthy();
      expect(meta.color).toMatch(/^text-/);
      expect(meta.bgColor).toMatch(/^bg-/);
    });
  });
});

describe('DECISION_META', () => {
  const types: DecisionType[] = ['go', 'evaluate', 'no_go'];

  types.forEach((type) => {
    it(`has metadata for ${type}`, () => {
      const meta = DECISION_META[type];
      expect(meta.label).toBeTruthy();
      expect(meta.color).toMatch(/^text-/);
      expect(meta.bgColor).toMatch(/^bg-/);
    });
  });
});

describe('SECTION_COPY', () => {
  it('has title and subtitle', () => {
    expect(SECTION_COPY.title).toBeTruthy();
    expect(SECTION_COPY.subtitle).toBeTruthy();
  });

  // AC3: Clear narrative flow
  it('has 3-step flow (Procurement -> Analysis -> Decision)', () => {
    expect(SECTION_COPY.flow).toHaveLength(3);
  });
});

describe('formatCurrency', () => {
  it('formats millions with M suffix', () => {
    expect(formatCurrency(1_200_000)).toBe('R$ 1.2M');
    expect(formatCurrency(2_500_000)).toBe('R$ 2.5M');
  });

  it('formats thousands with K suffix', () => {
    expect(formatCurrency(450_000)).toBe('R$ 450K');
    expect(formatCurrency(85_000)).toBe('R$ 85K');
  });

  it('handles edge case at 1M boundary', () => {
    expect(formatCurrency(999_999)).toBe('R$ 1000K');
    expect(formatCurrency(1_000_000)).toBe('R$ 1.0M');
  });
});

describe('getScoreColor', () => {
  it('returns green for scores >= 7.5', () => {
    const result = getScoreColor(8.5);
    expect(result.bar).toContain('emerald');
  });

  it('returns amber for scores 5.0-7.4', () => {
    const result = getScoreColor(5.2);
    expect(result.bar).toContain('amber');
  });

  it('returns red for scores < 5.0', () => {
    const result = getScoreColor(4.8);
    expect(result.bar).toContain('red');
  });

  it('returns green for boundary score 7.5', () => {
    const result = getScoreColor(7.5);
    expect(result.bar).toContain('emerald');
  });

  it('returns amber for boundary score 5.0', () => {
    const result = getScoreColor(5.0);
    expect(result.bar).toContain('amber');
  });
});
