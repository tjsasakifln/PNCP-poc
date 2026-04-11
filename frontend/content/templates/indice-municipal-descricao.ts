/**
 * STORY-436 AC4: Template editorial para páginas do Índice SmartLic de Transparência Municipal
 *
 * REGRAS EDITORIAIS (ver docs/editorial/estilo-guia.md):
 * - Apenas string concatenation — sem geração dinâmica por LLM neste arquivo
 * - Acentuação impecável (verificar: município não municipio, órgão não orgao)
 * - Voz jornalística — afirmações diretas baseadas em dados, sem hedging ("parece", "possivelmente")
 * - Números: formato brasileiro (1.234,56 — ponto para milhar, vírgula para decimal)
 * - Gate automático: validarContexto() verifica dados externos antes de renderizar
 *
 * GATE DE QUALIDADE AUTOMÁTICO — substitui revisão humana para dados de template:
 *   import { validarContexto } from '@/content/templates/indice-municipal-descricao';
 *   const erros = validarContexto(ctx);
 *   if (erros.length > 0) throw new Error(erros.join('\n'));
 */

export interface IndiceContext {
  municipio: string;          // Nome oficial IBGE (ex: "Florianópolis")
  uf: string;                 // Sigla (ex: "SC")
  uf_nome: string;            // Nome por extenso (ex: "Santa Catarina")
  indice_geral: number;       // 0-100 — pontuação composta
  rank_uf: number;            // Posição no ranking estadual (1 = melhor)
  total_municipios_uf: number; // Total de municípios com dados na UF
  rank_nacional: number;      // Posição no ranking nacional
  total_municipios_brasil: number; // Total com dados no Brasil
  periodo: string;            // Ex: "1º trimestre de 2026"
  total_editais: number;      // Editais publicados no período
  valor_total_brl: string;    // Ex: "R$ 12.345.678" — já formatado
  modalidade_principal: string; // Ex: "Pregão Eletrônico"
  pct_pregao: number;         // % de pregão eletrônico (0-100)
  destaques: string[];        // 1-3 observações positivas específicas ao município
  alertas: string[];          // 0-2 pontos de atenção (ex: prazo médio curto)
  metodologia_url: string;    // URL para página de metodologia
}

/** Descrição principal da página municipal (200-300 palavras) */
export function gerarDescricaoPrincipal(ctx: IndiceContext): string {
  const rankUfTexto =
    ctx.rank_uf === 1
      ? '1º lugar em ' + ctx.uf_nome
      : ctx.rank_uf + 'º lugar entre os municípios de ' + ctx.uf_nome;

  const rankNacionalTexto =
    ctx.rank_nacional <= 100
      ? 'Entre os 100 municípios com maior transparência no Brasil, ' +
        ctx.municipio + ' ocupa a posição ' + ctx.rank_nacional + 'º.'
      : ctx.municipio +
        ' está na posição ' +
        ctx.rank_nacional +
        'º no ranking nacional de transparência em contratações públicas.';

  return (
    ctx.municipio +
    ', em ' +
    ctx.uf_nome +
    ', recebeu nota ' +
    ctx.indice_geral.toFixed(1) +
    ' no Índice SmartLic de Transparência Municipal referente ao ' +
    ctx.periodo +
    '. A pontuação coloca o município em ' +
    rankUfTexto +
    ' com dados disponíveis para análise.' +
    '\n\n' +
    'No período, ' +
    ctx.municipio +
    ' publicou ' +
    ctx.total_editais.toLocaleString('pt-BR') +
    ' editais no PNCP, totalizando ' +
    ctx.valor_total_brl +
    ' em contratações. ' +
    ctx.modalidade_principal +
    ' foi a modalidade mais utilizada, respondendo por ' +
    ctx.pct_pregao.toFixed(0) +
    '% dos processos licitatórios.' +
    '\n\n' +
    rankNacionalTexto +
    '\n\n' +
    'O Índice SmartLic avalia cinco dimensões: volume de publicações, prazo entre publicação e abertura, ' +
    'adesão ao Pregão Eletrônico, regularidade das publicações e completude das informações. ' +
    'A metodologia completa está disponível em ' +
    ctx.metodologia_url +
    '.'
  );
}

