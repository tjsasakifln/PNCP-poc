/**
 * SEO helpers — canonical URLs, breadcrumbs, freshness labels.
 *
 * Centralizes SEO utilities used across pSEO pages, content pages,
 * and structured data generators.
 */

export const SITE_URL = 'https://smartlic.tech';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

/**
 * Build a canonical URL for a given path.
 * Normalizes trailing slashes and ensures absolute URL on the production host.
 *
 * @example
 * buildCanonical('/ajuda') // 'https://smartlic.tech/ajuda'
 * buildCanonical('ajuda/')  // 'https://smartlic.tech/ajuda'
 * buildCanonical('/')       // 'https://smartlic.tech'
 */
export function buildCanonical(path: string): string {
  if (!path || path === '/') return SITE_URL;
  let normalized = path.trim();
  if (!normalized.startsWith('/')) normalized = `/${normalized}`;
  if (normalized.length > 1 && normalized.endsWith('/')) {
    normalized = normalized.replace(/\/+$/, '');
  }
  return `${SITE_URL}${normalized}`;
}

/**
 * Normalize breadcrumb items:
 * - Trims labels
 * - Converts relative `href` to absolute
 * - Drops items without label
 */
export function buildBreadcrumbs(items: BreadcrumbItem[]): BreadcrumbItem[] {
  return items
    .filter((it) => it && typeof it.label === 'string' && it.label.trim().length > 0)
    .map((it) => ({
      label: it.label.trim(),
      href: it.href
        ? it.href.startsWith('http')
          ? it.href
          : buildCanonical(it.href)
        : undefined,
    }));
}

/**
 * Return a human-readable Portuguese freshness label.
 *
 * Examples:
 *   "Atualizado há 2 minutos"
 *   "Atualizado há 3 horas"
 *   "Atualizado há 5 dias"
 *   "Atualizado agora"
 */
// ──────────────────────────────────────────────
// CONV-006b: Operational title & description builders
// Rule: "promessa operacional > educacional"
// ──────────────────────────────────────────────

export type PageTemplateType =
  | 'guia-transversal'
  | 'setorial'
  | 'pergunta'
  | 'fornecedor'
  | 'orgao'
  | 'contrato'
  | 'cnpj'
  | 'glossario'
  | 'inteligencia';

export interface OperationalContext {
  /** Tema principal, nome do setor, razão social, termo do glossário etc. */
  subject: string;
  /** Unidade federativa (UF) opcional */
  uf?: string;
  /** Nome legível da UF opcional */
  ufName?: string;
  /** Número de editais / contratos */
  count?: number;
  /** Valor formatado (ex: "R$ 1,2 mi") */
  value?: string;
  /** Nome do órgão */
  orgao?: string;
  /** CNPJ puro (apenas dígitos) */
  cnpj?: string;
  /** Objeto do contrato */
  objeto?: string;
  /** Nome do setor */
  sector?: string;
  /** Pergunta completa */
  question?: string;
}

/**
 * Build a search-engine-optimized title using the "promessa operacional > educacional" rule.
 *
 * @param template - The page type template to use
 * @param ctx - Contextual data to inject into the template
 * @returns A SERP-optimized title string (max ~60 chars recommended, but not enforced)
 *
 * @example
 * buildOperationalTitle('setorial', { subject: 'Saúde', uf: 'SP', ufName: 'São Paulo', count: 42 })
 * // => "Licitações de Saúde em SP: 42 editais abertos — veja os mais viáveis"
 */
