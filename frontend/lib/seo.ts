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
