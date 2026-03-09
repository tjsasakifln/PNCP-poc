"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * DEBT-011 FE-001: /conta redirects to /conta/perfil.
 * All content has been decomposed into sub-routes.
 */
export default function ContaPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/conta/perfil");
  }, [router]);

  return (
    <div className="flex items-center justify-center py-12">
      <p className="text-[var(--ink-secondary)]">Carregando...</p>
    </div>
  );
}