export function buildOperationalTitle(
  template: PageTemplateType,
  ctx: OperationalContext,
): string {
  switch (template) {
    case 'guia-transversal':
      return `${ctx.subject}: encontre oportunidades reais para sua empresa`;

    case 'setorial':
      if (ctx.uf && ctx.count !== undefined) {
        return `Licitações de ${ctx.subject} em ${ctx.uf}: ${ctx.count} editais abertos — veja os mais viáveis`;
      }
      if (ctx.count !== undefined) {
        return `Licitações de ${ctx.subject}: ${ctx.count} editais abertos — veja os mais viáveis`;
      }
      return `Licitações de ${ctx.subject}: encontre editais viáveis agora`;

    case 'pergunta':
      if (ctx.question) {
        return `${ctx.question} Veja a resposta com dados reais das licitações públicas`;
      }
      return `${ctx.subject}: resposta com dados reais de licitações públicas`;

    case 'fornecedor':
      if (ctx.count !== undefined && ctx.value) {
        return `${ctx.subject} — ${ctx.count} contratos, ${ctx.value} em contratos públicos`;
      }
      if (ctx.value) {
        return `${ctx.subject} — ${ctx.value} em contratos públicos e oportunidades similares`;
      }
      return `${ctx.subject} — contratos públicos e oportunidades similares`;

    case 'orgao':
      if (ctx.value) {
        return `${ctx.subject} — ticket médio de ${ctx.value}, categorias compradas e editais abertos`;
      }
      return `${ctx.subject} — categorias compradas, ticket médio e editais abertos`;

    case 'contrato':
      if (ctx.objeto && ctx.orgao && ctx.value) {
        return `Contrato: ${ctx.objeto} — ${ctx.orgao}, ${ctx.value}`;
      }
      if (ctx.objeto && ctx.orgao) {
        return `Contrato: ${ctx.objeto} — ${ctx.orgao}`;
      }
      return `Contratos de ${ctx.subject}: veja oportunidades similares`;

    case 'cnpj':
      if (ctx.cnpj && ctx.count !== undefined && ctx.value) {
        return `CNPJ ${ctx.cnpj} — ${ctx.subject}: ${ctx.count} contratos, ${ctx.value} e oportunidades abertas`;
      }
      if (ctx.cnpj) {
        return `CNPJ ${ctx.cnpj} — ${ctx.subject}: contratos, concorrentes e oportunidades`;
      }
      return `${ctx.subject}: contratos, concorrentes e oportunidades em licitações públicas`;

    case 'glossario':
      return `${ctx.subject}: o que significa na prática e como aplicar ao seu segmento`;

    default:
      return ctx.subject;
  }
}

/**
 * Build a search-engine-optimized meta description using the
 * "promessa operacional > educacional" rule.
 *
 * @param template - The page type template to use
 * @param ctx - Contextual data to inject into the template
 * @returns A SERP-optimized description string (aim for 120-158 chars)
 *
 * @example
 * buildOperationalDescription('fornecedor', { subject: 'Empresa ABC Ltda', count: 47, value: 'R$ 5,2 mi' })
 * // => "Empresa ABC Ltda acumula 47 contratos públicos (R$ 5,2 mi). Veja padrões de compra, concorrentes e editais abertos no setor."
 */
