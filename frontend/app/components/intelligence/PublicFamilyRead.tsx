import { PublicFamilyShell } from "@/app/components/intelligence/PublicFamilyShell";
import type { JourneyContext } from "@/lib/conversion/journey";
import {
  adapterFamilyFor,
  loadPublicFamily,
  surfaceStateFromRead,
  type PublicFamilyPageModel,
} from "@/lib/intelligence/loadPublicFamily";

export async function PublicFamilyRead({
  family,
  publicId,
  setor,
  uf,
}: {
  family: JourneyContext["family"];
  publicId?: string;
  setor?: string;
  uf?: string;
}) {
  const hubProbe = !publicId;
  const adapterFamily = hubProbe ? "current_snapshot" : adapterFamilyFor(family);
  const id = publicId || "latest";
  let read: PublicFamilyPageModel | null = null;
  try {
    read = await loadPublicFamily(adapterFamily, id);
  } catch {
    // Entity pages surface the failure. Hub watermark probes must not
    // paint blocked/empty over a listing that already has coverage.
    read = hubProbe
      ? null
      : {
          family: adapterFamily,
          served_from: "blocked",
          mode: "shadow",
          canonical_id: null,
          display_name: null,
          as_of: null,
          completeness: null,
          freshness: null,
          reason_codes: [],
          divergence: ["public_unavailable"],
          blocked: true,
          stale: false,
          empty: true,
          row_count: 0,
        };
  }
  return (
    <PublicFamilyShell
      family={family}
      entityPublicId={publicId}
      setor={setor}
      uf={uf}
      state={surfaceStateFromRead(read, { hubProbe })}
      asOf={read?.as_of ?? null}
      reasonCodes={[...(read?.reason_codes || []), ...(read?.divergence || [])]}
    />
  );
}
