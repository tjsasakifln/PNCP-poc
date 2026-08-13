import Link from "next/link";
import type { EntityEdge } from "@/lib/intelligence/types";

export function EntityGraphNav({
  title = "Continuar a descoberta",
  edges,
}: {
  title?: string;
  edges: EntityEdge[];
}) {
  if (edges.length === 0) return null;

  return (
    <nav data-testid="entity-graph-nav" aria-label={title} className="mt-8">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-secondary">
        {title}
      </h2>
      <ul className="mt-3 flex flex-wrap gap-2">
        {edges.map((edge) => (
          <li key={`${edge.kind}-${edge.href}`}>
            <Link
              href={edge.href}
              className="inline-flex items-center rounded-full border border-border bg-surface-1 px-3 py-1.5 text-sm text-ink hover:border-brand-blue hover:text-brand-blue"
            >
              <span className="mr-2 text-[10px] uppercase tracking-wide text-ink-secondary">
                {edge.kind}
              </span>
              {edge.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function defaultFamilyEdges(input: {
  setor?: string;
  uf?: string;
  cnpj?: string;
  orgaoSlug?: string;
  municipioSlug?: string;
}): EntityEdge[] {
  const edges: EntityEdge[] = [
    { href: "/licitacoes", label: "Licitações", kind: "tender" },
    { href: "/contratos", label: "Contratos", kind: "contract" },
    { href: "/cnpj", label: "Empresas", kind: "company" },
    { href: "/orgaos", label: "Órgãos", kind: "organ" },
    { href: "/municipios", label: "Municípios", kind: "municipality" },
    { href: "/observatorio", label: "Observatório", kind: "observatory" },
  ];
  if (input.setor) {
    edges.unshift({
      href: `/licitacoes/${input.setor}`,
      label: `Setor ${input.setor}`,
      kind: "sector",
    });
  }
  if (input.cnpj) {
    edges.unshift({
      href: `/cnpj/${input.cnpj}`,
      label: `CNPJ ${input.cnpj}`,
      kind: "company",
    });
  }
  if (input.orgaoSlug) {
    edges.unshift({
      href: `/orgaos/${input.orgaoSlug}`,
      label: "Este órgão",
      kind: "organ",
    });
  }
  if (input.municipioSlug) {
    edges.unshift({
      href: `/municipios/${input.municipioSlug}`,
      label: "Este município",
      kind: "municipality",
    });
  }
  return edges;
}