/** Parágrafo de destaques positivos (1-3 itens) */
export function gerarTextodestaques(ctx: IndiceContext): string {
  if (ctx.destaques.length === 0) return '';

  const intro =
    ctx.destaques.length === 1
      ? 'Um ponto de destaque em ' + ctx.municipio + ': '
      : 'Os principais pontos de destaque em ' + ctx.municipio + ': ';

  return intro + ctx.destaques.join('; ') + '.';
}

/** Parágrafo de alertas/pontos de atenção */
export function gerarTextoAlertas(ctx: IndiceContext): string {
  if (ctx.alertas.length === 0) return '';

  return (
    'Pontos que merecem atenção: ' +
    ctx.alertas.join('; ') +
    '. Empresas que acompanham ' +
    ctx.municipio +
    ' devem considerar esses fatores na análise de viabilidade de propostas.'
  );
}

// ─── Gate de Qualidade Automático ────────────────────────────────────────────

/**
 * Termos proibidos que revelam geração automática de texto.
 * Espelho do lint-text.js — aplicado a strings dinâmicas em runtime.
 */
const PROHIBITED_PATTERNS: ReadonlyArray<{ re: RegExp; label: string }> = [
  { re: /é\s+importante\s+(notar|ressaltar|destacar)/i, label: 'é importante notar/ressaltar' },
  { re: /vale\s+ressaltar/i,         label: 'vale ressaltar' },
  { re: /fica\s+evidente\s+que/i,    label: 'fica evidente que' },
  { re: /no\s+contexto\s+atual/i,    label: 'no contexto atual' },
  { re: /de\s+forma\s+significativa/i, label: 'de forma significativa' },
  { re: /ao\s+longo\s+do\s+tempo/i,  label: 'ao longo do tempo' },
  { re: /é\s+fundamental/i,          label: 'é fundamental' },
  { re: /\bem\s+suma\b/i,            label: 'em suma' },
  { re: /\bem\s+resumo\b/i,          label: 'em resumo' },
  { re: /cabe\s+mencionar/i,         label: 'cabe mencionar' },
  { re: /tendo\s+em\s+vista/i,       label: 'tendo em vista' },
  { re: /apresentou\s+um\s+aumento/i, label: 'apresentou um aumento' },
  { re: /verificou-se\s+que/i,       label: 'verificou-se que' },
  { re: /\brobusto\b/i,              label: 'robusto (vago)' },
  { re: /evidencia-se/i,             label: 'evidencia-se' },
  { re: /destaque-se/i,              label: 'destaque-se' },
  { re: /pode-se\s+observar/i,       label: 'pode-se observar' },
  { re: /é\s+possível\s+notar/i,     label: 'é possível notar' },
];

/** Erros comuns de acentuação que o lint captura, replicados para runtime. */
const ACCENT_ERRORS: ReadonlyArray<{ re: RegExp; label: string }> = [
  { re: /\bmunicipio\b/i,    label: '"municipio" sem acento (deve ser "município")' },
  { re: /\blicitacao\b/i,    label: '"licitacao" sem acento (deve ser "licitação")' },
  { re: /\borgao\b/i,        label: '"orgao" sem acento (deve ser "órgão")' },
  { re: /\banalise\b/i,      label: '"analise" sem acento (deve ser "análise")' },
  { re: /\bperiodo\b/i,      label: '"periodo" sem acento (deve ser "período")' },
  { re: /\bpagina\b/i,       label: '"pagina" sem acento (deve ser "página")' },
  { re: /\bindice\b/i,       label: '"indice" sem acento (deve ser "índice")' },
];

