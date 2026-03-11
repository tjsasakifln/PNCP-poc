"use client";

import { useState } from "react";
import { usePipeline } from "../../hooks/usePipeline";
import { getUserFriendlyError } from "../../lib/error-messages";
import type { LicitacaoItem } from "../types";

interface AddToPipelineButtonProps {
  licitacao: LicitacaoItem;
  className?: string;
}

export function AddToPipelineButton({ licitacao, className = "" }: AddToPipelineButtonProps) {
  const { addItem } = usePipeline();
  const [status, setStatus] = useState<"idle" | "loading" | "saved" | "error" | "upgrade" | "limit">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (status === "saved" || status === "loading") return;

    setStatus("loading");
    try {
      await addItem({
        pncp_id: licitacao.pncp_id,
        objeto: licitacao.objeto,
        orgao: licitacao.orgao,
        uf: licitacao.uf,
        valor_estimado: licitacao.valor,
        data_encerramento: licitacao.data_encerramento || null,
        link_pncp: licitacao.link,
        stage: "descoberta",
        notes: null,
        search_id: null,
      });
      setStatus("saved");
      setTimeout(() => setStatus("idle"), 3000);
    } catch (err: unknown) {
      const raw = err instanceof Error ? err.message : "";
      const isPipelineLimit = err !== null && typeof err === 'object' && 'isPipelineLimitExceeded' in err && (err as { isPipelineLimitExceeded: boolean }).isPipelineLimitExceeded;
      if (raw.includes("já está no")) {
        setStatus("saved");
      } else if (isPipelineLimit) {
        // STORY-356 AC4: Pipeline limit exceeded — show upgrade state
        setStatus("limit");
        setErrorMsg(raw);
      } else if (raw.includes("plano") || raw.includes("disponível")) {
        setStatus("upgrade");
        setErrorMsg(getUserFriendlyError(err));
      } else {
        setStatus("error");
        setErrorMsg(getUserFriendlyError(err));
      }
      setTimeout(() => setStatus("idle"), 4000);
    }
  };

  const label =
    status === "loading"
      ? "Salvando..."
      : status === "saved"
      ? "No pipeline"
      : status === "error"
      ? "Erro"
      : status === "upgrade"
      ? "Upgrade"
      : status === "limit"
      ? "Limite"
      : "Pipeline";

  const colorClass =
    status === "saved"
      ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
      : status === "error"
      ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
      : status === "upgrade" || status === "limit"
      ? "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300"
      : "bg-brand-blue/10 text-brand-blue hover:bg-brand-blue/20";

  return (
    <button
      onClick={handleClick}
      disabled={status === "loading" || status === "saved"}
      className={`text-xs font-medium px-2.5 py-1 rounded-md transition-colors ${colorClass} disabled:opacity-60 ${className}`}
      title={status === "upgrade" || status === "limit" ? errorMsg : status === "error" ? errorMsg : "Salvar no pipeline"}
    >
      {status === "loading" && (
        <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin mr-1 align-middle" />
      )}
      {label}
    </button>
  );
}
