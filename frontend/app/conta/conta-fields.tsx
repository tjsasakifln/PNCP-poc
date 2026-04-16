/**
 * DEBT-011: Shared form field components for conta sub-routes.
 */

import { Label } from "../../components/ui/Label";

export function ProfileField({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex items-start justify-between">
      <span className="text-sm text-[var(--ink-muted)] w-36 flex-shrink-0">{label}</span>
      <span className="text-sm text-[var(--ink)] text-right">
        {value || <span className="text-[var(--ink-muted)] italic">Não informado</span>}
      </span>
    </div>
  );
}

export function SelectField({ label, value, onChange, options, error }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Array<{ value: string; label: string }>;
  error?: string;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm focus:border-[var(--brand-blue)] focus:outline-none"
      >
        <option value="">Selecione...</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {error && <p className="mt-1 text-xs text-error" role="alert" aria-live="assertive">{error}</p>}
    </div>
  );
}

export function NumberField({ label, value, onChange, placeholder, error }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  error?: string;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <input
        type="number"
        min={0}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm focus:border-[var(--brand-blue)] focus:outline-none"
      />
      {error && <p className="mt-1 text-xs text-error" role="alert" aria-live="assertive">{error}</p>}
    </div>
  );
}
