/**
 * SEO-P2-010 (#995): Related-articles resolver.
 *
 * Maps a content context (sector / cluster / glossary / question / cnpj) to a
 * deterministic, semantically-related set of internal URLs. Drives the
 * <RelatedArticles /> server component for cross-linking between route
 * families (sector ↔ city ↔ glossário ↔ perguntas).
 *
 * Diversity: results are seeded by a hash of `currentUrl` so different pages
 * surface different subsets of the candidate pool — avoids the "every page
 * links to the same 6 URLs" anti-pattern flagged by site crawlers.
 *
 * CONV-017 (#1332): Interlinking journeys for entity pages. Adds
 * journey-specific context types (fornecedor, orgao, contrato, municipio) and
 * a resolveJourney() function that returns ordered, intent-progressive steps
 * instead of shuffled related links.
 */
import { BLOG_ARTICLES } from '@/lib/blog';
import { GLOSSARY_TERMS } from '@/lib/glossary-terms';
import { QUESTIONS } from '@/lib/questions';
import { SECTORS, getRelatedSectors } from '@/lib/sectors';

export type RelatedContextType =
  | 'sector'
  | 'cluster'
  | 'glossary'
  | 'question'
  | 'cnpj';

export interface RelatedContext {
  /** Type of the page asking for related links. */
  type: RelatedContextType;
  /**
   * Identifier within the type. For `sector` it's a sector slug/id; for
   * `glossary` it's the term slug; for `question` the question slug; for
   * `cluster` a cluster name (e.g. "pncp"); for `cnpj` the digits.
   */
  value: string;
  /** Path of the current page — excluded from results so we never self-link. */
  currentUrl: string;
  /** Optional UF for sector pages — biases results toward neighboring UFs. */
  uf?: string;
}

export interface RelatedLink {
  /** Descriptive anchor text — full title, never "leia mais". */
  title: string;
  /** Short context (1 sentence) shown under the title. */
  description?: string;
  /** Internal URL (relative path). */
  href: string;
  /** Tag for the badge in the UI. */
  kind: 'artigo' | 'pergunta' | 'glossario' | 'setor' | 'panorama' | 'ferramenta';
}

/* -------------------------------------------------------------------------- */
/* CONV-017 (#1332): Journey types for entity-page interlinking               */
/* -------------------------------------------------------------------------- */

/** Entity page types that support intent-progressive journeys. */
export type JourneyEntityType =
  | 'fornecedor'
  | 'orgao'
  | 'contrato'
  | 'municipio';

/**
 * A single step in an intent-progressive journey.
 * Ordered by commercial intent (most transactional → most exploratory).
 */
export interface JourneyStep {
  /** 1-based position in the journey (1–5). */
  position: number;
  /** Short heading for the link. */
  title: string;
  /** Descriptive text explaining why the user would take this step. */
  description: string;
  /** Internal URL. */
  href: string;
  /** Semantic type of the destination for analytics tracking. */
  destinationType: string;
  /** Emoji icon representing the step. */
  icon: string;
}

/**
 * Context for resolving an intent-progressive journey on entity pages.
 */
export interface JourneyContext {
  /** Entity type. */
  type: JourneyEntityType;
  /** Primary identifier (CNPJ, slug, or sector). */
  value: string;
  /** Current page path (excluded from self-linking). */
  currentUrl: string;
  /** Human-readable name of the entity. */
  name?: string;
  /** UF code (e.g. "SP", "RJ") for geography-biased links. */
  uf?: string;
  /** Human-readable UF name. */
  ufName?: string;
  /** Sector slug when known (e.g. "engenharia"). */
  sectorSlug?: string;
  /** Sector name when known. */
  sectorName?: string;
  /** Top buyer CNPJs for fornecedor/orgao pages (first = primary). */
  orgaoCnpjs?: string[];
  /** Top buyer names matching orgaoCnpjs. */
  orgaoNames?: string[];
}

/* -------------------------------------------------------------------------- */
/* Deterministic shuffle                                                      */
/* -------------------------------------------------------------------------- */

