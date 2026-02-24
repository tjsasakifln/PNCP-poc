"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

// ─── Types ───────────────────────────────────────────────────────────────────

type QuestionType = "select" | "multi-select" | "numeric-pair";

interface QuestionOption {
  value: string;
  label: string;
}

interface Question {
  id: string;
  title: string;
  micro_copy: string;
  type: QuestionType;
  options?: QuestionOption[];
  field1?: { key: string; label: string; placeholder?: string };
  field2?: { key: string; label: string; placeholder?: string };
}

interface CompletenessResponse {
  completeness_pct: number;
  next_question?: string | null;
  is_complete: boolean;
}

interface ProfileCompletionPromptProps {
  /** Bearer token for API calls */
  accessToken?: string | null;
  /** Called after a successful save (e.g. to refresh parent data) */
  onProfileUpdated?: (percentage: number) => void;
}

// ─── Question Definitions ─────────────────────────────────────────────────────

const QUESTIONS: Record<string, Question> = {
  company_size: {
    id: "company_size",
    title: "Qual o porte da sua empresa?",
    micro_copy:
      "Usamos essa informação para filtrar editais com exigências de porte adequado, evitando falsos positivos de habilitação.",
    type: "select",
    options: [
      { value: "mei", label: "MEI — Microempreendedor Individual" },
      { value: "me", label: "ME — Microempresa" },
      { value: "epp", label: "EPP — Empresa de Pequeno Porte" },
      { value: "medio", label: "Médio Porte" },
      { value: "grande", label: "Grande Empresa" },
    ],
  },
  experience_level: {
    id: "experience_level",
    title: "Qual sua experiência com licitações?",
    micro_copy:
      "Isso ajuda o SmartLic a calibrar a complexidade das oportunidades sugeridas e a linguagem das análises.",
    type: "select",
    options: [
      { value: "iniciante", label: "Iniciante — nunca participei" },
      { value: "basico", label: "Básico — já participei de algumas" },
      { value: "intermediario", label: "Intermediário — participo regularmente" },
      { value: "avancado", label: "Avançado — processo sistematizado" },
    ],
  },
  company_metrics: {
    id: "company_metrics",
    title: "Quantos funcionários e faturamento anual?",
    micro_copy:
      "Usamos isso para avaliar sua capacidade de atender editais com exigências de porte e para calcular viabilidade financeira.",
    type: "numeric-pair",
    field1: {
      key: "num_employees",
      label: "Funcionários",
      placeholder: "Ex: 15",
    },
    field2: {
      key: "annual_revenue",
      label: "Faturamento anual (R$)",
      placeholder: "Ex: 500000",
    },
  },
  certifications: {
    id: "certifications",
    title: "Quais atestados/certificações sua empresa possui?",
    micro_copy:
      "Atestados aumentam sua elegibilidade em editais especializados. Selecionando aqui, evitamos sugerir editais que exigem o que você não tem.",
    type: "multi-select",
    options: [
      { value: "crea", label: "CREA (Engenharia)" },
      { value: "crf", label: "CRF (Farmácia)" },
      { value: "inmetro", label: "INMETRO" },
      { value: "iso_9001", label: "ISO 9001 (Qualidade)" },
      { value: "iso_14001", label: "ISO 14001 (Ambiental)" },
      { value: "pgr_pcmso", label: "PGR/PCMSO (Segurança do Trabalho)" },
      { value: "alvara_sanitario", label: "Alvará Sanitário" },
      { value: "registro_anvisa", label: "Registro ANVISA" },
      { value: "habilitacao_antt", label: "Habilitação ANTT" },
      { value: "registro_cfq", label: "Registro CRQ (Química)" },
      { value: "licenca_ambiental", label: "Licença Ambiental" },
      { value: "crt", label: "CRT (Técnico)" },
      { value: "nenhum", label: "Nenhum no momento" },
    ],
  },
};

// Question order (same as story spec)
const QUESTION_ORDER = [
  "company_size",
  "experience_level",
  "company_metrics",
  "certifications",
];

// ─── LocalStorage helpers ─────────────────────────────────────────────────────

