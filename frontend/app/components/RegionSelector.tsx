"use client";

const REGIONS: Record<string, { label: string; ufs: string[] }> = {
  norte: { label: "Norte", ufs: ["AC", "AP", "AM", "PA", "RO", "RR", "TO"] },
  nordeste: { label: "Nordeste", ufs: ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"] },
  centro_oeste: { label: "Centro-Oeste", ufs: ["DF", "GO", "MT", "MS"] },
  sudeste: { label: "Sudeste", ufs: ["ES", "MG", "RJ", "SP"] },
  sul: { label: "Sul", ufs: ["PR", "RS", "SC"] },
};

interface RegionSelectorProps {
  selected: Set<string>;
  onToggleRegion: (ufs: string[]) => void;
}

export function RegionSelector({ selected, onToggleRegion }: RegionSelectorProps) {
  const isRegionFullySelected = (regionUfs: string[]) =>
    regionUfs.every(uf => selected.has(uf));

  const isRegionPartiallySelected = (regionUfs: string[]) =>
    regionUfs.some(uf => selected.has(uf)) && !isRegionFullySelected(regionUfs);

  return (
    <div className="flex flex-wrap gap-2 mb-3">
      {Object.entries(REGIONS).map(([key, region]) => {
        const full = isRegionFullySelected(region.ufs);
        const partial = isRegionPartiallySelected(region.ufs);
        const count = region.ufs.filter(uf => selected.has(uf)).length;

        return (
          <button
            key={key}
            onClick={() => onToggleRegion(region.ufs)}
            type="button"
            aria-label={`Selecionar região ${region.label}`}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-150 border ${
              full
                ? "bg-emerald-700 text-white border-emerald-700"
                : partial
                  ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 border-green-500/30 dark:border-green-400/30"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200/60 dark:border-gray-700/40 hover:border-green-500/50"
            }`}
          >
            {region.label}
            {partial && <span className="ml-1 text-xs opacity-75">({count}/{region.ufs.length})</span>}
          </button>
        );
      })}
    </div>
  );
}

export { REGIONS };
