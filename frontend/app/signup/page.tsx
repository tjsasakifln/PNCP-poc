"use client";

import { useState, useRef, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";
import InstitutionalSidebar from "../components/InstitutionalSidebar";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic";

// Available sectors
const SECTORS = [
  { id: "vestuario", name: "Vestuário e Uniformes" },
  { id: "alimentos", name: "Alimentos e Merenda" },
  { id: "informatica", name: "Informática e Tecnologia" },
  { id: "mobiliario", name: "Mobiliário" },
  { id: "papelaria", name: "Papelaria e Material de Escritório" },
  { id: "engenharia", name: "Engenharia e Construção" },
  { id: "software", name: "Software e Sistemas" },
  { id: "facilities", name: "Facilities (Limpeza e Zeladoria)" },
  { id: "saude", name: "Saúde" },
  { id: "vigilancia", name: "Vigilância e Segurança" },
  { id: "transporte", name: "Transporte e Veículos" },
  { id: "manutencao_predial", name: "Manutenção Predial" },
  { id: "outro", name: "Outro" },
];

// Phone mask helper for Brazilian format
function formatPhoneBR(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 2) return digits;
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  }
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}

// Extract only digits from formatted phone
function extractDigits(phone: string): string {
  return phone.replace(/\D/g, "");
}

// Validate phone has 10-11 digits
function isValidPhone(phone: string): boolean {
  const digits = extractDigits(phone);
  return digits.length >= 10 && digits.length <= 11;
}

// Consent terms text
const CONSENT_TERMS = `TERMOS DE CONSENTIMENTO PARA COMUNICACOES PROMOCIONAIS

Ao fornecer seus dados e marcar a caixa de aceite abaixo, voce autoriza expressamente a equipe do ${APP_NAME} a enviar comunicacoes promocionais por EMAIL e pela PLATAFORMA, incluindo:

1. Mensagens promocionais sobre novos recursos e funcionalidades;
2. Ofertas especiais, descontos e pacotes promocionais;
3. Dicas e conteudos relevantes sobre licitacoes publicas;
4. Lembretes sobre oportunidades de licitacao compativeis com seu perfil.

FREQUENCIA: As mensagens serao enviadas com moderacao, respeitando horarios comerciais (segunda a sexta, 9h as 18h).

CANCELAMENTO: Voce pode cancelar o recebimento a qualquer momento:
- Clicando em "Descadastrar" nos emails recebidos
- Acessando as configuracoes do seu perfil
- Entrando em contato pela secao de suporte na plataforma

PRIVACIDADE: Seus dados (email e telefone) nao serao compartilhados com terceiros e serao utilizados exclusivamente para as finalidades descritas acima.

Este consentimento esta em conformidade com a Lei Geral de Protecao de Dados (LGPD - Lei n. 13.709/2018).

Ao rolar ate o final deste texto e marcar a caixa abaixo, voce confirma que leu e compreendeu todos os termos acima.`;

