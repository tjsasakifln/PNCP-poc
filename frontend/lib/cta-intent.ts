/**
 * CRO-CTA-000: CTA Architecture by Search Intent
 *
 * Kills "Teste Gratis por 14 Dias" as default CTA for pSEO pages.
 * Each CtaPageType defines a CTA that answers:
 *   "What did the visitor just discover they can do RIGHT NOW,
 *    with no commitment, that delivers immediate value?"
 *
 * Reference: github.com/issues/1214
 * Frameworks: Schwartz Awareness Levels, StoryBrand, PAS, B=MAP, Hook Model
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * Awareness-based page type taxonomy for CTA selection.
 *
 * Each page type maps to a Schwartz awareness level:
 * - Unaware:  doesn't know the problem exists
 * - Problem Aware: knows the problem, doesn't know about solutions
 * - Solution Aware: knows about solutions, hasn't chosen one
 * - Product Aware: knows about the product, deciding to buy
 */
export type CtaPageType =
  | 'pncp-guia'
  | 'primeira-licitacao'
  | 'setorial-com-editais'
  | 'setorial-zero-editais'
  | 'contratos'
  | 'juridico-perguntas'
  | 'subcontratacao'
  | 'blog-generico'
  // CONV-002 (#1311): Entity page CTAs — NEVER "Ver planos" or "Teste grátis"
  | 'fornecedor-perfil'
  | 'orgao-perfil'
  | 'contrato-detalhe'
  | 'cnpj-investigacao'
  // CONV-001 (#1310): pSEO informational page CTAs
  | 'guia-geral'
  | 'perguntas-juridicas'
  | 'glossario';

/** Complete CTA configuration for a page type + context. */
export interface CtaConfig {
  /** The page type that generated this config */
  pageType: CtaPageType;
  /** H2/H3 headline — the promise / continuation of the visitor's mental sentence */
  headline: string;
  /** Supporting subtext (1-2 sentences) */
  subtext: string;
  /** Primary button label (max 5 words, ideally <= 4) */
  buttonText: string;
  /** Primary button href */
  buttonLink: string;
  /** Optional secondary action label (lighter visual weight) */
  secondaryText?: string;
  /** Optional secondary action href */
  secondaryLink?: string;
  /** Optional social proof line ("Consultorias ja usam") */
  socialProof?: string;
  /** Micro-filter config for pre-segmentation before email capture */
  microfiltro?: MicrofiltroConfig;
  /** When true, CTA emphasises monitoring/alertas over immediate search */
  monitoringCta?: boolean;
  /** Analytics campaign identifier (passed as utm_campaign) */
  campaign: string;
}

/** Pre-segmentation filter shown before the primary CTA on setorial pages. */
export interface MicrofiltroConfig {
  label: string;
  options: MicrofiltroOption[];
}

export interface MicrofiltroOption {
  value: string;
  label: string;
}

