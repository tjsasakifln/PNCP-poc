import { BRAND, DEFAULT_TITLE } from "@/lib/brand/system";
import {
  SAAS_CTA_DENYLIST,
  familyFromPath,
  resolveJourney,
} from "@/lib/conversion/journey";
import { classifySurface } from "@/lib/intelligence/types";

describe("brand system", () => {
  it("describes SmartLic as CONFENGE public intelligence, not SaaS", () => {
    expect(BRAND.descriptor).toMatch(/CONFENGE/i);
    expect(BRAND.relationship).toMatch(/Não é um SaaS de assinatura/i);
    expect(DEFAULT_TITLE).toMatch(/CONFENGE/);
  });
});

describe("journey", () => {
  it("maps public paths to families", () => {
    expect(familyFromPath("/licitacoes/saude")).toBe("tender");
    expect(familyFromPath("/contratos/engenharia/sc")).toBe("contract");
    expect(familyFromPath("/cnpj/00")).toBe("company");
    expect(familyFromPath("/orgaos/pref")).toBe("organ");
    expect(familyFromPath("/municipios/joinville-sc")).toBe("municipality");
    expect(familyFromPath("/observatorio/raio-x-marco-2026")).toBe("observatory");
  });

  it("builds contextual CTA without SaaS destinations", () => {
    const cta = resolveJourney({
      family: "tender",
      entityPublicId: "proc-1",
      setor: "saude",
    });
    expect(cta.href).toContain("/consultoria-b2g");
    expect(cta.href).toContain("cta=cta.tender.go_nogo");
    expect(cta.href).not.toMatch(/signup|planos|pricing/);
    expect(SAAS_CTA_DENYLIST).toContain("/signup");
  });
});

describe("surface classification", () => {
  it("keeps empty, stale, blocked and error distinct", () => {
    expect(classifySurface({ hasEntity: false })).toBe("empty");
    expect(classifySurface({ hasEntity: true, rowCount: 0 })).toBe("empty");
    expect(classifySurface({ hasEntity: true, rowCount: 3, freshness: "stale" })).toBe("stale");
    expect(classifySurface({ hasEntity: true, blocked: true })).toBe("blocked");
    expect(classifySurface({ hasEntity: true, error: true })).toBe("error");
    expect(classifySurface({ hasEntity: true, rowCount: 2, freshness: "fresh" })).toBe("ok");
  });
});