/** Markdown exposto que apareceria no HTML renderizado. */
const MARKDOWN_ARTIFACTS: ReadonlyArray<{ re: RegExp; label: string }> = [
  { re: /\*\*[^*]+\*\*/,   label: '**negrito** markdown exposto' },
  { re: /\*[^*\s][^*]*\*/, label: '*itálico* markdown exposto' },
  { re: /^#{1,6}\s/m,      label: '# cabeçalho markdown exposto' },
  { re: /_{2}[^_]+_{2}/,   label: '__negrito__ markdown exposto' },
];

/**
 * Valida os dados do contexto antes de renderizar.
 * Verifica campos dinâmicos (municipio, uf_nome, destaques, alertas, periodo)
 * contra termos proibidos, erros de acentuação e artefatos de markdown.
 *
 * @returns Array de strings descrevendo violações encontradas. Array vazio = OK.
 *
 * @example
 *   const erros = validarContexto(ctx);
 *   if (erros.length > 0) {
 *     console.error('Conteúdo bloqueado pelo gate editorial:', erros);
 *     throw new Error('Gate editorial falhou: ' + erros[0]);
 *   }
 */
export function validarContexto(ctx: IndiceContext): string[] {
  const erros: string[] = [];
  const allPatterns = [...PROHIBITED_PATTERNS, ...ACCENT_ERRORS, ...MARKDOWN_ARTIFACTS];

  const checkField = (value: string, fieldName: string) => {
    for (const { re, label } of allPatterns) {
      if (re.test(value)) {
        erros.push(`[${fieldName}] Violação editorial: "${label}" encontrado em: "${value.slice(0, 80)}"`);
      }
    }
  };

  // Verificar campos de texto livre (onde dados externos podem entrar)
  checkField(ctx.municipio, 'municipio');
  checkField(ctx.uf_nome, 'uf_nome');
  checkField(ctx.periodo, 'periodo');
  checkField(ctx.modalidade_principal, 'modalidade_principal');

  for (let i = 0; i < ctx.destaques.length; i++) {
    checkField(ctx.destaques[i], `destaques[${i}]`);
  }
  for (let i = 0; i < ctx.alertas.length; i++) {
    checkField(ctx.alertas[i], `alertas[${i}]`);
  }

  // Validar tipos numéricos (previne dados corrompidos)
  if (ctx.indice_geral < 0 || ctx.indice_geral > 100) {
    erros.push(`[indice_geral] Valor fora do intervalo 0-100: ${ctx.indice_geral}`);
  }
  if (ctx.pct_pregao < 0 || ctx.pct_pregao > 100) {
    erros.push(`[pct_pregao] Valor fora do intervalo 0-100: ${ctx.pct_pregao}`);
  }
  if (ctx.total_editais < 0) {
    erros.push(`[total_editais] Valor negativo: ${ctx.total_editais}`);
  }
  if (ctx.rank_uf < 1 || ctx.rank_nacional < 1) {
    erros.push(`[rank] Ranking deve ser >= 1. rank_uf=${ctx.rank_uf}, rank_nacional=${ctx.rank_nacional}`);
  }

  // Validar que valor_total_brl tem formato brasileiro
  if (!ctx.valor_total_brl.startsWith('R$')) {
    erros.push(`[valor_total_brl] Deve começar com "R$": "${ctx.valor_total_brl}"`);
  }

  return erros;
}

/** Título da página (60-70 chars) */
export function gerarTitulo(ctx: IndiceContext): string {
  return (
    'Índice de Transparência — ' +
    ctx.municipio +
    ' (' +
    ctx.uf +
    ') | SmartLic'
  );
}

/** Meta description (150-160 chars) */
export function gerarMetaDescription(ctx: IndiceContext): string {
  const desc =
    ctx.municipio +
    ' tem nota ' +
    ctx.indice_geral.toFixed(1) +
    ' no Índice SmartLic (' +
    ctx.periodo +
    '). ' +
    ctx.total_editais.toLocaleString('pt-BR') +
    ' editais publicados, valor total ' +
    ctx.valor_total_brl +
    '. Rank ' +
    ctx.rank_nacional +
    'º nacional.';

  // Truncar em 160 chars preservando a última palavra completa
  if (desc.length <= 160) return desc;
  return desc.slice(0, 157) + '...';
}
