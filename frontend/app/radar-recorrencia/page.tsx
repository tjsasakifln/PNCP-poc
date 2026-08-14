"use client";
/**
 * PREDINT-022 (#1671): Radar de Recorrencia Governamental
 *
 * Pagina flagship /radar-recorrencia que consolida os sinais preditivos
 * em uma interface de descoberta premium.
 *
 * 3 blocos funcionais:
 *   1. RecorrenciaTable — contratos expirando
 *   2. OrgaosRecorrentes — orgaos com maior recorencia
 *   3. IncumbentAlert — alertas de incumbente
 *
 * Feature flag: PREDICTIVE_INTEL_ENABLED
 * Plan capability: allow_predictive_intel
 */

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/components/AuthProvider";
import { RecorrenciaTable } from "@/app/components/RecorrenciaTable";
import { OrgaosRecorrentes } from "@/app/components/OrgaoRecorrenteCard";
import { IncumbentAlert } from "@/app/components/IncumbentAlert";
import { PredictiveNarrative } from "@/app/components/PredictiveNarrative";

// ---------------------------------------------------------------------------
// Upgrade CTA component
// ---------------------------------------------------------------------------

function UpgradeBanner() {
  return (
    <div className="max-w-4xl mx-auto py-20 px-4 text-center">
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl border p-12">
        <span className="text-5xl block mb-4" aria-hidden="true">
          &#x1F52D;
        </span>
        <h1 className="text-2xl font-bold text-gray-900 mb-3">
          Radar de Recorrencia Governamental
        </h1>
        <p className="text-gray-500 mb-6 max-w-md mx-auto">
          Antecipe renovacoes contratuais e identifique orgaos com alta
          recorencia de contratacoes. Disponível no plano SmartLic Command.
        </p>
        <a
          href="/consultoria-b2g?ref=radar-recorrencia"
          className="inline-block rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm"
        >
          Conhecer o SmartLic Command &rarr;
        </a>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Loading Skeleton
// ---------------------------------------------------------------------------

function PageSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 animate-pulse">
      <div className="h-8 w-64 bg-gray-100 rounded mb-2" />
      <div className="h-4 w-96 bg-gray-100 rounded mb-8" />
      <div className="h-64 bg-gray-50 rounded-lg mb-8" />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-32 bg-gray-50 rounded-lg" />
        ))}
      </div>
      <div className="h-40 bg-gray-50 rounded-lg" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Error Boundary (per-block)
// ---------------------------------------------------------------------------

function ErrorBlock({
  children,
  title,
}: {
  children: React.ReactNode;
  title?: string;
}) {
  return (
    <div className="bg-gray-50 rounded-lg border p-6 text-center">
      <p className="text-sm text-gray-500 mb-2">
        {title || "Dados temporariamente indisponiveis"}
      </p>
      <div className="flex justify-center">{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Block Wrapper
// ---------------------------------------------------------------------------

interface BlockWrapperProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  error?: boolean;
  testId?: string;
}

function BlockWrapper({
  title,
  description,
  children,
  error = false,
  testId,
}: BlockWrapperProps) {
  return (
    <section
      className="mb-10"
      data-testid={testId || `block-${title.toLowerCase().replace(/\s+/g, "-")}`}
    >
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
        {description && (
          <p className="text-sm text-gray-500 mt-1">{description}</p>
        )}
      </div>
      {error ? (
        <ErrorBlock>
          <button
            onClick={() => window.location.reload()}
            className="text-sm text-blue-600 hover:underline"
          >
            Tentar novamente
          </button>
        </ErrorBlock>
      ) : (
        children
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function RadarRecorrenciaPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [capabilityChecked, setCapabilityChecked] = useState(false);
  const [hasCapability, setHasCapability] = useState(false);
  const [blocksError, setBlocksError] = useState<Record<string, boolean>>({});

  // Check feature flag and capability
  useEffect(() => {
    if (authLoading) return;

    if (!user) {
      setHasCapability(false);
      setCapabilityChecked(true);
      return;
    }

    // Check feature flag via health endpoint
    fetch("/api/features", { credentials: "include" })
      .then((res) => (res.ok ? res.json() : null))
      .then((features) => {
        // Also check user profile for capability flag
        return fetch("/v1/user/me", { credentials: "include" })
          .then((res) => (res.ok ? res.json() : null));
      })
      .then((profile) => {
        const caps = profile?.capabilities ?? {};
        const allowed = caps.allow_predictive_intel === true;
        setHasCapability(allowed);
        setCapabilityChecked(true);
      })
      .catch(() => {
        // Feature flag off or error — redirect to upgrade
        setHasCapability(false);
        setCapabilityChecked(true);
      });
  }, [user, authLoading]);

  // Auth loading
  if (authLoading) {
    return <PageSkeleton />;
  }

  // Not logged in or no capability
  if (!user || !hasCapability) {
    return <UpgradeBanner />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Radar de Recorrencia Governamental
          </h1>
          <p className="text-gray-500 mt-2">
            Antecipe renovacoes contratuais, identifique orgaos recorrentes e
            monitore alertas de incumbentes
          </p>
        </div>

        {/* Block 1: Contratos Expirando */}
        <BlockWrapper
          title="Contratos Expirando"
          description="Contratos proximos do vencimento com alta probabilidade de renovacao"
          error={blocksError["recorrencia"]}
          testId="block-contratos-expirando"
        >
          <RecorrenciaTable />
        </BlockWrapper>

        {/* Block 2: Orgaos Mais Recorrentes */}
        <BlockWrapper
          title="Orgaos Mais Recorrentes"
          description="Orgaos com maior indice de recorrencia contratual"
          error={blocksError["orgaos"]}
          testId="block-orgaos-recorrentes"
        >
          <OrgaosRecorrentes />
        </BlockWrapper>

        {/* Block 3: Alertas de Incumbente */}
        <BlockWrapper
          title="Alertas de Incumbente"
          description="Fornecedores com sinais de perda de espaco em orgaos publicos"
          error={blocksError["incumbentes"]}
          testId="block-incumbentes"
        >
          <IncumbentAlert />
        </BlockWrapper>

        {/* Predictive Narrative */}
        <BlockWrapper
          title="Analise Preditiva"
          description="Gere uma analise narrativa baseada nos sinais de recorrencia"
          testId="block-analise-preditiva"
        >
          <PredictiveNarrative />
        </BlockWrapper>
      </div>
    </div>
  );
}
