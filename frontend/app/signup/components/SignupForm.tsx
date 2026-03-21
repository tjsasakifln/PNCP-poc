"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { UseFormReturn } from "react-hook-form";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/Input";
import { Label } from "../../../components/ui/Label";
import { getPasswordStrength, type SignupFormData } from "../../../lib/schemas/forms";
import Link from "next/link";

// STORY-258: Email type result
type EmailCheckResult = {
  is_disposable: boolean;
  is_corporate: boolean;
} | null;

// STORY-258: Phone check result
type PhoneCheckResult = {
  already_registered: boolean;
} | null;

interface SignupFormProps {
  form: UseFormReturn<SignupFormData>;
  loading: boolean;
  error: string | null;
  onSubmit: (data: SignupFormData) => void;
  isFormValid: boolean;
}

export function SignupForm({ form, loading, error, onSubmit, isFormValid }: SignupFormProps) {
  const {
    register,
    handleSubmit: rhfHandleSubmit,
    watch,
    formState: { errors, isDirty },
  } = form;

  const password = watch("password");
  const confirmPassword = watch("confirmPassword");
  const email = watch("email");
  const phone = watch("phone") || "";

  const [showPassword, setShowPassword] = useState(false);

  // STORY-258: Email validation state
  const [emailCheckLoading, setEmailCheckLoading] = useState(false);
  const [emailCheckResult, setEmailCheckResult] = useState<EmailCheckResult>(null);
  const [emailCheckError, setEmailCheckError] = useState<string | null>(null);

  // STORY-258: Phone validation state
  const [phoneCheckLoading, setPhoneCheckLoading] = useState(false);
  const [phoneCheckResult, setPhoneCheckResult] = useState<PhoneCheckResult>(null);
  const [phoneCheckError, setPhoneCheckError] = useState<string | null>(null);
  const phoneDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Password strength
  const passwordStrength = getPasswordStrength(password);
  const passwordMeetsPolicy =
    password.length >= 8 && /[A-Z]/.test(password) && /\d/.test(password);
  const confirmPasswordMatch = confirmPassword !== "" && confirmPassword === password;

  // STORY-258: Email check on blur
  const handleEmailBlur = useCallback(async () => {
    const trimmed = email.trim();
    const basicValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed);
    if (!basicValid || !trimmed) return;

    setEmailCheckLoading(true);
    setEmailCheckError(null);
    setEmailCheckResult(null);
    try {
      const res = await fetch(
        `/api/auth/check-email?email=${encodeURIComponent(trimmed)}`
      );
      if (res.ok) {
        const data = await res.json();
        setEmailCheckResult(data);
        if (data.is_disposable) {
          setEmailCheckError(
            "Emails descartáveis não são aceitos. Use um email corporativo ou permanente."
          );
        }
      }
    } catch {
      // silent — do not block signup on check failure
    } finally {
      setEmailCheckLoading(false);
    }
  }, [email]);

  // STORY-258: Phone check with 300ms debounce on blur
  const handlePhoneBlur = useCallback(() => {
    const trimmed = phone.trim();
    if (!trimmed) return;

    if (phoneDebounceRef.current) clearTimeout(phoneDebounceRef.current);
    phoneDebounceRef.current = setTimeout(async () => {
      setPhoneCheckLoading(true);
      setPhoneCheckError(null);
      setPhoneCheckResult(null);
      try {
        const res = await fetch(
          `/api/auth/check-phone?phone=${encodeURIComponent(trimmed)}`
        );
        if (res.ok) {
          const data = await res.json();
          setPhoneCheckResult(data);
          if (data.already_registered) {
            setPhoneCheckError(
              "Este telefone já está associado a uma conta. Tente fazer login."
            );
          }
        }
      } catch {
        // silent
      } finally {
        setPhoneCheckLoading(false);
      }
    }, 300);
  }, [phone]);

  // Propagate check errors to parent isFormValid via effect
  useEffect(() => {
    // Parent checks emailCheckError/phoneCheckError via isFormValid prop
    // These are internal checks only used for UI feedback here
  }, [emailCheckError, phoneCheckError]);

  return (
    <>
      {error && (
        <div className="mb-4 p-3 bg-error-subtle text-error rounded-input text-sm">
          {error}
        </div>
      )}

      <form onSubmit={rhfHandleSubmit(onSubmit)} className="space-y-4">
        {/* Full Name — SAB-007 AC1 */}
        <div>
          <Label htmlFor="fullName" required>
            Nome completo
          </Label>
          <Input
            id="fullName"
            type="text"
            inputSize="lg"
            placeholder="Seu nome"
            required
            error={errors.fullName?.message}
            errorTestId="name-error"
            {...register("fullName")}
          />
        </div>

        {/* Email */}
        <div>
          <Label htmlFor="email" required>
            Email
          </Label>
          <div className="relative">
            <Input
              id="email"
              type="email"
              inputSize="lg"
              placeholder="seu@email.com"
              required
              state={errors.email || emailCheckError ? "error" : undefined}
              {...register("email", {
                onChange: () => {
                  setEmailCheckResult(null);
                  setEmailCheckError(null);
                },
                onBlur: handleEmailBlur,
              })}
            />
            {/* STORY-258: Loading spinner */}
            {emailCheckLoading && (
              <div className="absolute right-3 top-3">
                <svg className="animate-spin h-4 w-4 text-ink-muted" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
            )}
          </div>
          {/* SAB-007 AC2: Format error */}
          {errors.email && !emailCheckError && (
            <p className="mt-1 text-xs text-error" data-testid="email-error">
              {errors.email.message}
            </p>
          )}
          {/* STORY-258: Disposable email error */}
          {emailCheckError && (
            <p className="mt-1 text-xs text-error" data-testid="email-disposable-error">
              {emailCheckError}
            </p>
          )}
          {/* STORY-258: Email type badge */}
          {emailCheckResult && !emailCheckError && (
            <span
              className={`inline-flex items-center gap-1 mt-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                emailCheckResult.is_corporate
                  ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                  : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
              }`}
              data-testid="email-type-badge"
            >
              <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                {emailCheckResult.is_corporate ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                )}
              </svg>
              {emailCheckResult.is_corporate ? "Email corporativo" : "Email pessoal"}
            </span>
          )}
        </div>

        {/* Phone (STORY-258) */}
        <div>
          <Label htmlFor="phone">
            Telefone <span className="text-ink-muted font-normal">(opcional)</span>
          </Label>
          <Input
            id="phone"
            type="tel"
            inputSize="lg"
            placeholder="+55 11 91234-5678"
            error={phoneCheckError || undefined}
            errorTestId="phone-error"
            {...register("phone", {
              onChange: () => {
                setPhoneCheckResult(null);
                setPhoneCheckError(null);
              },
              onBlur: handlePhoneBlur,
            })}
          />
          {phoneCheckLoading && (
            <p className="mt-1 text-xs text-ink-muted">Verificando...</p>
          )}
          {phoneCheckResult && !phoneCheckError && (
            <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-400" data-testid="phone-ok">
              Telefone disponível
            </p>
          )}
        </div>

        {/* Password — SAB-007 AC3 */}
        <div>
          <Label htmlFor="password" required>
            Senha
          </Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              inputSize="lg"
              className="pr-12"
              placeholder="Min. 8 caracteres, 1 maiúscula, 1 número"
              required
              minLength={8}
              error={errors.password?.message}
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-3 p-1 text-ink-muted
                         hover:text-ink transition-colors"
              aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
            >
              {showPassword ? (
                <svg role="img" aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              ) : (
                <svg role="img" aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}
            </button>
          </div>
          {/* SAB-007 AC3: Password strength bar */}
          {password && (
            <div className="mt-2" data-testid="password-strength">
              <div className="flex gap-1 mb-1">
                <div className={`h-1.5 flex-1 rounded-full transition-colors ${
                  passwordStrength.score >= 1 ? (
                    passwordStrength.level === "fraca" ? "bg-red-500" :
                    passwordStrength.level === "média" ? "bg-yellow-500" : "bg-green-500"
                  ) : "bg-gray-200 dark:bg-gray-700"
                }`} />
                <div className={`h-1.5 flex-1 rounded-full transition-colors ${
                  passwordStrength.score >= 2 ? (
                    passwordStrength.level === "média" ? "bg-yellow-500" : "bg-green-500"
                  ) : "bg-gray-200 dark:bg-gray-700"
                }`} />
                <div className={`h-1.5 flex-1 rounded-full transition-colors ${
                  passwordStrength.score >= 3 ? "bg-green-500" : "bg-gray-200 dark:bg-gray-700"
                }`} />
              </div>
              <p className={`text-xs ${
                passwordStrength.level === "fraca" ? "text-red-500" :
                passwordStrength.level === "média" ? "text-yellow-600 dark:text-yellow-400" :
                "text-green-600"
              }`} data-testid="password-strength-label">
                Senha {passwordStrength.level}
              </p>
            </div>
          )}
          {/* Password policy requirements */}
          {password && !passwordMeetsPolicy && (
            <ul className="mt-1 text-xs space-y-0.5">
              <li className={password.length >= 8 ? "text-green-600" : "text-error"}>
                {password.length >= 8 ? "\u2713" : "\u2717"} Mínimo 8 caracteres
              </li>
              <li className={/[A-Z]/.test(password) ? "text-green-600" : "text-error"}>
                {/[A-Z]/.test(password) ? "\u2713" : "\u2717"} Pelo menos 1 letra maiúscula
              </li>
              <li className={/\d/.test(password) ? "text-green-600" : "text-error"}>
                {/\d/.test(password) ? "\u2713" : "\u2717"} Pelo menos 1 número
              </li>
            </ul>
          )}
        </div>

        {/* Confirm Password — SAB-007 AC4 */}
        <div>
          <Label htmlFor="confirmPassword" required>
            Confirmar senha
          </Label>
          <Input
            id="confirmPassword"
            type="password"
            inputSize="lg"
            placeholder="Repita sua senha"
            required
            state={confirmPasswordMatch ? "success" : undefined}
            error={errors.confirmPassword?.message}
            errorTestId="confirm-password-error"
            {...register("confirmPassword")}
          />
          {confirmPasswordMatch && !errors.confirmPassword && (
            <p className="mt-1 text-xs text-green-600" data-testid="confirm-password-match">
              &#10003; Senhas coincidem
            </p>
          )}
        </div>

        {/* SAB-007 AC5/AC6/AC7: Submit button with tooltip, transition, spinner */}
        <div className="relative group">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            className={`w-full transition-all duration-300 ease-in-out font-semibold
                       ${isFormValid
                         ? "shadow-md hover:shadow-lg"
                         : "!bg-gray-300 dark:!bg-gray-700 !text-gray-500 dark:!text-gray-400 cursor-not-allowed"
                       }`}
            disabled={loading || !isFormValid}
            loading={loading}
          >
            {loading ? "Criando conta..." : "Criar conta"}
          </Button>
          {/* AC5: Tooltip when disabled */}
          {!isFormValid && !loading && (
            <div
              className="absolute -top-10 left-1/2 -translate-x-1/2 px-3 py-1.5
                         bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900
                         text-xs rounded-md whitespace-nowrap
                         opacity-0 group-hover:opacity-100 transition-opacity
                         pointer-events-none z-10"
              role="tooltip"
              data-testid="submit-tooltip"
            >
              Preencha todos os campos
              <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-100" />
            </div>
          )}
        </div>
        {!isFormValid && isDirty && !loading && (
          <p className="mt-2 text-xs text-center text-ink-muted" data-testid="form-hint">
            Preencha todos os campos corretamente para continuar.
          </p>
        )}
      </form>

      <p className="mt-6 text-center text-sm text-ink-secondary">
        Já tem conta?{" "}
        <Link href="/login" className="text-brand-blue hover:underline">
          Fazer login
        </Link>
      </p>
    </>
  );
}
