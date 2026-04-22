'use client';

import { useEffect, useState } from 'react';

interface TableOfContentsProps {
  sections: { id: string; title: string }[];
}

/**
 * STORY-SEO-008 AC2: Sticky TOC sidebar for pillar pages.
 * Highlights the section currently in viewport.
 */
export default function TableOfContents({ sections }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (visible) setActiveId(visible.target.id);
      },
      { rootMargin: '-20% 0px -70% 0px', threshold: 0 },
    );

    for (const { id } of sections) {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    }

    return () => observer.disconnect();
  }, [sections]);

  return (
    <nav
      aria-label="Table of contents"
      className="sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto pr-4"
      data-testid="pillar-toc"
    >
      <h2 className="text-xs font-semibold uppercase tracking-wider text-ink-secondary mb-4">
        Neste guia
      </h2>
      <ol className="space-y-2 text-sm">
        {sections.map(({ id, title }) => {
          const isActive = activeId === id;
          return (
            <li key={id}>
              <a
                href={`#${id}`}
                className={
                  'block leading-snug border-l-2 pl-3 py-1 transition-colors ' +
                  (isActive
                    ? 'border-brand-blue text-brand-blue font-medium'
                    : 'border-[var(--border)] text-ink-secondary hover:text-ink hover:border-ink-secondary')
                }
              >
                {title}
              </a>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
