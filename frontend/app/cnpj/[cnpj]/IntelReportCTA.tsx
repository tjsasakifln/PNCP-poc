"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

// ----- CNPJ variant (INTEL-REPORT-001) -----

interface CnpjProps {
  cnpj: string;
}

/**
 * Intel Report CTA for /cnpj/[cnpj] pages (#632).
 *
 * Unauthenticated click → redirect to /consultoria-b2g (SaaS signup is sunset).
 * Authenticated click → Stripe Checkout for Raio-X do Concorrente (R$197).
 *
 * Must be a separate "use client" file because the parent page.tsx is a
 * Server Component with ISR (revalidate=3600 — SEO-FE-ISR-001 #1038).
 */
export default function IntelReportCTA({ cnpj }: CnpjProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleBuy = async () => {
    setLoading(true);
    try {
      if (typeof window !== "undefined" && window.mixpanel) {
        window.mixpanel.track("intel_report_cta_clicked", {
          cnpj,
          page_path: `/cnpj/${cnpj}`,
        });
      }

      const res = await fetch("/api/intel-reports/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_type: "cnpj", entity_key: cnpj }),
      });

      if (res.status === 401) {
        router.push(`/consultoria-b2g?ref=cnpj-${cnpj}&intent=intel_report`);
        return;
      }

      if (!res.ok) {
        throw new Error(`checkout failed: ${res.status}`);
      }

      const { checkout_url } = await res.json();

      if (typeof window !== "undefined" && window.mixpanel) {
        window.mixpanel.track("intel_report_checkout_started", {
          product_type: "cnpj",
          entity_key: cnpj,
        });
      }

      window.location.href = checkout_url;
    } catch {
      setLoading(false);
      alert("Não foi possível iniciar o checkout. Tente novamente.");
    }
  };

  return (
    <button
      onClick={handleBuy}
      disabled={loading}
      className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
    >
      {loading ? "Aguarde..." : "Comprar Raio-X — R$197"}
    </button>
  );
}

// ----- Sector × UF variant (INTEL-REPORT-002) -----

interface SectorUfProps {
  /** sector_id as in sectors_data.yaml — e.g. "limpeza" */
  sectorId: string;
  /** 2-letter UF code — e.g. "SP" */
  uf: string;
  /** Human-readable sector label for display — e.g. "Limpeza e Conservação" */
  sectorLabel?: string;
  /** Redirect path on 401 — defaults to /licitacoes/[sectorId] */
  redirectPath?: string;
}

/**
 * Intel Report CTA for Panorama Setorial × UF pages (INTEL-REPORT-002, #826).
 *
 * entity_key format sent to backend: "sectorId:UF" — e.g. "limpeza:SP".
 * Price: R$147 (set in backend/schemas/intel_report.py INTEL_REPORT_PRICES).
 */
export function SectorUfIntelReportCTA({
  sectorId,
  uf,
  sectorLabel,
  redirectPath,
}: SectorUfProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const entityKey = `${sectorId}:${uf}`;
  const displayLabel = sectorLabel || sectorId;
  const fallbackRedirect = redirectPath || `/licitacoes/${sectorId}`;

  const handleBuy = async () => {
    setLoading(true);
    try {
      if (typeof window !== "undefined" && window.mixpanel) {
        window.mixpanel.track("intel_report_cta_clicked", {
          product_type: "sector_uf",
          sector_id: sectorId,
          uf,
          entity_key: entityKey,
        });
      }

      const res = await fetch("/api/intel-reports/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_type: "sector_uf", entity_key: entityKey }),
      });

      if (res.status === 401) {
        router.push(
          `/consultoria-b2g?ref=sector-${sectorId}-${uf}&intent=intel_report_sector`
        );
        return;
      }

      if (!res.ok) {
        throw new Error(`checkout failed: ${res.status}`);
      }

      const { checkout_url } = await res.json();

      if (typeof window !== "undefined" && window.mixpanel) {
        window.mixpanel.track("intel_report_checkout_started", {
          product_type: "sector_uf",
          entity_key: entityKey,
        });
      }

      window.location.href = checkout_url;
    } catch {
      setLoading(false);
      alert("Não foi possível iniciar o checkout. Tente novamente.");
    }
  };

  return (
    <button
      onClick={handleBuy}
      disabled={loading}
      className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
    >
      {loading
        ? "Aguarde..."
        : `Comprar Panorama ${displayLabel} × ${uf} — R$147`}
    </button>
  );
}