export function buildOperationalDescription(
  template: PageTemplateType,
  ctx: OperationalContext,
): string {
  switch (template) {
    case 'guia-transversal':
      if (ctx.sector) {
        return `Descubra editais reais de ${ctx.subject} compatíveis com sua empresa no setor de ${ctx.sector}. Filtre por UF, valor e modalidade. Dado público verificável.`;
      }
      return `Descubra editais reais de ${ctx.subject} compatíveis com sua empresa. Filtre por UF, valor e modalidade. Dado público verificável.`;

    case 'setorial':
      if (ctx.uf && ctx.ufName && ctx.count !== undefined) {
        return `${ctx.count} editais de ${ctx.subject.toLowerCase()} abertos ${ctx.ufName ? 'em ' + ctx.ufName : 'no ' + ctx.uf} agora. Filtre por valor, modalidade e prazo — veja apenas os viáveis para sua empresa.`;
      }
      if (ctx.count !== undefined) {
        return `${ctx.count} editais de ${ctx.subject.toLowerCase()} abertos agora. Filtre por valor, modalidade e prazo — veja apenas os viáveis para sua empresa.`;
      }
      return `Editais de ${ctx.subject.toLowerCase()} abertos agora. Filtre por valor, modalidade e prazo — veja apenas os viáveis para sua empresa.`;

    case 'pergunta':
      if (ctx.sector) {
        return `Respondemos "${ctx.subject}" com dados reais do setor de ${ctx.sector}. Informação prática para sua decisão em licitações públicas.`;
      }
      return `Respondemos "${ctx.subject}" com dados reais de licitações públicas. Informação prática para sua decisão.`;

    case 'fornecedor':
      if (ctx.count !== undefined && ctx.value) {
        return `${ctx.subject} acumula ${ctx.count} contratos públicos (${ctx.value}) em fontes oficiais. Veja padrões de compra, concorrentes e editais abertos no setor.`;
      }
      return `Perfil de ${ctx.subject} com contratos públicos em fontes oficiais. Veja padrões de compra, concorrentes e oportunidades.`;

    case 'orgao':
      if (ctx.count !== undefined) {
        return `${ctx.subject} publicou ${ctx.count} licitações recentemente. Veja as categorias mais compradas, ticket médio e editais abertos agora.`;
      }
      return `${ctx.subject}: veja as categorias mais compradas, ticket médio e editais abertos. Dados oficiais do PNCP.`;

    case 'contrato':
      if (ctx.orgao && ctx.value) {
        return `Contrato de ${ctx.subject} firmado com ${ctx.orgao} no valor de ${ctx.value}. Veja contratos similares, fornecedores e oportunidades abertas no setor.`;
      }
      return `Contratos públicos de ${ctx.subject}: veja valores, órgãos contratantes e oportunidades abertas. Dados oficiais atualizados.`;

    case 'cnpj':
      if (ctx.count !== undefined && ctx.value) {
        return `CNPJ ${ctx.cnpj || ''} — ${ctx.subject} tem ${ctx.count} contratos públicos (${ctx.value}). Consulte concorrentes, órgãos contratantes e editais abertos no setor.`;
      }
      return `CNPJ ${ctx.cnpj || ''} — ${ctx.subject}. Consulte contratos públicos, concorrentes e editais abertos no setor de atuação.`;

    case 'glossario':
      if (ctx.sector) {
        return `${ctx.subject}: entenda o significado prático e como aplicar no seu segmento de ${ctx.sector}. Guia objetivo para tomada de decisão.`;
      }
      return `${ctx.subject}: entenda o significado prático e como aplicar no seu segmento. Guia objetivo para tomada de decisão.`;

    default:
      return ctx.subject;
  }
}

export function getFreshnessLabel(updatedAt: Date | string | number): string {
  const date = updatedAt instanceof Date ? updatedAt : new Date(updatedAt);
  if (Number.isNaN(date.getTime())) return 'Atualizado recentemente';

  const diffMs = Date.now() - date.getTime();
  const diffSec = Math.max(0, Math.floor(diffMs / 1000));

  if (diffSec < 60) return 'Atualizado agora';

  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) {
    return `Atualizado há ${diffMin} minuto${diffMin !== 1 ? 's' : ''}`;
  }

  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) {
    return `Atualizado há ${diffHours} hora${diffHours !== 1 ? 's' : ''}`;
  }

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) {
    return `Atualizado há ${diffDays} dia${diffDays !== 1 ? 's' : ''}`;
  }

  const diffMonths = Math.floor(diffDays / 30);
  if (diffMonths < 12) {
    return `Atualizado há ${diffMonths} ${diffMonths !== 1 ? 'meses' : 'mês'}`;
  }

  const diffYears = Math.floor(diffMonths / 12);
  return `Atualizado há ${diffYears} ano${diffYears !== 1 ? 's' : ''}`;
}
