/**
 * DEBT-012 FE-028: Zod form validation schema tests.
 */
import {
  signupSchema,
  onboardingStep1Schema,
  onboardingStep2Schema,
  profileSchema,
  getPasswordStrength,
} from "../../lib/schemas/forms";

describe("signupSchema", () => {
  const validData = {
    fullName: "João da Silva",
    email: "joao@email.com",
    phone: "",
    password: "Senha1234",
    confirmPassword: "Senha1234",
  };

  it("accepts valid signup data", () => {
    const result = signupSchema.safeParse(validData);
    expect(result.success).toBe(true);
  });

  it("rejects empty fullName", () => {
    const result = signupSchema.safeParse({ ...validData, fullName: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("Nome é obrigatório");
    }
  });

  it("rejects short fullName", () => {
    const result = signupSchema.safeParse({ ...validData, fullName: "J" });
    expect(result.success).toBe(false);
  });

  it("rejects invalid email format", () => {
    const result = signupSchema.safeParse({ ...validData, email: "not-email" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("Email inválido");
    }
  });

  it("rejects empty email", () => {
    const result = signupSchema.safeParse({ ...validData, email: "" });
    expect(result.success).toBe(false);
  });

  it("rejects password shorter than 8 chars", () => {
    const result = signupSchema.safeParse({
      ...validData,
      password: "Ab1",
      confirmPassword: "Ab1",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("Mínimo 8 caracteres");
    }
  });

  it("rejects password without uppercase", () => {
    const result = signupSchema.safeParse({
      ...validData,
      password: "senha1234",
      confirmPassword: "senha1234",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("Pelo menos 1 letra maiúscula");
    }
  });

  it("rejects password without digit", () => {
    const result = signupSchema.safeParse({
      ...validData,
      password: "SenhaForte",
      confirmPassword: "SenhaForte",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("Pelo menos 1 número");
    }
  });

  it("rejects mismatched passwords", () => {
    const result = signupSchema.safeParse({
      ...validData,
      confirmPassword: "Different1",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const mismatchError = result.error.issues.find(
        (i) => i.path.includes("confirmPassword") && i.message === "Senhas não coincidem"
      );
      expect(mismatchError).toBeDefined();
    }
  });

  it("allows optional phone", () => {
    const result = signupSchema.safeParse({ ...validData, phone: undefined });
    expect(result.success).toBe(true);
  });
});

describe("onboardingStep1Schema", () => {
  it("accepts valid step 1 data", () => {
    const result = onboardingStep1Schema.safeParse({
      cnae: "4781-4/00 — Comércio",
      objetivo_principal: "Encontrar uniformes",
    });
    expect(result.success).toBe(true);
  });

  it("rejects empty cnae", () => {
    const result = onboardingStep1Schema.safeParse({
      cnae: "",
      objetivo_principal: "Algo",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty objetivo", () => {
    const result = onboardingStep1Schema.safeParse({
      cnae: "4781",
      objetivo_principal: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects objetivo longer than 200 chars", () => {
    const result = onboardingStep1Schema.safeParse({
      cnae: "4781",
      objetivo_principal: "a".repeat(201),
    });
    expect(result.success).toBe(false);
  });
});

describe("onboardingStep2Schema", () => {
  it("accepts valid step 2 data", () => {
    const result = onboardingStep2Schema.safeParse({
      ufs_atuacao: ["SP", "RJ"],
      faixa_valor_min: 100000,
      faixa_valor_max: 500000,
    });
    expect(result.success).toBe(true);
  });

  it("rejects empty UFs", () => {
    const result = onboardingStep2Schema.safeParse({
      ufs_atuacao: [],
      faixa_valor_min: 0,
      faixa_valor_max: 0,
    });
    expect(result.success).toBe(false);
  });

  it("rejects max < min when both > 0", () => {
    const result = onboardingStep2Schema.safeParse({
      ufs_atuacao: ["SP"],
      faixa_valor_min: 500000,
      faixa_valor_max: 100000,
    });
    expect(result.success).toBe(false);
  });

  it("allows both zero (no limits)", () => {
    const result = onboardingStep2Schema.safeParse({
      ufs_atuacao: ["SP"],
      faixa_valor_min: 0,
      faixa_valor_max: 0,
    });
    expect(result.success).toBe(true);
  });
});

describe("profileSchema", () => {
  const validProfile = {
    ufs_atuacao: ["SP"],
    porte_empresa: "EPP",
    experiencia_licitacoes: "INICIANTE",
    faixa_valor_min: "50000",
    faixa_valor_max: "500000",
    capacidade_funcionarios: "10",
    faturamento_anual: "1000000",
    atestados: [],
  };

  it("accepts valid profile data", () => {
    const result = profileSchema.safeParse(validProfile);
    expect(result.success).toBe(true);
  });

  it("rejects max < min when both provided", () => {
    const result = profileSchema.safeParse({
      ...validProfile,
      faixa_valor_min: "500000",
      faixa_valor_max: "100000",
    });
    expect(result.success).toBe(false);
  });

  it("allows empty strings for value range", () => {
    const result = profileSchema.safeParse({
      ...validProfile,
      faixa_valor_min: "",
      faixa_valor_max: "",
    });
    expect(result.success).toBe(true);
  });
});

describe("getPasswordStrength", () => {
  it("returns fraca for empty password", () => {
    expect(getPasswordStrength("").level).toBe("fraca");
    expect(getPasswordStrength("").score).toBe(0);
  });

  it("returns fraca for short password", () => {
    expect(getPasswordStrength("abc").level).toBe("fraca");
  });

  it("returns média for moderate password", () => {
    expect(getPasswordStrength("Abc12345").level).toBe("média");
  });

  it("returns forte for complex password", () => {
    expect(getPasswordStrength("Str0ng!Pass@2026").level).toBe("forte");
  });
});
