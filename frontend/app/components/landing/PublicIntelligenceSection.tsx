import Link from "next/link";
import { BRAND } from "@/lib/brand/system";
import { JOURNEYS } from "@/lib/conversion/journey";

const SURFACES = [
  { href: "/licitacoes", label: "Licitações", intent: JOURNEYS.tender.intent },
  { href: "/contratos", label: "Contratos", intent: JOURNEYS.contract.intent },
  { href: "/cnpj", label: "Empresas / CNPJ", intent: JOURNEYS.company.intent },
  { href: "/orgaos", label: "Órgãos", intent: JOURNEYS.organ.intent },
  { href: "/municipios", label: "Municípios", intent: JOURNEYS.municipality.intent },
  { href: "/observatorio", label: "Observatório", intent: JOURNEYS.observatory.intent },
] as const;

export default function PublicIntelligenceSection() {
  return (
    <section
      id="inteligencia-publica"
      data-testid="public-intelligence-section"
      className="relative mx-auto max-w-landing px-4 py-20 sm:px-6 sm:py-28 lg:px-8"
    >
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wide text-brand-blue">
          {BRAND.descriptor}
        </p>
        <h2 className="mt-3 text-3xl font-display font-bold tracking-tight text-ink sm:text-4xl">
          Seis superfícies públicas, um único plano de fatos
        </h2>
        <p className="mt-4 text-lg text-ink-secondary">
          Consulte o dado. Veja a fonte. Siga para a entidade seguinte.
          Se a decisão for comercial, a CONFENGE entra — sem trial e sem plano.
        </p>
      </div>
      <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SURFACES.map((surface) => (
          <li key={surface.href}>
            <Link
              href={surface.href}
              className="block h-full rounded-xl border border-border bg-surface-1 p-5 hover:border-brand-blue"
            >
              <h3 className="text-lg font-semibold text-ink">{surface.label}</h3>
              <p className="mt-2 text-sm text-ink-secondary">{surface.intent}</p>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
