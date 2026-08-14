/**
 * Server-only extra-cli public_read_v1 probe via the SmartLic adapter.
 * The browser never receives the extra-cli database credential.
 */

export type PublicFamilyName =
  | "current_snapshot"
  | "tenders"
  | "contracts"
  | "entities"
  | "suppliers"
  | "organs"
  | "municipalities";

export interface PublicFamilyPageModel {
  family: string;
  served_from: string;
  mode: string;
  canonical_id: string | null;
  display_name: string | null;
  as_of: string | null;
  completeness: string | null;
  freshness: string | null;
  reason_codes: string[];
  divergence: string[];
  blocked: boolean;
  stale: boolean;
  empty: boolean;
  row_count: number | null;
}

const FAMILY_BY_ROUTE: Record<string, PublicFamilyName> = {
  tender: "tenders",
  contract: "contracts",
  company: "suppliers",
  organ: "organs",
  municipality: "municipalities",
  observatory: "current_snapshot",
  tool: "current_snapshot",
  home: "current_snapshot",
};

export function adapterFamilyFor(routeFamily: string): PublicFamilyName {
  return FAMILY_BY_ROUTE[routeFamily] || "current_snapshot";
}

export function publicReadPath(family: PublicFamilyName, publicId: string): string {
  return `/v1/public-read/${family}/${encodeURIComponent(publicId)}`;
}

interface FamilyReadPayload {
  family?: string;
  served_from?: string;
  mode?: string;
  entity?: {
    canonical_id?: string | null;
    display_name?: string | null;
    as_of?: string | null;
    completeness?: string | null;
    freshness?: string | null;
    reason_codes?: string[];
  } | null;
  divergence?: string[];
  row_count?: number | null;
}

export function familyReadToPageModel(body: FamilyReadPayload): PublicFamilyPageModel {
  const entity = body.entity || null;
  const freshness = entity?.freshness || null;
  const divergence = body.divergence || [];
  return {
    family: body.family || "",
    served_from: body.served_from || "blocked",
    mode: body.mode || "off",
    canonical_id: entity?.canonical_id ?? null,
    display_name: entity?.display_name ?? null,
    as_of: entity?.as_of ?? null,
    completeness: entity?.completeness ?? null,
    freshness,
    reason_codes: entity?.reason_codes || [],
    divergence,
    blocked: body.served_from === "blocked" || freshness === "BLOCKED" || divergence.includes("public_unavailable"),
    stale: freshness === "STALE",
    empty: !entity || body.row_count === 0,
    row_count: body.row_count ?? null,
  };
}

export async function loadPublicFamily(
  family: PublicFamilyName,
  publicId: string,
): Promise<PublicFamilyPageModel | null> {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return null;
  }
  const url = `${backendUrl}${publicReadPath(family, publicId)}`;
  const res = await fetch(url, {
    next: { revalidate: 3600 },
    signal: AbortSignal.timeout(4000),
    cache: "no-store",
  });
  if (res.status >= 500) {
    throw new Error(`public_read_backend_5xx:${res.status}`);
  }
  if (!res.ok) {
    return null;
  }
  return familyReadToPageModel((await res.json()) as FamilyReadPayload);
}