const SKIPPED_KEY_PREFIX = "profile_question_skipped_";
const SAVED_KEY_PREFIX = "profile_question_saved_";

function markSkipped(questionId: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(`${SKIPPED_KEY_PREFIX}${questionId}`, "true");
  } catch {
    // ignore
  }
}

function markSaved(questionId: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(`${SAVED_KEY_PREFIX}${questionId}`, "true");
    // Clear skipped flag if it was set before
    localStorage.removeItem(`${SKIPPED_KEY_PREFIX}${questionId}`);
  } catch {
    // ignore
  }
}

function isSkippedThisSession(questionId: string): boolean {
  if (typeof window === "undefined") return false;
  // We store skipped in sessionStorage so it reappears on next visit
  try {
    return sessionStorage.getItem(`${SKIPPED_KEY_PREFIX}${questionId}`) === "true";
  } catch {
    return false;
  }
}

function setSkippedThisSession(questionId: string): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(`${SKIPPED_KEY_PREFIX}${questionId}`, "true");
  } catch {
    // ignore
  }
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SelectQuestion({
  question,
  value,
  onChange,
}: {
  question: Question;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-2" role="radiogroup" aria-label={question.title}>
      {(question.options ?? []).map((opt) => (
        <button
          key={opt.value}
          type="button"
          role="radio"
          aria-checked={value === opt.value}
          onClick={() => onChange(opt.value)}
          className={`w-full text-left px-4 py-3 rounded-input border text-sm transition-colors ${
            value === opt.value
              ? "border-[var(--brand-blue)] bg-blue-50 dark:bg-blue-900/20 text-[var(--brand-blue)] font-medium"
              : "border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] hover:bg-[var(--surface-1)]"
          }`}
          data-testid={`option-${opt.value}`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function MultiSelectQuestion({
  question,
  values,
  onChange,
}: {
  question: Question;
  values: string[];
  onChange: (v: string[]) => void;
}) {
  const toggle = (val: string) => {
    if (val === "nenhum") {
      onChange(["nenhum"]);
      return;
    }
    const next = values.includes(val)
      ? values.filter((v) => v !== val)
      : [...values.filter((v) => v !== "nenhum"), val];
    onChange(next);
  };

  return (
    <div className="space-y-2" role="group" aria-label={question.title}>
      {(question.options ?? []).map((opt) => {
        const selected = values.includes(opt.value);
        return (
          <button
            key={opt.value}
            type="button"
            aria-pressed={selected}
            onClick={() => toggle(opt.value)}
            className={`w-full text-left px-4 py-3 rounded-input border text-sm transition-colors flex items-center gap-3 ${
              selected
                ? "border-[var(--brand-blue)] bg-blue-50 dark:bg-blue-900/20 text-[var(--brand-blue)] font-medium"
                : "border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] hover:bg-[var(--surface-1)]"
            }`}
            data-testid={`option-${opt.value}`}
          >
            <span
              className={`w-4 h-4 rounded flex-shrink-0 border-2 flex items-center justify-center transition-colors ${
                selected
                  ? "border-[var(--brand-blue)] bg-[var(--brand-blue)]"
                  : "border-[var(--border)]"
              }`}
            >
              {selected && (
                <svg
                  className="w-2.5 h-2.5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              )}
            </span>
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

function NumericPairQuestion({
  question,
  values,
  onChange,
}: {
  question: Question;
  values: Record<string, string>;
  onChange: (v: Record<string, string>) => void;
}) {
  const f1 = question.field1!;
  const f2 = question.field2!;

  return (
    <div className="space-y-4">
      <div>
        <label
          htmlFor={`field-${f1.key}`}
          className="block text-sm font-medium text-[var(--ink-secondary)] mb-1"
        >
          {f1.label}
        </label>
        <input
          id={`field-${f1.key}`}
          type="number"
          min={0}
          value={values[f1.key] ?? ""}
          onChange={(e) => onChange({ ...values, [f1.key]: e.target.value })}
          placeholder={f1.placeholder}
          className="w-full px-4 py-3 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue-subtle)]"
          data-testid={`input-${f1.key}`}
        />
      </div>
      <div>
        <label
          htmlFor={`field-${f2.key}`}
          className="block text-sm font-medium text-[var(--ink-secondary)] mb-1"
        >
          {f2.label}
        </label>
        <input
          id={`field-${f2.key}`}
          type="number"
          min={0}
          value={values[f2.key] ?? ""}
          onChange={(e) => onChange({ ...values, [f2.key]: e.target.value })}
          placeholder={f2.placeholder}
          className="w-full px-4 py-3 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue-subtle)]"
          data-testid={`input-${f2.key}`}
        />
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

/**
 * STORY-260: Shows 1 question at a time based on GET /v1/profile/completeness → next_question.
 * After save: success animation, next question on NEXT visit (not immediately).
 * After skip: disappears for this session, reappears on next dashboard visit.
 */
export default function ProfileCompletionPrompt({
  accessToken,
  onProfileUpdated,
}: ProfileCompletionPromptProps) {
  const [question, setQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form state for different question types
  const [selectValue, setSelectValue] = useState<string>("");
  const [multiValues, setMultiValues] = useState<string[]>([]);
  const [numericValues, setNumericValues] = useState<Record<string, string>>({});

  const fetchNextQuestion = useCallback(async () => {
    try {
      const headers: Record<string, string> = {};
      if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
      }

      const res = await fetch("/api/profile-completeness", { headers });
      if (!res.ok) {
        setLoading(false);
        return;
      }

      const data: CompletenessResponse = await res.json();

      // If complete, nothing to show
      if (data.is_complete || !data.next_question) {
        setLoading(false);
        return;
      }

      const nextId = data.next_question;

      // Skip if user already dismissed this session
      if (isSkippedThisSession(nextId)) {
        setLoading(false);
        return;
      }

      // Find the question definition
      const q = QUESTIONS[nextId];
      if (!q) {
        // Try next in order
        const idx = QUESTION_ORDER.indexOf(nextId);
        if (idx >= 0) {
          for (let i = idx + 1; i < QUESTION_ORDER.length; i++) {
            const fallback = QUESTIONS[QUESTION_ORDER[i]];
            if (fallback && !isSkippedThisSession(fallback.id)) {
              setQuestion(fallback);
              break;
            }
          }
        }
        setLoading(false);
        return;
      }

      setQuestion(q);
      setLoading(false);
    } catch {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchNextQuestion();
  }, [fetchNextQuestion]);

  // Map question IDs to backend field names in PerfilContexto schema
  const QUESTION_TO_FIELD: Record<string, string> = {
    company_size: "porte_empresa",
    experience_level: "experiencia_licitacoes",
    certifications: "atestados",
    // company_metrics uses field1/field2 keys directly (num_employees → capacidade_funcionarios, annual_revenue → faturamento_anual)
  };

  const getFieldPayload = (): Record<string, unknown> | null => {
    if (!question) return null;

    switch (question.type) {
      case "select": {
        if (!selectValue) return null;
        const fieldName = QUESTION_TO_FIELD[question.id] ?? question.id;
        return { [fieldName]: selectValue };
      }

      case "multi-select": {
        if (multiValues.length === 0) return null;
        const fieldName = QUESTION_TO_FIELD[question.id] ?? question.id;
        return { [fieldName]: multiValues };
      }

      case "numeric-pair": {
        const f1 = question.field1!;
        const f2 = question.field2!;
        const v1 = numericValues[f1.key];
        const v2 = numericValues[f2.key];
        if (!v1 || !v2) return null;
        // Map field keys to backend names
        const fieldMap: Record<string, string> = {
          num_employees: "capacidade_funcionarios",
          annual_revenue: "faturamento_anual",
        };
        return {
          [fieldMap[f1.key] ?? f1.key]: Number(v1),
          [fieldMap[f2.key] ?? f2.key]: Number(v2),
        };
      }
    }
  };

  const isValid = getFieldPayload() !== null;

  const handleSave = async () => {
    const fieldPayload = getFieldPayload();
    if (!fieldPayload || !question) return;

    setSaving(true);
    try {
      const authHeaders: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (accessToken) {
        authHeaders["Authorization"] = `Bearer ${accessToken}`;
      }

      // GET current context first to merge partial update
      let existingContext: Record<string, unknown> = {};
      try {
        const getRes = await fetch("/api/profile-context", {
          headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
        });
        if (getRes.ok) {
          const getData = await getRes.json();
          existingContext = getData.context_data ?? {};
        }
      } catch {
        // best-effort: proceed with just the new field
      }

      // Merge new field into existing context
      const mergedPayload = { ...existingContext, ...fieldPayload };

      const res = await fetch("/api/profile-context", {
        method: "PUT",
        headers: authHeaders,
        body: JSON.stringify(mergedPayload),
      });

      if (res.ok) {
        markSaved(question.id);
        setSaveSuccess(true);

        // Fetch updated percentage for parent callback
        try {
          const completenessRes = await fetch("/api/profile-completeness", {
            headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
          });
          if (completenessRes.ok) {
            const data: CompletenessResponse = await completenessRes.json();
            onProfileUpdated?.(data.completeness_pct);
          }
        } catch {
          // best-effort
        }

        // Hide after brief success animation — next question shows on next visit
        setTimeout(() => {
          setDismissed(true);
        }, 1800);
      }
    } catch {
      // silent fail
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = () => {
    if (question) {
      setSkippedThisSession(question.id);
    }
    setDismissed(true);
  };

  // Don't render if still loading, dismissed, or no question
  if (loading || dismissed || !question) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="rounded-2xl border border-[var(--border)] bg-[var(--surface-0)] shadow-sm overflow-hidden"
        data-testid="profile-completion-prompt"
      >
        {/* Header strip */}
        <div className="px-5 py-3 bg-[var(--surface-1)] border-b border-[var(--border)] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg
              className="w-4 h-4 text-[var(--brand-blue)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
            <span className="text-xs font-semibold text-[var(--ink-secondary)] uppercase tracking-wide">
              Complete seu perfil
            </span>
          </div>
          <span className="text-xs text-[var(--ink-muted)]">
            {QUESTION_ORDER.indexOf(question.id) + 1}/{QUESTION_ORDER.length}
          </span>
        </div>

        <div className="px-5 py-5">
          {/* Success state */}
          <AnimatePresence>
            {saveSuccess && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center py-6 text-center"
                data-testid="save-success"
              >
                <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-800/40 flex items-center justify-center mb-3">
                  <svg
                    className="w-6 h-6 text-emerald-600 dark:text-emerald-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2.5}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-[var(--ink)]">Salvo!</p>
                <p className="text-xs text-[var(--ink-secondary)] mt-1">
                  Suas análises ficaram mais precisas.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Question */}
          {!saveSuccess && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-[var(--ink)] mb-1">
                  {question.title}
                </h3>
                <p className="text-xs text-[var(--ink-secondary)] leading-relaxed">
                  {question.micro_copy}
                </p>
              </div>

              {/* Input */}
              {question.type === "select" && (
                <SelectQuestion
                  question={question}
                  value={selectValue}
                  onChange={setSelectValue}
                />
              )}

              {question.type === "multi-select" && (
                <MultiSelectQuestion
                  question={question}
                  values={multiValues}
                  onChange={setMultiValues}
                />
              )}

              {question.type === "numeric-pair" && (
                <NumericPairQuestion
                  question={question}
                  values={numericValues}
                  onChange={setNumericValues}
                />
              )}

              {/* Actions */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={handleSave}
                  disabled={saving || !isValid}
                  className="flex-1 py-2.5 bg-[var(--brand-navy)] text-white rounded-button font-semibold text-sm hover:bg-[var(--brand-blue)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  data-testid="save-button"
                >
                  {saving ? "Salvando..." : "Salvar"}
                </button>
                <button
                  onClick={handleSkip}
                  className="text-sm text-[var(--ink-muted)] hover:text-[var(--ink)] hover:underline transition-colors py-2.5 px-2"
                  data-testid="skip-button"
                >
                  Pular por enquanto
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
