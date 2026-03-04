/**
 * UX-409 — Perfil mostra 0% de completude quando faixa_valor_min=0
 *
 * Tests that `completenessCount()` correctly treats falsy-but-valid values
 * (like `0`) as filled fields, while still treating `null`/`undefined` as empty.
 */

import { completenessCount, TOTAL_PROFILE_FIELDS, ProfileContext } from "../app/conta/profile-utils";

describe("UX-409: completenessCount treats 0 as valid", () => {
  const FULL_CONTEXT: ProfileContext = {
    ufs_atuacao: ["SP"],
    porte_empresa: "me",
    experiencia_licitacoes: "intermediario",
    faixa_valor_min: 50000,
    capacidade_funcionarios: 20,
    faturamento_anual: 1000000,
    atestados: ["crea"],
  };

  // AC2: faixa_valor_min=0 should count as filled
  it("counts faixa_valor_min=0 as a filled field", () => {
    const ctx: ProfileContext = { ...FULL_CONTEXT, faixa_valor_min: 0 };
    expect(completenessCount(ctx)).toBe(TOTAL_PROFILE_FIELDS);
  });

  // AC3: faixa_valor_min=null should NOT count as filled
  it("does NOT count faixa_valor_min=null as filled", () => {
    const ctx: ProfileContext = { ...FULL_CONTEXT, faixa_valor_min: null };
    expect(completenessCount(ctx)).toBe(TOTAL_PROFILE_FIELDS - 1);
  });

  // AC4: capacidade_funcionarios=0 should count as filled
  it("counts capacidade_funcionarios=0 as a filled field", () => {
    const ctx: ProfileContext = { ...FULL_CONTEXT, capacidade_funcionarios: 0 };
    expect(completenessCount(ctx)).toBe(TOTAL_PROFILE_FIELDS);
  });

  // AC4 complement: faturamento_anual=0 should also count as filled
  it("counts faturamento_anual=0 as a filled field", () => {
    const ctx: ProfileContext = { ...FULL_CONTEXT, faturamento_anual: 0 };
    expect(completenessCount(ctx)).toBe(TOTAL_PROFILE_FIELDS);
  });

  // AC5: All fields filled (including zeros) returns TOTAL_PROFILE_FIELDS
  it("returns TOTAL_PROFILE_FIELDS when all fields filled with zeros", () => {
    const ctx: ProfileContext = {
      ufs_atuacao: ["RJ"],
      porte_empresa: "mei",
      experiencia_licitacoes: "iniciante",
      faixa_valor_min: 0,
      capacidade_funcionarios: 0,
      faturamento_anual: 0,
      atestados: ["iso_9001"],
    };
    expect(completenessCount(ctx)).toBe(TOTAL_PROFILE_FIELDS);
  });

  // Regression: empty context returns 0
  it("returns 0 for completely empty context", () => {
    const ctx: ProfileContext = {};
    expect(completenessCount(ctx)).toBe(0);
  });

  // Regression: null numerics + empty arrays/strings = 0
  it("returns 0 when all fields are null/empty", () => {
    const ctx: ProfileContext = {
      ufs_atuacao: [],
      porte_empresa: "",
      experiencia_licitacoes: "",
      faixa_valor_min: null,
      capacidade_funcionarios: null,
      faturamento_anual: null,
      atestados: [],
    };
    expect(completenessCount(ctx)).toBe(0);
  });

  // Partial fill
  it("correctly counts partial fill (3/7)", () => {
    const ctx: ProfileContext = {
      ufs_atuacao: ["SP", "MG"],
      porte_empresa: "epp",
      experiencia_licitacoes: "avancado",
      faixa_valor_min: null,
      capacidade_funcionarios: null,
      faturamento_anual: null,
      atestados: [],
    };
    expect(completenessCount(ctx)).toBe(3);
  });

  // TOTAL_PROFILE_FIELDS constant check
  it("TOTAL_PROFILE_FIELDS equals 7", () => {
    expect(TOTAL_PROFILE_FIELDS).toBe(7);
  });
});
