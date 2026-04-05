import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import { buildBreadcrumbs, buildCanonical, type BreadcrumbItem } from '@/lib/seo';

interface BreadcrumbNavProps {
  items: BreadcrumbItem[];
  className?: string;
  /** If true, renders only the visual nav (no JSON-LD). Use when the page
   *  already emits its own BreadcrumbList schema elsewhere. */
  suppressSchema?: boolean;
}

/**
 * Accessible breadcrumb navigation with inline BreadcrumbList JSON-LD schema.
 *
 * Renders:
 *   - <nav aria-label="Breadcrumb"> with visual ">" separators
 *   - <script type="application/ld+json"> BreadcrumbList for rich results
 *
 * The last item is styled as bold and marked with aria-current="page".
 * Items with `href` are rendered as links; items without href render as span.
 *
 * @example
 * <BreadcrumbNav items={[
 *   { label: 'Início', href: '/' },
 *   { label: 'Guias', href: '/guias' },
 *   { label: 'Como avaliar' },
 * ]} />
 */
export default function BreadcrumbNav({
  items,
  className = '',
  suppressSchema = false,
}: BreadcrumbNavProps) {
  const normalized = buildBreadcrumbs(items);
  if (normalized.length === 0) return null;

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: normalized.map((it, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: it.label,
      ...(it.href ? { item: it.href } : {}),
    })),
  };

  // Fallback href for the current page (required by Schema.org)
  if (!normalized[normalized.length - 1].href) {
    (jsonLd.itemListElement[normalized.length - 1] as Record<string, unknown>).item =
      buildCanonical('/');
  }

  return (
    <>
      {!suppressSchema && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      )}
      <nav
        aria-label="Breadcrumb"
        className={`flex items-center gap-2 text-sm text-ink-secondary ${className}`}
      >
        <ol className="flex items-center gap-2 flex-wrap">
          {normalized.map((item, i) => {
            const isLast = i === normalized.length - 1;
            return (
              <li key={`${item.label}-${i}`} className="flex items-center gap-2">
                {i > 0 && (
                  <ChevronRight
                    className="w-4 h-4 text-ink-muted"
                    aria-hidden="true"
                  />
                )}
                {item.href && !isLast ? (
                  <Link
                    href={item.href}
                    className="hover:text-brand-blue transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 rounded px-1"
                  >
                    {item.label}
                  </Link>
                ) : (
                  <span
                    className={isLast ? 'font-semibold text-ink' : ''}
                    aria-current={isLast ? 'page' : undefined}
                  >
                    {item.label}
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    </>
  );
}
