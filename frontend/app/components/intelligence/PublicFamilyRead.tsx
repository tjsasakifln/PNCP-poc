import { PublicFamilyShell } from "@/app/components/intelligence/PublicFamilyShell";
import type { JourneyContext } from "@/lib/conversion/journey";
import {
  adapterFamilyFor,
  loadPublicFamily,
} from "@/lib/intelligence/loadPublicFamily";
import type { SurfaceState } from "@/lib/intelligence/types";

function surfaceFromRead(read: {
  blocked: boolean;
  stale: boolean;
  empty: boolean;
  divergence: string[];
} | null): SurfaceState {
  if (!read) return "unknown";
  if (read.blocked || read.divergence.includes("public_unavailable")) return "blocked";
  if (read.stale) return "stale";
  if (read.empty) return "empty";
  return "ok";
}

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
  const adapterFamily = publicId ? adapterFamilyFor(family) : "current_snapshot";
  const id = publicId || "latest";
  let read = null;
  try {
    read = await loadPublicFamily(adapterFamily, id);
  } catch {
    read = {
      blocked: true,
      stale: false,
      empty: true,
      divergence: ["public_unavailable"],
      as_of: null,
      reason_codes: [],
    };
  }
  return (
    <PublicFamilyShell
      family={family}
      entityPublicId={publicId}
      setor={setor}
      uf={uf}
      state={surfaceFromRead(read)}
      asOf={read?.as_of ?? null}
      reasonCodes={[...(read?.reason_codes || []), ...(read?.divergence || [])]}
    />
  );
}
