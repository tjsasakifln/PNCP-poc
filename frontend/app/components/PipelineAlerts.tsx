"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePipeline } from "../../hooks/usePipeline";
import { useAuth } from "./AuthProvider";

export function PipelineAlerts() {
  const { session } = useAuth();
  const { alerts, fetchAlerts } = usePipeline();

  useEffect(() => {
    if (session?.access_token) {
      fetchAlerts();
    }
  }, [session?.access_token, fetchAlerts]);

  if (!alerts || alerts.length === 0) return null;

  return (
    <Link
      href="/pipeline"
      className="flex items-center gap-1.5 text-xs font-medium text-orange-600 dark:text-orange-400 hover:text-orange-700 dark:hover:text-orange-300 transition-colors"
      title={`${alerts.length} licitação(ões) com prazo próximo`}
    >
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500" />
      </span>
      <span>{alerts.length}</span>
    </Link>
  );
}