export default function SignupPage() {
  const { signUpWithEmail, signInWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [fullName, setFullName] = useState("");
  const [company, setCompany] = useState("");
  const [sector, setSector] = useState("");
  const [sectorOther, setSectorOther] = useState("");
  const [phone, setPhone] = useState("");
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false);
  const [whatsappConsent, setWhatsappConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const scrollBoxRef = useRef<HTMLDivElement>(null);

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneBR(e.target.value);
    setPhone(formatted);
  };

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
    if (isAtBottom && !hasScrolledToBottom) {
      setHasScrolledToBottom(true);
    }
  }, [hasScrolledToBottom]);

  const handleConsentChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (hasScrolledToBottom) {
      setWhatsappConsent(e.target.checked);
    }
  };

  const isSectorValid = sector !== "" && (sector !== "outro" || sectorOther.trim() !== "");

  const passwordsMatch = password === confirmPassword && password.length >= 6;

  const isFormValid =
    fullName.trim() !== "" &&
    company.trim() !== "" &&
    isSectorValid &&
    email.trim() !== "" &&
    passwordsMatch &&
    isValidPhone(phone) &&
    whatsappConsent;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!isValidPhone(phone)) {
      setError("Telefone invalido. Use o formato (XX) XXXXX-XXXX");
      return;
    }

    if (password !== confirmPassword) {
      setError("As senhas nao coincidem");
      return;
    }

    if (!whatsappConsent) {
      setError("Voce precisa aceitar os termos para continuar");
      return;
    }

    setLoading(true);

    const finalSector = sector === "outro" ? sectorOther.trim() : sector;

    try {
      await signUpWithEmail(email, password, fullName, company, finalSector, extractDigits(phone), whatsappConsent);
      setSuccess(true);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao criar conta";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg text-center">
          <div className="text-4xl mb-4">&#10003;</div>
          <h2 className="text-xl font-semibold text-[var(--ink)] mb-2">Conta criada!</h2>
          <p className="text-[var(--ink-secondary)]">
            Verifique seu email <strong>{email}</strong> para confirmar o cadastro.
          </p>
          <Link
            href="/login"
            className="mt-6 inline-block text-[var(--brand-blue)] hover:underline"
          >
            Ir para login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Left: Institutional Sidebar */}
      <InstitutionalSidebar variant="signup" className="w-full md:w-1/2" />

      {/* Right: Signup Form */}
      <div className="w-full md:w-1/2 flex items-center justify-center bg-[var(--canvas)] p-4 py-8">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg">
          <h1 className="text-2xl font-display font-bold text-center text-[var(--ink)] mb-2">
            Criar conta
          </h1>
          <p className="text-center text-[var(--ink-secondary)] mb-6">
            Comece com 3 buscas gratuitas
          </p>

        {error && (
          <div className="mb-4 p-3 bg-[var(--error-subtle)] text-[var(--error)] rounded-input text-sm">
            {error}
          </div>
        )}

        {/* Google OAuth */}
        <button
          onClick={() => signInWithGoogle()}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 mb-4
                     border border-[var(--border)] rounded-button bg-[var(--surface-0)]
                     text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors"
        >
          <svg
              role="img"
              aria-label="Ícone" width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Cadastrar com Google
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-[var(--border)]" />
          <span className="text-xs text-[var(--ink-muted)]">OU</span>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Full Name */}
          <div>
            <label htmlFor="fullName" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Nome completo
            </label>
            <input
              id="fullName"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-4 py-3 rounded-input border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                         focus:ring-[var(--brand-blue-subtle)]"
              placeholder="Seu nome"
            />
          </div>

          {/* Company */}
          <div>
            <label htmlFor="company" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Empresa
            </label>
            <input
              id="company"
              type="text"
              required
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="w-full px-4 py-3 rounded-input border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                         focus:ring-[var(--brand-blue-subtle)]"
              placeholder="Nome da sua empresa"
            />
          </div>

          {/* Sector */}
          <div>
            <label htmlFor="sector" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Setor de atuação
            </label>
            <select
              id="sector"
              required
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="w-full px-4 py-3 rounded-input border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                         focus:ring-[var(--brand-blue-subtle)]"
            >
              <option value="">Selecione um setor</option>
              {SECTORS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Sector Other - shown only when "outro" is selected */}
          {sector === "outro" && (
            <div>
              <label htmlFor="sectorOther" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
                Qual setor?
              </label>
              <input
                id="sectorOther"
                type="text"
                required
                value={sectorOther}
                onChange={(e) => setSectorOther(e.target.value)}
                className="w-full px-4 py-3 rounded-input border border-[var(--border)]
                           bg-[var(--surface-0)] text-[var(--ink)]
                           focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                           focus:ring-[var(--brand-blue-subtle)]"
                placeholder="Descreva seu setor de atuação"
              />
            </div>
          )}

          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-input border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                         focus:ring-[var(--brand-blue-subtle)]"
              placeholder="seu@email.com"
            />
          </div>

          {/* WhatsApp Phone */}
          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              <span className="flex items-center gap-2">
                <svg
              role="img"
              aria-label="Ícone" className="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
                WhatsApp
              </span>
            </label>
            <input
              id="phone"
              type="tel"
              required
              value={phone}
              onChange={handlePhoneChange}
              className="w-full px-4 py-3 rounded-input border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                         focus:ring-[var(--brand-blue-subtle)]"
              placeholder="(11) 99999-9999"
            />
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Senha
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 pr-12 rounded-input border border-[var(--border)]
                           bg-[var(--surface-0)] text-[var(--ink)]
                           focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                           focus:ring-[var(--brand-blue-subtle)]"
                placeholder="Minimo 6 caracteres"
                minLength={6}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--ink-muted)]
                           hover:text-[var(--ink)] transition-colors"
                aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
              >
                {showPassword ? (
                  <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Confirmar senha
            </label>
            <div className="relative">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`w-full px-4 py-3 pr-12 rounded-input border
                           bg-[var(--surface-0)] text-[var(--ink)]
                           focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                           focus:ring-[var(--brand-blue-subtle)]
                           ${confirmPassword && password !== confirmPassword
                             ? 'border-[var(--error)]'
                             : 'border-[var(--border)]'}`}
                placeholder="Digite a senha novamente"
                minLength={6}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--ink-muted)]
                           hover:text-[var(--ink)] transition-colors"
                aria-label={showConfirmPassword ? "Ocultar senha" : "Mostrar senha"}
              >
                {showConfirmPassword ? (
                  <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            {confirmPassword && password !== confirmPassword && (
              <p className="mt-1 text-xs text-[var(--error)]">As senhas nao coincidem</p>
            )}
          </div>

          {/* Consent Terms Scroll Box */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-[var(--ink-secondary)]">
              Termos de consentimento
              {!hasScrolledToBottom && (
                <span className="ml-2 text-xs text-[var(--ink-muted)]">
                  (role ate o final para aceitar)
                </span>
              )}
            </label>
            <div
              ref={scrollBoxRef}
              onScroll={handleScroll}
              data-testid="consent-scroll-box"
              className="h-36 overflow-y-auto p-3 text-xs text-[var(--ink-secondary)]
                         bg-[var(--surface-1)] border border-[var(--border)] rounded-input
                         whitespace-pre-wrap leading-relaxed"
            >
              {CONSENT_TERMS}
            </div>

            {/* Scroll indicator */}
            {!hasScrolledToBottom && (
              <div className="flex items-center justify-center gap-1 text-xs text-[var(--ink-muted)]">
                <svg
              role="img"
              aria-label="Ícone" className="w-4 h-4 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
                Role para baixo
              </div>
            )}

            {/* Consent Checkbox */}
            <label className={`flex items-start gap-3 p-3 rounded-input border transition-colors cursor-pointer
                              ${hasScrolledToBottom
                                ? "border-[var(--border)] hover:bg-[var(--surface-1)]"
                                : "border-[var(--border)] opacity-50 cursor-not-allowed"}`}>
              <input
                type="checkbox"
                checked={whatsappConsent}
                onChange={handleConsentChange}
                disabled={!hasScrolledToBottom}
                className="mt-0.5 w-4 h-4 rounded border-[var(--border)] text-[var(--brand-blue)]
                           focus:ring-[var(--brand-blue)] disabled:opacity-50"
              />
              <span className="text-sm text-[var(--ink)]">
                Li e aceito os termos de consentimento
              </span>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading || !isFormValid}
            className="w-full py-3 bg-[var(--brand-navy)] text-white rounded-button
                       font-semibold hover:bg-[var(--brand-blue)] transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Criando conta..." : "Criar conta"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--ink-secondary)]">
          Ja tem conta?{" "}
          <Link href="/login" className="text-[var(--brand-blue)] hover:underline">
            Fazer login
          </Link>
        </p>
        </div>
      </div>
    </div>
  );
}
