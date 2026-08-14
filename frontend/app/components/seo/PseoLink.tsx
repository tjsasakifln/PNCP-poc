/**
 * Client link component that fires a pSEO analytics event on click.
 * CONV-009b (#1325).
 *
 * Usage (in server or client components):
 *   <PseoLink
 *     href="/consultoria-b2g?ref=contratos"
 *     eventName="pseo_alert_signup"
 *     sourceTemplate="contrato_page"
 *     setor="pavimentacao-asfaltica"
 *     uf="SC"
 *   >
 *     Testar 14 dias gratis
 *   </PseoLink>
 *
 * Zero breaking change — extends native Link props. All extra tracking
 * props are optional; the component passes through all standard Link
 * attributes unmodified.
 */

'use client';

import Link from 'next/link';
import { type ComponentProps, type ReactNode } from 'react';
import { trackPseoEvent, PseoEventName, PseoSourceTemplate } from '@/lib/analytics/pseo';

interface PseoLinkProps extends Omit<ComponentProps<typeof Link>, 'onClick'> {
  /** pSEO event to fire on click. */
  eventName: PseoEventName;
  /** Template/section identifier for event attribution. */
  sourceTemplate: PseoSourceTemplate;
  /** Entity identifier. */
  entityId?: string;
  /** Sector slug. */
  setor?: string;
  /** Two-letter UF code. */
  uf?: string;
  children: ReactNode;
}

/**
 * A link wrapper that fires a typed pSEO analytics event on click.
 * All standard Link props (className, href, etc.) pass through.
 * The onClick handler fires the event before delegating to the original
 * Link behavior — does NOT prevent default navigation.
 */
export function PseoLink({
  eventName,
  sourceTemplate,
  entityId,
  setor,
  uf,
  children,
  ...linkProps
}: PseoLinkProps) {
  const handleClick = () => {
    trackPseoEvent(eventName, {
      source_template: sourceTemplate,
      entity_id: entityId,
      setor,
      uf,
      destination: linkProps.href?.toString(),
    });
  };

  return (
    <Link {...linkProps} onClick={handleClick}>
      {children}
    </Link>
  );
}
