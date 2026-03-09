import { z } from "zod";

// ============================================================================
// Signup Form Schema
// ============================================================================

export const signupSchema = z
  .object({
    fullName: z
      .string()
      .min(1, "Nome é obrigatório")
      .min(2, "Nome deve ter pelo menos 2 caracteres"),
    email: z
      .string()
      .min(1, "Email é obrigatório")
      .email("Email inválido"),
    phone: z.string().optional(),
    password: z
      .string()
      .min(8, "Mínimo 8 caracteres")
      .regex(/[A-Z]/, "Pelo menos 1 letra maiúscula")
      .regex(/\d/, "Pelo menos 1 número"),
    confirmPassword: z.string().min(1, "Confirme sua senha"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Senhas não coincidem",
    path: ["confirmPassword"],
  });

export type SignupFormData = z.infer<typeof signupSchema>;

// ============================================================================
// Onboarding Form Schema (multi-step)
// ============================================================================

export const onboardingStep1Schema = z.object({
  cnae: z.string().min(1, "Segmento / CNAE é obrigatório"),
  objetivo_principal: z
    .string()
    .min(1, "Objetivo principal é obrigatório")
    .max(200, "Máximo 200 caracteres"),
});

export const onboardingStep2Schema = z
  .object({
    ufs_atuacao: z.array(z.string()).min(1, "Selecione pelo menos 1 estado"),
    faixa_valor_min: z.number().min(0),
    faixa_valor_max: z.number().min(0),
  })
  .refine(
    (data) =>
      !(data.faixa_valor_min > 0 && data.faixa_valor_max > 0 && data.faixa_valor_max < data.faixa_valor_min),
    {
      message: "Valor máximo deve ser maior que o mínimo",
      path: ["faixa_valor_max"],
    }
  );

export type OnboardingStep1Data = z.infer<typeof onboardingStep1Schema>;
export type OnboardingStep2Data = z.infer<typeof onboardingStep2Schema>;

// ============================================================================
// Profile (Conta/Perfil) Form Schema
// ============================================================================

export const profileSchema = z
  .object({
    ufs_atuacao: z.array(z.string()),
    porte_empresa: z.string(),
    experiencia_licitacoes: z.string(),
    faixa_valor_min: z.string(),
    faixa_valor_max: z.string(),
    capacidade_funcionarios: z.string(),
    faturamento_anual: z.string(),
    atestados: z.array(z.string()),
  })
  .refine(
    (data) => {
      const min = data.faixa_valor_min ? Number(data.faixa_valor_min) : 0;
      const max = data.faixa_valor_max ? Number(data.faixa_valor_max) : 0;
      if (min > 0 && max > 0) return max >= min;
      return true;
    },
    {
      message: "Valor máximo deve ser maior que o mínimo",
      path: ["faixa_valor_max"],
    }
  );

export type ProfileFormData = z.infer<typeof profileSchema>;

// ============================================================================
// Password Strength Helper
// ============================================================================

export function getPasswordStrength(pw: string): {
  level: "fraca" | "média" | "forte";
  score: number;
} {
  if (!pw) return { level: "fraca", score: 0 };
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  if (score <= 2) return { level: "fraca", score: 1 };
  if (score <= 4) return { level: "média", score: 2 };
  return { level: "forte", score: 3 };
}
