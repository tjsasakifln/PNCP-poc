import { formatBRLCompact, formatBRL } from '@/lib/programmatic';

describe('formatBRLCompact', () => {
  // AC5: >= R$1B → compact "bi"
  it('formata bilhões com sufixo "bi"', () => {
    expect(formatBRLCompact(10_849_085_800)).toBe('R$10,8 bi');
  });

  it('formata exatamente R$1B', () => {
    expect(formatBRLCompact(1_000_000_000)).toBe('R$1,0 bi');
  });

  // AC6: >= R$1M → compact "mi"
  it('formata milhões com sufixo "mi"', () => {
    expect(formatBRLCompact(1_500_000)).toBe('R$1,5 mi');
  });

  it('formata exatamente R$1M', () => {
    expect(formatBRLCompact(1_000_000)).toBe('R$1,0 mi');
  });

  it('formata R$999.999 sem compact (abaixo de 1M)', () => {
    expect(formatBRLCompact(999_999)).toBe('R$\u00A0999.999');
  });

  // AC7: < R$1M → comportamento igual ao formatBRL (sem compact)
  it('formata R$750.000 sem compact notation', () => {
    expect(formatBRLCompact(750_000)).toBe(formatBRL(750_000));
  });

  it('formata zero sem compact notation', () => {
    expect(formatBRLCompact(0)).toBe(formatBRL(0));
  });

  it('formata R$500M (teto do cap de outlier) corretamente', () => {
    expect(formatBRLCompact(500_000_000)).toBe('R$500,0 mi');
  });
});
