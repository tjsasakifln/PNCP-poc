/**
 * DEBT-011: Shared form field components for conta sub-routes.
 */

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

export function SelectField({ label, value, onChange, options }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">{label}</label>
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
    </div>
  );
}

export function NumberField({ label, value, onChange, placeholder }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">{label}</label>
      <input
        type="number"
        min={0}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm focus:border-[var(--brand-blue)] focus:outline-none"
      />
    </div>
  );
}
