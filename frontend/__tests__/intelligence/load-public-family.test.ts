import {
  adapterFamilyFor,
  familyReadToPageModel,
  publicReadPath,
} from "@/lib/intelligence/loadPublicFamily";

describe("loadPublicFamily wiring", () => {
  it("points the tender family at the adapter tenders path", () => {
    expect(adapterFamilyFor("tender")).toBe("tenders");
    expect(publicReadPath("tenders", "pncp:1")).toBe("/v1/public-read/tenders/pncp%3A1");
  });

  it("maps a FamilyRead payload without inventing COMPLETE", () => {
    const page = familyReadToPageModel({
      family: "tenders",
      served_from: "legacy",
      mode: "shadow",
      entity: {
        canonical_id: "proc-1",
        display_name: "Edital",
        as_of: "2026-08-13T12:00:00+00:00",
        completeness: "INCOMPLETE",
        freshness: "STALE",
        reason_codes: ["stale_or_unknown_freshness"],
      },
      divergence: ["freshness_delta"],
      row_count: 1,
    });
    expect(page.completeness).toBe("INCOMPLETE");
    expect(page.stale).toBe(true);
    expect(page.blocked).toBe(false);
    expect(page.divergence).toContain("freshness_delta");
  });

  it("classifies producer failure instead of empty agreement", () => {
    const page = familyReadToPageModel({
      family: "tenders",
      served_from: "legacy",
      mode: "shadow",
      entity: null,
      divergence: ["dsn_missing", "public_unavailable"],
      row_count: 0,
    });
    expect(page.empty).toBe(true);
    expect(page.blocked).toBe(true);
    expect(page.divergence).toContain("public_unavailable");
  });
});
