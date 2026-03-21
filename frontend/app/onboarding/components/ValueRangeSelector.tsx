import { Label } from "../../../components/ui/Label";
import { VALUE_PRESETS } from "./types";

export function ValueRangeSelector({
  valorMin,
  valorMax,
  onChangeMin,
  onChangeMax,
}: {
  valorMin: number;
  valorMax: number;
  onChangeMin: (v: number) => void;
  onChangeMax: (v: number) => void;
}) {
  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(val);

  return (
    <div>
      <Label>Faixa de valor ideal dos contratos</Label>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-xs">Valor mínimo</Label>
          <select
            value={valorMin}
            onChange={(e) => onChangeMin(parseInt(e.target.value))}
            className="w-full min-h-[44px] px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)]"
          >
            <option value={0}>Sem limite</option>
            {VALUE_PRESETS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
        <div>
          <Label className="text-xs">Valor máximo</Label>
          <select
            value={valorMax}
            onChange={(e) => onChangeMax(parseInt(e.target.value))}
            className="w-full min-h-[44px] px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-sm text-[var(--ink)]"
          >
            <option value={0}>Sem limite</option>
            {VALUE_PRESETS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
      </div>
      {valorMin > 0 && valorMax > 0 && valorMax < valorMin && (
        <p className="text-xs text-[var(--error)] mt-1">
          Valor máximo deve ser maior que o mínimo
        </p>
      )}
      <div className="text-xs text-[var(--ink-secondary)] mt-2">
        {valorMin > 0 || valorMax > 0
          ? `Faixa: ${valorMin > 0 ? formatCurrency(valorMin) : "Sem mínimo"} — ${valorMax > 0 ? formatCurrency(valorMax) : "Sem máximo"}`
          : "Todas as faixas de valor"}
      </div>
    </div>
  );
}
