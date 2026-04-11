/**
 * STORY-436 AC4: Template editorial para páginas do Índice SmartLic de Transparência Municipal
 *
 * REGRAS EDITORIAIS (ver docs/editorial/estilo-guia.md):
 * - Apenas string concatenation — sem geração dinâmica por LLM neste arquivo
 * - Acentuação impecável (verificar: município não municipio, órgão não orgao)
 * - Voz jornalística — afirmações diretas baseadas em dados, sem hedging ("parece", "possivelmente")
 * - Números: formato brasileiro (1.234,56 — ponto para milhar, vírgula para decimal)
 * - Revisão humana obrigatória antes de publicar qualquer variação nova
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
