import { Label } from "../../../components/ui/Label";
import { CNAEInput } from "./CNAEInput";
import type { OnboardingData } from "./types";

interface OnboardingStep1Props {
  data: OnboardingData;
  onChange: (partial: Partial<OnboardingData>) => void;
  errors: Record<string, { message?: string }>;
  onBlur: (field: string) => void;
}

export function OnboardingStep1({ data, onChange, errors, onBlur }: OnboardingStep1Props) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--ink)] mb-1">Qual é o seu negócio?</h2>
        <p className="text-sm text-[var(--ink-secondary)]">
          Informe seu segmento para encontrarmos oportunidades relevantes
        </p>
      </div>

      <CNAEInput
        value={data.cnae}
        onChange={(cnae) => onChange({ cnae })}
        onBlur={() => onBlur("cnae")}
        error={errors.cnae?.message}
      />

      <div>
        <Label required htmlFor="objetivo_principal">Qual é seu objetivo principal?</Label>
        <textarea
          id="objetivo_principal"
          value={data.objetivo_principal}
          onChange={(e) => onChange({ objetivo_principal: e.target.value.slice(0, 200) })}
          onBlur={() => onBlur("objetivo_principal")}
          placeholder="Ex: Encontrar oportunidades de uniformes escolares acima de R$ 100.000 em São Paulo"
          rows={3}
          className={`w-full px-3 py-2.5 rounded-lg border bg-[var(--surface-0)] text-sm text-[var(--ink)] placeholder:text-[var(--ink-secondary)] focus:ring-2 focus:ring-[var(--brand-blue)]/30 focus:border-[var(--brand-blue)] transition-all resize-none ${
            errors.objetivo_principal ? "border-[var(--error)]" : "border-[var(--border)]"
          }`}
          maxLength={200}
          aria-invalid={!!errors.objetivo_principal}
          aria-describedby={errors.objetivo_principal ? "objetivo-error" : undefined}
        />
        {errors.objetivo_principal && (
          <p id="objetivo-error" className="text-xs text-[var(--error)] mt-1" role="alert" data-testid="objetivo-error">
            {errors.objetivo_principal.message}
          </p>
        )}
        <p className="text-xs text-[var(--ink-secondary)] mt-1 text-right">
          {data.objetivo_principal.length}/200
        </p>
      </div>
    </div>
  );
}
