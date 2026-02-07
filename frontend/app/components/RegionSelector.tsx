"use client";

import { useState } from "react";

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
  onPreviewStates?: (ufs: string[]) => void;
  onClearPreview?: () => void;
}

export function RegionSelector({ selected, onToggleRegion, onPreviewStates, onClearPreview }: RegionSelectorProps) {
  const [clickedKey, setClickedKey] = useState<string | null>(null);
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);

  const isRegionFullySelected = (regionUfs: string[]) =>
    regionUfs.every(uf => selected.has(uf));

  const isRegionPartiallySelected = (regionUfs: string[]) =>
    regionUfs.some(uf => selected.has(uf)) && !isRegionFullySelected(regionUfs);

  const handleClick = (key: string, regionUfs: string[]) => {
    // Trigger animation
    setClickedKey(key);
    setTimeout(() => setClickedKey(null), 200);

    // Execute callback
    onToggleRegion(regionUfs);
  };

  return (
    <div className="flex flex-wrap gap-2 mb-3">
      {Object.entries(REGIONS).map(([key, region]) => {
        const full = isRegionFullySelected(region.ufs);
        const partial = isRegionPartiallySelected(region.ufs);
        const count = region.ufs.filter(uf => selected.has(uf)).length;
        const unselectedCount = region.ufs.filter(uf => !selected.has(uf)).length;
        const isClicked = clickedKey === key;

        return (
          <button
            key={key}
            onClick={() => handleClick(key, region.ufs)}
            onMouseEnter={() => {
              setHoveredKey(key);
              onPreviewStates?.(region.ufs.filter(uf => !selected.has(uf)));
            }}
            onMouseLeave={() => {
              setHoveredKey(null);
              onClearPreview?.();
            }}
            type="button"
            aria-label={`Selecionar região ${region.label}`}
            className={`px-3 py-1 rounded-button text-sm font-medium transition-all duration-200 border
                       ${isClicked ? 'scale-95' : 'scale-100 hover:scale-105'}
                       active:scale-95
                       ${
              full
                ? "bg-brand-navy text-white border-brand-navy"
                : partial
                  ? "bg-brand-blue-subtle text-brand-blue border-accent"
                  : "bg-surface-1 text-ink-secondary border-transparent hover:border-accent hover:text-brand-blue"
            }`}
          >
            {full ? (
              <>
                {region.label} ✓
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleRegion(region.ufs);
                  }}
                  className="ml-1 text-xs opacity-75 hover:opacity-100"
                  aria-label={`Remover região ${region.label}`}
                >
                  ×
                </button>
              </>
            ) : (
              <>
                {region.label}
                {partial && <span className="ml-1 text-xs opacity-75">({count}/{region.ufs.length})</span>}
                {hoveredKey === key && !full && unselectedCount > 0 && (
                  <span className="ml-1 text-xs bg-brand-blue text-white rounded-full px-1.5">+{unselectedCount}</span>
                )}
              </>
            )}
          </button>
        );
      })}
    </div>
  );
}

export { REGIONS };
