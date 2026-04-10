import { stripMarkdown } from '@/lib/text';

describe('stripMarkdown', () => {
  it('returns empty string for falsy input', () => {
    expect(stripMarkdown('')).toBe('');
  });

  it('removes bold markers', () => {
    expect(stripMarkdown('Texto com **negrito** aqui.')).toBe(
      'Texto com negrito aqui.'
    );
  });

  it('removes italic markers', () => {
    expect(stripMarkdown('Texto com *itálico* aqui.')).toBe(
      'Texto com itálico aqui.'
    );
  });

  it('removes inline code', () => {
    expect(stripMarkdown('Use a função `getQuestionBySlug`.')).toBe(
      'Use a função getQuestionBySlug.'
    );
  });

  it('extracts link text from markdown links', () => {
    expect(stripMarkdown('Veja o [PNCP](https://pncp.gov.br) oficial.')).toBe(
      'Veja o PNCP oficial.'
    );
  });

  it('strips bullet list markers', () => {
    expect(
      stripMarkdown('Itens:\n- primeiro\n- segundo\n- terceiro')
    ).toBe('Itens: primeiro segundo terceiro');
  });

  it('strips numbered list markers', () => {
    expect(
      stripMarkdown('Etapas:\n1. Publicação\n2. Habilitação\n3. Adjudicação')
    ).toBe('Etapas: Publicação Habilitação Adjudicação');
  });

  it('strips heading markers', () => {
    expect(stripMarkdown('## Principais hipóteses de dispensa')).toBe(
      'Principais hipóteses de dispensa'
    );
  });

  it('strips blockquote markers', () => {
    expect(stripMarkdown('> Citação importante aqui.')).toBe(
      'Citação importante aqui.'
    );
  });

  it('handles complex content with all marker types', () => {
    const input =
      '**Importante:** Conforme a [Lei 14.133](https://lei.gov.br/14133), o processo segue:\n\n' +
      '1. **Publicação** no `PNCP`\n' +
      '2. **Habilitação** dos licitantes\n' +
      '3. *Análise* das propostas';
    const expected =
      'Importante: Conforme a Lei 14.133, o processo segue: ' +
      'Publicação no PNCP Habilitação dos licitantes Análise das propostas';
    expect(stripMarkdown(input)).toBe(expected);
  });

  it('collapses multiple whitespace into single space', () => {
    expect(stripMarkdown('um   dois\n\n\ntrês')).toBe('um dois três');
  });

  it('preserves accents during stripping', () => {
    expect(stripMarkdown('**Licitação** e **órgão público**')).toBe(
      'Licitação e órgão público'
    );
  });

  it('handles table cells by flattening with spaces', () => {
    const table = '| Modalidade | Prazo |\n|---|---|\n| Pregão | 8 dias |';
    expect(stripMarkdown(table)).toBe('Modalidade Prazo Pregão 8 dias');
  });
});