/** Dynamic context from the page that personalises CTA copy. */
export interface CtaContext {
  /** Sector name in Portuguese (e.g. "TI", "Saude") */
  setor?: string;
  /** UF name in Portuguese (e.g. "Sao Paulo", "Bahia") */
  uf?: string;
  /** Two-letter UF code (e.g. "SP", "BA") */
  ufCode?: string;
  /** Total edital/contract count for the current page */
  count?: number;
  /** URL slug for UTM tracking */
  slug: string;
  /** Total contract value (used for zero-editais pages) */
  totalValue?: number;
  /** Entity name for entity page CTAs (e.g. company name, agency name) */
  entityName?: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_SIGNUP_HREF = '/consultoria-b2g?source=blog&utm_source=blog&utm_medium=programmatic';

/** Portuguese preposition map for Brazilian states. */
const UF_PREPOSITIONS: Record<string, string> = {
  BA: 'na',   DF: 'no',  GO: 'em',  MG: 'em',  MS: 'em',  MT: 'em',
  PR: 'no',   RJ: 'no',  RS: 'no',  SC: 'em',  SP: 'em',  default: 'em',
};

function prepFor(ufCode?: string): string {
  if (!ufCode) return 'em';
  return UF_PREPOSITIONS[ufCode.toUpperCase()] ?? UF_PREPOSITIONS.default;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildSignupHref(slug: string, campaign: string): string {
  return `${DEFAULT_SIGNUP_HREF}&utm_campaign=${campaign}&utm_content=${encodeURIComponent(slug)}`;
}

function buildAlertHref(setor?: string, ufCode?: string): string {
  const params = new URLSearchParams();
  if (setor) params.set('setor', setor);
  if (ufCode) params.set('uf', ufCode);
  const qs = params.toString();
  const base = '/alertas-publicos';
  return qs ? `${base}?${qs}` : base;
}

// ---------------------------------------------------------------------------
// Per-type factories
// ---------------------------------------------------------------------------

function ctaPnpGuia(context: CtaContext): CtaConfig {
  return {
    pageType: 'pncp-guia',
    headline: 'O PNCP não filtra por setor. O SmartLic filtra.',
    subtext: 'Encontre editais do seu segmento em segundos com classificação por inteligência artificial.',
    buttonText: 'Ver editais do meu setor',
    buttonLink: buildSignupHref(context.slug, 'pncp-guia'),
    socialProof: 'Consultorias e assessorias já usam para qualificar prospects',
    campaign: 'pncp-guia',
  };
}

function ctaPrimeiraLicitacao(context: CtaContext): CtaConfig {
  return {
    pageType: 'primeira-licitacao',
    headline: 'Encontre sua primeira licitação viável',
    subtext: 'Receba um checklist gratuito e alertas automáticos de oportunidades compatíveis com seu perfil.',
    buttonText: 'Receber material gratuito',
    buttonLink: buildSignupHref(context.slug, 'primeira-licitacao'),
    secondaryText: 'Encontrar minha primeira oportunidade',
    secondaryLink: '/buscar',
    campaign: 'primeira-licitacao',
  };
}

function ctaSetorialComEditais(context: CtaContext): CtaConfig {
  const s = context.setor || 'seu setor';
  const count = context.count ?? 0;
  return {
    pageType: 'setorial-com-editais',
    headline: count > 0
      ? `${count} licitações de ${s} abertas agora`
      : `Licitações de ${s} abertas agora`,
    subtext: `Filtre por valor, modalidade e prazo. Veja a viabilidade real de cada edital com IA.`,
    buttonText: `Ver editais de ${s} abertos`,
    buttonLink: buildSignupHref(context.slug, 'setorial-editais'),
    microfiltro: {
      label: 'Filtrar por prioridade',
      options: [
        { value: 'todos', label: 'Todos os editais' },
        { value: 'viabilidade-alta', label: 'Alta viabilidade' },
        { value: 'maior-valor', label: 'Maior valor' },
      ],
    },
    socialProof: count > 0
      ? `${count} editais analisados por IA`
      : 'Centenas de editais analisados por IA',
    campaign: 'setorial-editais',
  };
}

function ctaSetorialZeroEditais(context: CtaContext): CtaConfig {
  const s = context.setor || 'o setor';
  const ufPrep = prepFor(context.ufCode);
  const ufName = context.uf || 'sua região';
  const totalValue = context.totalValue ?? 0;

  return {
    pageType: 'setorial-zero-editais',
    headline: totalValue > 0
      ? `Nenhum edital agora — mas R$ ${formatValueCrude(totalValue)} mi contratados em 12 meses`
      : `Nenhum edital agora — mas o mercado de ${s} continua ativo`,
    subtext: `Crie um alerta para ser notificado quando surgirem oportunidades de ${s} ${ufPrep} ${ufName}.`,
    buttonText: `Criar alerta para ${s} ${ufPrep} ${ufName}`,
    buttonLink: buildAlertHref(context.setor, context.ufCode),
    monitoringCta: true,
    campaign: 'setorial-zero-editais',
  };
}

function ctaContratos(context: CtaContext): CtaConfig {
  const s = context.setor || 'seu mercado';
  const count = context.count ?? 0;
  return {
    pageType: 'contratos',
    headline: 'Mapeie quem compra do seu setor no governo',
    subtext: count > 0
      ? `${count.toLocaleString('pt-BR')} contratos indexados por setor, órgão e valor. Descubra compradores recorrentes.`
      : 'Milhares de contratos indexados por setor, órgão e valor. Descubra compradores recorrentes.',
    buttonText: 'Mapear contratos do meu mercado',
    buttonLink: buildSignupHref(context.slug, 'contratos'),
    socialProof: 'Dados de 2M+ contratos históricos do PNCP',
    campaign: 'contratos',
  };
}

function ctaJuridicoPerguntas(context: CtaContext): CtaConfig {
  return {
    pageType: 'juridico-perguntas',
    headline: 'Este contrato vai vencer — monitore',
    subtext: 'Acompanhe vencimentos, termos e aditivos de contratos públicos com alertas inteligentes.',
    buttonText: 'Monitorar contratos do meu setor',
    buttonLink: buildSignupHref(context.slug, 'juridico-monitoramento'),
    monitoringCta: true,
    campaign: 'juridico-monitoramento',
  };
}

function ctaSubcontratacao(context: CtaContext): CtaConfig {
  return {
    pageType: 'subcontratacao',
    headline: 'Encontre contratos que podem precisar da sua empresa',
    subtext: 'Mapeie vencedores de licitações e contratos ativos para identificar oportunidades de subcontratação.',
    buttonText: 'Mapear oportunidades de subcontratação',
    buttonLink: buildSignupHref(context.slug, 'subcontratacao'),
    campaign: 'subcontratacao',
  };
}

function ctaBlogGenerico(context: CtaContext): CtaConfig {
  return {
    pageType: 'blog-generico',
    headline: 'Veja licitações reais do seu setor',
    subtext: 'Filtre por viabilidade real, receba alertas automáticos e exporte relatórios.',
    buttonText: 'Buscar licitações agora',
    buttonLink: buildSignupHref(context.slug, 'blog-generico'),
    campaign: 'blog-generico',
  };
}

// ---------------------------------------------------------------------------
// CONV-002 (#1311): Entity page CTA factories — NEVER "Ver planos" / "Teste grátis"
// ---------------------------------------------------------------------------

/**
 * Fornecedor perfil page — CTA continues investigation into commercial analysis.
 */
function ctaFornecedorPerfil(context: CtaContext): CtaConfig {
  const name = context.entityName || 'esta empresa';
  return {
    pageType: 'fornecedor-perfil',
    headline: `Análise comercial de ${name}`,
    subtext: 'Descubra oportunidades de subcontratação, concorrentes em licitações similares e órgãos que compram do mesmo segmento.',
    buttonText: 'Gerar análise comercial',
    buttonLink: buildSignupHref(context.slug, 'fornecedor-analise'),
    secondaryText: 'Ver editais do segmento',
    secondaryLink: context.setor ? `/licitações/${context.setor}` : '/buscar',
    campaign: 'fornecedor-analise',
  };
}

/**
 * Órgão perfil page — CTA leads to monitoring + active bids.
 */
function ctaOrgaoPerfil(context: CtaContext): CtaConfig {
  const name = context.entityName || 'este órgão';
  return {
    pageType: 'orgao-perfil',
    headline: `Acompanhe as licitações de ${name}`,
    subtext: 'Veja os editais abertos agora, históricos de compras e receba alertas automáticos de novas oportunidades.',
    buttonText: 'Ver editais deste órgão',
    buttonLink: buildSignupHref(context.slug, 'orgao-editais'),
    secondaryText: 'Criar alerta de novos editais',
    secondaryLink: `/alertas-públicos?órgão=${encodeURIComponent(name)}`,
    monitoringCta: true,
    campaign: 'orgao-editais',
  };
}

/**
 * Contrato detalhe page — CTA leads to similar contracts discovery.
 */
function ctaContratoDetalhe(context: CtaContext): CtaConfig {
  const count = context.count ?? 0;
  return {
    pageType: 'contrato-detalhe',
    headline: 'Encontre contratos semelhantes',
    subtext: count > 0
      ? `Mapeie ${count.toLocaleString('pt-BR')} contratos similares por setor, órgão comprador e região. Identifique padrões de compra.`
      : 'Mapeie contratos similares por setor, órgão comprador e região. Identifique padrões de compra.',
    buttonText: 'Explorar contratos similares',
    buttonLink: buildSignupHref(context.slug, 'contratos-similares'),
    secondaryText: 'Desbloquear órgãos compradores do segmento',
    secondaryLink: '/consultoria-b2g?ref=contratos-orgaos',
    socialProof: 'Dados de 2M+ contratos históricos do PNCP',
    campaign: 'contratos-similares',
  };
}

/**
 * CNPJ investigação page — CTA leads to competitive intelligence report.
 */
function ctaCnpjInvestigacao(context: CtaContext): CtaConfig {
  const name = context.entityName || 'esta empresa';
  return {
    pageType: 'cnpj-investigacao',
    headline: `Inteligência competitiva de ${name}`,
    subtext: 'Análise o padrão de vitórias, mapeie possíveis contratantes e identifique oportunidades de subcontratação.',
    buttonText: 'Analisar padrão de vitórias',
    buttonLink: buildSignupHref(context.slug, 'cnpj-intel'),
    secondaryText: 'Mapear possíveis contratantes',
    secondaryLink: `/cnpj/${context.slug}/contratantes`,
    campaign: 'cnpj-intel',
  };
}

// ---------------------------------------------------------------------------
// Crude helpers (no external deps to keep this file self-contained)
// ---------------------------------------------------------------------------

function formatValueCrude(value: number): string {
  if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(1);
  if (value >= 1_000_000) return (value / 1_000_000).toFixed(1);
  if (value >= 1_000) return (value / 1_000).toFixed(0);
  return value.toFixed(0);
}

function ctaGuiaGeral(context: CtaContext): CtaConfig {
  const s = context.setor || 'seu setor';
  return {
    pageType: 'guia-geral',
    headline: `Descubra quanto sua empresa pode faturar com licitações de ${s}`,
    subtext: 'Veja editais abertos, valores praticados e órgãos compradores — tudo classificado por setor com inteligência artificial.',
    buttonText: 'Ver oportunidades no meu setor',
    buttonLink: buildSignupHref(context.slug, 'guia-geral'),
    socialProof: 'Centenas de empresas já usam para prospectar no B2G',
    campaign: 'guia-geral',
  };
}

function ctaPerguntasJuridicas(context: CtaContext): CtaConfig {
  return {
    pageType: 'perguntas-juridicas',
    headline: 'Transforme dúvidas jurídicas em oportunidades de negócio',
    subtext: 'Monitore editais, contratos e aditivos do seu setor com alertas inteligentes e análise de viabilidade por IA.',
    buttonText: 'Monitorar oportunidades agora',
    buttonLink: buildSignupHref(context.slug, 'perguntas-juridicas'),
    monitoringCta: true,
    campaign: 'perguntas-juridicas',
  };
}

function ctaGlossario(context: CtaContext): CtaConfig {
  return {
    pageType: 'glossario',
    headline: 'Entenda o termo — e encontre licitações onde ele aparece',
    subtext: 'Cada termo do glossário representa um mercado real. Veja editais abertos com classificação por setor e viabilidade.',
    buttonText: 'Buscar licitações do meu setor',
    buttonLink: buildSignupHref(context.slug, 'glossario'),
    campaign: 'glossario',
  };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Return the CTA configuration for a given page type and dynamic context.
 *
 * Use this in page components to derive `CtaConfig` and pass to `<CtaIntent />`.
 *
 * @example
 *   const cta = getCtaByIntent('setorial-com-editais', { setor: 'TI', count: 42, slug: 'ti-sp' });
 *   // => <CtaIntent config={cta} variant="inline" />
 */
export function getCtaByIntent(pageType: CtaPageType, context: CtaContext): CtaConfig {
  switch (pageType) {
    case 'pncp-guia':
      return ctaPnpGuia(context);
    case 'primeira-licitacao':
      return ctaPrimeiraLicitacao(context);
    case 'setorial-com-editais':
      return ctaSetorialComEditais(context);
    case 'setorial-zero-editais':
      return ctaSetorialZeroEditais(context);
    case 'contratos':
      return ctaContratos(context);
    case 'juridico-perguntas':
      return ctaJuridicoPerguntas(context);
    case 'subcontratacao':
      return ctaSubcontratacao(context);
    case 'blog-generico':
      return ctaBlogGenerico(context);
    // CONV-002 (#1311): Entity page CTAs
    case 'fornecedor-perfil':
      return ctaFornecedorPerfil(context);
    case 'orgao-perfil':
      return ctaOrgaoPerfil(context);
    case 'contrato-detalhe':
      return ctaContratoDetalhe(context);
    case 'cnpj-investigacao':
      return ctaCnpjInvestigacao(context);
    // CONV-001 (#1310): pSEO informational page CTAs
    case 'guia-geral':
      return ctaGuiaGeral(context);
    case 'perguntas-juridicas':
      return ctaPerguntasJuridicas(context);
    case 'glossario':
      return ctaGlossario(context);
  }
}

/**
 * Returns true when the context indicates zero-edital state for a setorial page.
 *
 * Helper used by page components to determine which CtaPageType to request.
 */
export function isZeroEditais(count: number | undefined | null): boolean {
  return !count || count <= 0;
}
