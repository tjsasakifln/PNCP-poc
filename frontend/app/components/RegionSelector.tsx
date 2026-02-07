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

  // AC12: Calculate how many states would be added on click
  const getUnselectedCount = (regionUfs: string[]) =>
    regionUfs.filter(uf => !selected.has(uf)).length;

  const handleClick = (key: string, regionUfs: string[]) => {
    // Trigger animation
    setClickedKey(key);
    setTimeout(() => setClickedKey(null), 200);

    // Execute callback
    onToggleRegion(regionUfs);
  };

  // AC12: Handle preview on hover
  const handleMouseEnter = (key: string, regionUfs: string[]) => {
    setHoveredKey(key);
    const unselected = regionUfs.filter(uf => !selected.has(uf));
    if (unselected.length > 0) {
      onPreviewStates?.(unselected);
    }
  };

  const handleMouseLeave = () => {
    setHoveredKey(null);
    onClearPreview?.();
  };

  return (
    <div className="flex flex-wrap gap-2 mb-3">
      {Object.entries(REGIONS).map(([key, region]) => {
        const full = isRegionFullySelected(region.ufs);
        const partial = isRegionPartiallySelected(region.ufs);
        const count = region.ufs.filter(uf => selected.has(uf)).length;
        const unselectedCount = getUnselectedCount(region.ufs);
        const isClicked = clickedKey === key;
        const isHovered = hoveredKey === key;

        return (
          <button
            key={key}
            onClick={() => handleClick(key, region.ufs)}
            onMouseEnter={() => handleMouseEnter(key, region.ufs)}
            onMouseLeave={handleMouseLeave}
            type="button"
            aria-label={`Selecionar região ${region.label}${unselectedCount > 0 ? ` (adicionar ${unselectedCount} estado${unselectedCount > 1 ? 's' : ''})` : ''}`}
            className={`px-3 py-1.5 rounded-button text-sm font-medium transition-all duration-200 border relative
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
                {/* AC12: Fully selected region with checkmark and remove button */}
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
                {/* AC12: Show partial selection count */}
                {partial && <span className="ml-1 text-xs opacity-75">({count}/{region.ufs.length})</span>}
                {/* AC12: Show preview badge on hover with count of states to be added */}
                {isHovered && !full && unselectedCount > 0 && (
                  <span className="ml-1.5 text-xs bg-brand-blue text-white rounded-full px-2 py-0.5 font-semibold animate-fadeIn">
                    +{unselectedCount}
                  </span>
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