/** djb2 — small deterministic string hash (stable across server/client). */
function hashString(input: string): number {
  let h = 5381;
  for (let i = 0; i < input.length; i++) {
    h = ((h << 5) + h + input.charCodeAt(i)) | 0;
  }
  return h >>> 0;
}

/**
 * Stable shuffle: same `seed` always produces the same order, but different
 * seeds spread the candidate pool across pages.
 */
export function deterministicShuffle<T>(items: T[], seed: string): T[] {
  const out = items.slice();
  const baseSeed = hashString(seed);
  for (let i = out.length - 1; i > 0; i--) {
    const j = (baseSeed + i * 2654435761) % (i + 1);
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/* -------------------------------------------------------------------------- */
/* Resolvers per context type                                                 */
/* -------------------------------------------------------------------------- */

function uniqueByHref(links: RelatedLink[]): RelatedLink[] {
  const seen = new Set<string>();
  const out: RelatedLink[] = [];
  for (const link of links) {
    if (seen.has(link.href)) continue;
    seen.add(link.href);
    out.push(link);
  }
  return out;
}

function blogToLink(slug: string): RelatedLink | null {
  const article = BLOG_ARTICLES.find((a) => a.slug === slug);
  if (!article) return null;
  return {
    title: article.title,
    description: article.description,
    href: `/blog/${article.slug}`,
    kind: 'artigo',
  };
}

function glossaryToLink(slug: string): RelatedLink | null {
  const term = GLOSSARY_TERMS.find((t) => t.slug === slug);
  if (!term) return null;
  return {
    title: term.term,
    description:
      term.definition.length > 140
        ? term.definition.slice(0, 137) + '...'
        : term.definition,
    href: `/glossario/${term.slug}`,
    kind: 'glossario',
  };
}

function questionToLink(slug: string): RelatedLink | null {
  const q = QUESTIONS.find((qq) => qq.slug === slug);
  if (!q) return null;
  return {
    title: q.title,
    description: q.metaDescription,
    href: `/perguntas/${q.slug}`,
    kind: 'pergunta',
  };
}

function resolveSector(ctx: RelatedContext): RelatedLink[] {
  const sector = SECTORS.find(
    (s) => s.id === ctx.value || s.slug === ctx.value,
  );
  if (!sector) return [];

  const links: RelatedLink[] = [
    {
      title: `Panorama Nacional: ${sector.name}`,
      description: `Visão geral do mercado de ${sector.name.toLowerCase()} em licitações públicas.`,
      href: `/blog/panorama/${sector.slug}`,
      kind: 'panorama',
    },
    {
      title: `Licitações abertas de ${sector.name}`,
      description: sector.description,
      href: `/blog/programmatic/${sector.slug}`,
      kind: 'setor',
    },
    {
      title: `Contratos públicos de ${sector.name}`,
      description: `Histórico de contratos firmados no setor de ${sector.name.toLowerCase()}.`,
      href: `/blog/contratos/${sector.slug}`,
      kind: 'setor',
    },
  ];

  // Add 2-3 UF variants when we know the current UF.
  const ufCandidates = ['sp', 'rj', 'mg', 'rs', 'pr', 'sc', 'ba', 'pe', 'go', 'df'];
  for (const uf of ufCandidates) {
    if (uf === ctx.uf?.toLowerCase()) continue;
    links.push({
      title: `Licitações de ${sector.name} em ${uf.toUpperCase()}`,
      href: `/blog/licitacoes/${sector.slug}/${uf}`,
      kind: 'setor',
    });
  }

  // Add blog articles tagged for this sector via SECTOR_EDITORIAL_MAP from
  // RelatedPages — we rebuild a minimal version here to stay decoupled.
  const SECTOR_EDITORIAL: Record<string, string[]> = {
    informatica: [
      'inteligencia-artificial-consultoria-licitacao-2026',
      'nova-geracao-ferramentas-mercado-licitacoes',
    ],
    software: [
      'inteligencia-artificial-consultoria-licitacao-2026',
      'nova-geracao-ferramentas-mercado-licitacoes',
    ],
    engenharia: ['estruturar-setor-licitacao-5-milhoes'],
    saude: ['clausulas-escondidas-editais-licitacao'],
    facilities: ['reduzir-tempo-analisando-editais-irrelevantes'],
    vigilancia: ['empresas-vencem-30-porcento-pregoes'],
    transporte: ['pipeline-licitacoes-funil-comercial'],
  };
  for (const slug of SECTOR_EDITORIAL[sector.id] ?? []) {
    const link = blogToLink(slug);
    if (link) links.push(link);
  }

  return links;
}

function resolveCluster(ctx: RelatedContext): RelatedLink[] {
  // Pull articles whose tags or keywords reference the cluster keyword.
  const needle = ctx.value.toLowerCase();
  const matches = BLOG_ARTICLES.filter((a) => {
    const haystack = [
      ...(a.tags ?? []),
      ...(a.keywords ?? []),
      a.title,
      a.slug,
    ]
      .join(' ')
      .toLowerCase();
    return haystack.includes(needle);
  });

  return matches.map((a) => ({
    title: a.title,
    description: a.description,
    href: `/blog/${a.slug}`,
    kind: 'artigo' as const,
  }));
}

function resolveGlossary(ctx: RelatedContext): RelatedLink[] {
  const term = GLOSSARY_TERMS.find((t) => t.slug === ctx.value);
  const links: RelatedLink[] = [];

  // Related glossary terms — peer concepts.
  for (const slug of term?.relatedTerms ?? []) {
    const link = glossaryToLink(slug);
    if (link) links.push(link);
  }

  // Questions whose `relatedTerms` reference this term.
  const matchingQuestions = QUESTIONS.filter((q) =>
    q.relatedTerms.includes(ctx.value),
  ).slice(0, 4);
  for (const q of matchingQuestions) {
    links.push({
      title: q.title,
      description: q.metaDescription,
      href: `/perguntas/${q.slug}`,
      kind: 'pergunta',
    });
  }

  // Blog articles whose slug or keywords mention the term name.
  if (term) {
    const needle = term.term.toLowerCase();
    const blogMatches = BLOG_ARTICLES.filter((a) => {
      const haystack = [a.title, a.slug, ...(a.keywords ?? [])]
        .join(' ')
        .toLowerCase();
      return haystack.includes(needle);
    }).slice(0, 2);
    for (const a of blogMatches) {
      links.push({
        title: a.title,
        description: a.description,
        href: `/blog/${a.slug}`,
        kind: 'artigo',
      });
    }
  }

  return links;
}

function resolveQuestion(ctx: RelatedContext): RelatedLink[] {
  const q = QUESTIONS.find((qq) => qq.slug === ctx.value);
  if (!q) return [];

  const links: RelatedLink[] = [];

  // Related glossary terms.
  for (const slug of q.relatedTerms ?? []) {
    const link = glossaryToLink(slug);
    if (link) links.push(link);
  }

  // Related articles by explicit slug list.
  for (const slug of q.relatedArticles ?? []) {
    const link = blogToLink(slug);
    if (link) links.push(link);
  }

  // Sibling questions in the same category.
  const siblings = QUESTIONS.filter(
    (qq) => qq.category === q.category && qq.slug !== q.slug,
  ).slice(0, 4);
  for (const sib of siblings) {
    links.push({
      title: sib.title,
      description: sib.metaDescription,
      href: `/perguntas/${sib.slug}`,
      kind: 'pergunta',
    });
  }

  return links;
}

function resolveCnpj(ctx: RelatedContext): RelatedLink[] {
  // CNPJ pages are data-heavy; we surface evergreen tools and panoramas instead
  // of trying to find sibling CNPJs (that's a separate backend job).
  return [
    {
      title: 'Calculadora de Oportunidades B2G',
      description: 'Estime potencial em licitações para o seu CNPJ.',
      href: '/calculadora',
      kind: 'ferramenta',
    },
    {
      title: 'Comparador de Concorrentes',
      description: 'Compare seu CNPJ com fornecedores concorrentes.',
      href: '/comparador',
      kind: 'ferramenta',
    },
    {
      title: 'Glossário de Licitações',
      href: '/glossario',
      kind: 'glossario',
    },
    {
      title: 'Perguntas frequentes sobre PNCP',
      href: '/perguntas',
      kind: 'pergunta',
    },
  ];
}

/* -------------------------------------------------------------------------- */
/* CONV-017 (#1332): Journey resolvers per entity type                        */
/* -------------------------------------------------------------------------- */

/**
 * Jornada do Fornecedor — intenção progressiva.
 *
 * 1. Órgãos compradores  → transacional
 * 2. Setores de atuação   → exploratório-setorial
 * 3. Concorrentes         → inteligência competitiva
 * 4. Subcontratação       → parceria
 * 5. Relatório completo   → aprofundamento
 */
function resolveFornecedorJourney(ctx: JourneyContext): JourneyStep[] {
  const cnpj = ctx.value;
  const name = ctx.name ?? 'este fornecedor';

  // Step 1: link to top comprador orgão if available, else generic orgãos page.
  const orgaoHref = ctx.orgaoCnpjs?.[0]
    ? `/orgaos/${ctx.orgaoCnpjs[0]}`
    : '/orgaos';
  const orgaoTitle = ctx.orgaoCnpjs?.[0]
    ? `Órgãos compradores de ${name}`
    : 'Órgãos compradores do governo';

  // Step 2: link to setor if available, else generic licitacoes page.
  const setorHref = ctx.sectorSlug
    ? `/licitacoes/${ctx.sectorSlug}`
    : '/licitacoes';

  return [
    {
      position: 1,
      title: orgaoTitle,
      description: 'Conheça os órgãos que mais contratam esta empresa.',
      href: orgaoHref,
      destinationType: 'orgao',
      icon: '🏛️',
    },
    {
      position: 2,
      title: `Setores de atuação`,
      description: 'Descubra os setores onde esta empresa atua em licitações.',
      href: setorHref,
      destinationType: 'licitacoes',
      icon: '📋',
    },
    {
      position: 3,
      title: 'Concorrentes',
      description: 'Veja quem compete com esta empresa nos mesmos mercados.',
      href: `/intel-concorrente?cnpj=${cnpj}`,
      destinationType: 'concorrente',
      icon: '🔍',
    },
    {
      position: 4,
      title: 'Subcontratação',
      description: 'Identifique oportunidades de subcontratação com esta empresa.',
      href: '/subcontratacao/mapear',
      destinationType: 'subcontratacao',
      icon: '🤝',
    },
    {
      position: 5,
      title: 'Relatório completo',
      description: `Análise aprofundada de oportunidades B2G para ${name}.`,
      href: `/intel-reports/new?cnpj=${cnpj}`,
      destinationType: 'relatorio',
      icon: '📊',
    },
  ];
}

/**
 * Jornada do Órgão — intenção progressiva.
 *
 * 1. Categorias principais → transacional
 * 2. Fornecedores          → descoberta
 * 3. Contratos             → histórico
 * 4. Órgãos similares      → comparação
 * 5. Criar alerta          → conversão
 */
function resolveOrgaoJourney(ctx: JourneyContext): JourneyStep[] {
  const cnpj = ctx.value;
  const name = ctx.name ?? 'este órgão';

  // Step 1: link to setor if available, else generic licitacoes.
  const categoriasHref = ctx.sectorSlug
    ? `/licitacoes/${ctx.sectorSlug}`
    : '/licitacoes';

  // Step 4: link to orgaos filtered by UF.
  const similaresHref = ctx.uf
    ? `/orgaos?uf=${ctx.uf.toLowerCase()}`
    : '/orgaos';

  return [
    {
      position: 1,
      title: 'Categorias principais',
      description: `Veja as licitações por categoria que ${name} publica.`,
      href: categoriasHref,
      destinationType: 'licitacoes',
      icon: '📋',
    },
    {
      position: 2,
      title: `Fornecedores recorrentes`,
      description: 'Quem mais vence licitações e fornece para este órgão.',
      href: `/fornecedores/${cnpj}`,
      destinationType: 'fornecedor',
      icon: '🏢',
    },
    {
      position: 3,
      title: `Contratos do órgão`,
      description: 'Histórico completo de contratos firmados por este órgão.',
      href: `/contratos/orgao/${cnpj}`,
      destinationType: 'contrato',
      icon: '📄',
    },
    {
      position: 4,
      title: 'Órgãos similares',
      description: 'Compare com outros órgãos compradores na mesma região.',
      href: similaresHref,
      destinationType: 'orgao',
      icon: '🏛️',
    },
    {
      position: 5,
      title: 'Criar alerta',
      description: 'Receba notificações de novos editais publicados por este órgão.',
      href: `/consultoria-b2g?ref=orgao-${cnpj}`,
      destinationType: 'alerta',
      icon: '🔔',
    },
  ];
}

/**
 * Jornada do Contrato (setor × UF) — intenção progressiva.
 *
 * 1. Editais abertos agora → transacional
 * 2. Fornecedores ativos   → descoberta
 * 3. Órgãos compradores    → top buyers
 * 4. Setores relacionados  → adjacência
 * 5. Relatório             → aprofundamento
 */
function resolveContratoJourney(ctx: JourneyContext): JourneyStep[] {
  const { sectorSlug, uf, sectorName, ufName, value } = ctx;
  const sl = sectorSlug ?? value;
  const u = (uf ?? '').toLowerCase();

  // Step 4: related sectors for branching.
  const relatedSectors = getRelatedSectors(sl);
  const relatedSector = relatedSectors[0];

  return [
    {
      position: 1,
      title: `Editais abertos agora`,
      description: `Veja os editais abertos de ${sectorName ?? 'licitações'}${ufName ? ` em ${ufName}` : ''}.`,
      href: `/licitacoes/${sl}/${u}`,
      destinationType: 'licitacoes',
      icon: '📢',
    },
    {
      position: 2,
      title: `Fornecedores ativos`,
      description: `Fornecedores que atuam em ${sectorName ?? 'licitações'}${ufName ? ` ${ufName}` : ''}.`,
      href: `/fornecedores/${sl}/${u}`,
      destinationType: 'fornecedor',
      icon: '🏢',
    },
    {
      position: 3,
      title: 'Órgãos que mais compram',
      description: 'Os maiores compradores deste setor na região.',
      href: `/orgaos?uf=${u}`,
      destinationType: 'orgao',
      icon: '🏛️',
    },
    {
      position: 4,
      title: relatedSector
        ? `Setores relacionados: ${relatedSector.name}`
        : 'Setores relacionados',
      description: relatedSector
        ? `Explore contratos de ${relatedSector.name}${ufName ? ` em ${ufName}` : ''}.`
        : 'Veja contratos em outros setores.',
      href: relatedSector
        ? `/contratos/${relatedSector.slug}/${u}`
        : '/contratos',
      destinationType: 'contrato',
      icon: '📎',
    },
    {
      position: 5,
      title: 'Relatório de oportunidade',
      description: `Análise completa de oportunidades em ${sectorName ?? 'licitações'}${ufName ? ` ${ufName}` : ''}.`,
      href: `/intel-reports/new?sector=${sl}&uf=${u}`,
      destinationType: 'relatorio',
      icon: '📊',
    },
  ];
}

/**
 * Jornada do Município — intenção progressiva.
 *
 * 1. Editais abertos   → transacional
 * 2. Fornecedores      → descoberta
 * 3. Órgãos municipais → exploração
 * 4. Comparar          → benchmarking
 * 5. Alerta            → conversão
 */
function resolveMunicipioJourney(ctx: JourneyContext): JourneyStep[] {
  const { value: slug, name, uf } = ctx;
  const nome = name ?? slug;

  return [
    {
      position: 1,
      title: `Editais abertos em ${nome}`,
      description: `Veja as licitações públicas abertas em ${nome} agora.`,
      href: `/licitacoes?municipio=${slug}`,
      destinationType: 'licitacoes',
      icon: '📢',
    },
    {
      position: 2,
      title: `Fornecedores em ${nome}`,
      description: `Empresas que fornecem para órgãos em ${nome}.`,
      href: uf ? `/fornecedores?uf=${uf.toLowerCase()}&municipio=${slug}` : '/fornecedores',
      destinationType: 'fornecedor',
      icon: '🏢',
    },
    {
      position: 3,
      title: `Órgãos municipais`,
      description: `Órgãos públicos sediados em ${nome}.`,
      href: uf ? `/orgaos?uf=${uf.toLowerCase()}&municipio=${slug}` : '/orgaos',
      destinationType: 'orgao',
      icon: '🏛️',
    },
    {
      position: 4,
      title: 'Comparar municípios',
      description: 'Compare indicadores de licitações entre municípios.',
      href: `/comparador?municipio=${slug}`,
      destinationType: 'comparador',
      icon: '📊',
    },
    {
      position: 5,
      title: 'Criar alerta',
      description: `Receba alertas semanais de editais em ${nome}.`,
      href: `/consultoria-b2g?ref=municipio-${slug}`,
      destinationType: 'alerta',
      icon: '🔔',
    },
  ];
}

/* -------------------------------------------------------------------------- */
/* Public API                                                                  */
/* -------------------------------------------------------------------------- */

export interface ResolveOptions {
  /** Maximum links to return — defaults to 6, capped at 8 (anti-doorway). */
  limit?: number;
}

/**
 * Resolve up to `limit` semantically-related URLs for a given context.
 *
 * Guarantees:
 * - Never includes `ctx.currentUrl`.
 * - De-duplicated by `href`.
 * - Order is deterministic for a given `currentUrl` (server/client agree),
 *   but varies across pages (anti-doorway diversity).
 * - Capped at 8 links — issue #995 specifies 4-8.
 */
export function resolveRelated(
  ctx: RelatedContext,
  options: ResolveOptions = {},
): RelatedLink[] {
  const limit = Math.min(Math.max(options.limit ?? 6, 4), 8);

  let candidates: RelatedLink[];
  switch (ctx.type) {
    case 'sector':
      candidates = resolveSector(ctx);
      break;
    case 'cluster':
      candidates = resolveCluster(ctx);
      break;
    case 'glossary':
      candidates = resolveGlossary(ctx);
      break;
    case 'question':
      candidates = resolveQuestion(ctx);
      break;
    case 'cnpj':
      candidates = resolveCnpj(ctx);
      break;
    default:
      candidates = [];
  }

  const filtered = uniqueByHref(candidates).filter(
    (link) => link.href !== ctx.currentUrl,
  );

  // Deterministic shuffle for diversity, then cap.
  const shuffled = deterministicShuffle(filtered, ctx.currentUrl);
  return shuffled.slice(0, limit);
}

/**
 * CONV-017 (#1332): Resolve an intent-progressive journey for entity pages.
 *
 * Unlike resolveRelated(), this returns an ordered, non-shuffled sequence of
 * up to 5 steps that guides the user from transactional to exploratory pages.
 * Each step carries structured metadata for tracking and Schema.org markup.
 *
 * Guarantees:
 * - Always returns exactly 5 steps (may overshoot).
 * - Ordered by commercial intent (most actionable first).
 * - Never includes `ctx.currentUrl`.
 */
export function resolveJourney(ctx: JourneyContext): JourneyStep[] {
  let steps: JourneyStep[];
  switch (ctx.type) {
    case 'fornecedor':
      steps = resolveFornecedorJourney(ctx);
      break;
    case 'orgao':
      steps = resolveOrgaoJourney(ctx);
      break;
    case 'contrato':
      steps = resolveContratoJourney(ctx);
      break;
    case 'municipio':
      steps = resolveMunicipioJourney(ctx);
      break;
    default:
      steps = [];
  }

  // Filter out current page, limit to 5.
  return steps
    .filter((s) => s.href !== ctx.currentUrl)
    .slice(0, 5);
}
