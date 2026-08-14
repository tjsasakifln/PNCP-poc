import { FamilyCta } from "@/app/components/conversion/FamilyCta";
import { DataStateBanner } from "@/app/components/intelligence/DataStateBanner";
import {
  defaultFamilyEdges,
  EntityGraphNav,
} from "@/app/components/intelligence/EntityGraphNav";
import { ProvenanceBar } from "@/app/components/intelligence/ProvenanceBar";
import type { JourneyContext } from "@/lib/conversion/journey";
import { defaultLimitations, type SurfaceState } from "@/lib/intelligence/types";

export function PublicFamilyShell({
  family,
  state = "ok",
  source = "legado SmartLic (transição) + extra-cli public_read_v1 quando habilitado",
  asOf = null,
  reasonCodes = [],
  entityPublicId,
  setor,
  uf,
}: {
  family: JourneyContext["family"];
  state?: SurfaceState;
  source?: string;
  asOf?: string | null;
  reasonCodes?: string[];
  entityPublicId?: string;
  setor?: string;
  uf?: string;
}) {
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <ProvenanceBar
        state={state}
        provenance={{
          source,
          asOf,
          freshness: state === "stale" ? "stale" : state === "ok" ? "fresh" : "unknown",
          completeness: state === "empty" ? "incomplete" : "unknown",
          reasonCodes,
          limitations: defaultLimitations(family),
          contractVersion: "public_read_v1",
        }}
      />
      <DataStateBanner state={state} />
      <EntityGraphNav edges={defaultFamilyEdges({ setor, uf })} />
      <FamilyCta
        context={{
          family,
          entityPublicId,
          setor,
          uf,
          dataState: state,
        }}
      />
    </div>
  );
}
