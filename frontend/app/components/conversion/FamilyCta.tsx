import Link from "next/link";
import { resolveJourney, type JourneyContext } from "@/lib/conversion/journey";
import { BRAND } from "@/lib/brand/system";

export function FamilyCta({ context }: { context: JourneyContext }) {
  const cta = resolveJourney(context);
  return (
    <section
      data-testid="family-cta"
      data-cta-id={cta.id}
      data-family={cta.family}
      className="mt-10 rounded-xl border border-border bg-surface-1 p-6"
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-secondary">
        {BRAND.descriptor}
      </p>
      <h2 className="mt-2 text-xl font-bold text-ink">{cta.label}</h2>
      <p className="mt-2 text-sm text-ink-secondary">{cta.helper}</p>
      <Link
        href={cta.href}
        data-cta-id={cta.id}
        className="mt-4 inline-flex min-h-[44px] items-center rounded-lg bg-brand-navy px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-blue"
      >
        {cta.label}
      </Link>
    </section>
  );
}
