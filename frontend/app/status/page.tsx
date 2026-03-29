import { Metadata } from "next";
import StatusContent from "./components/StatusContent";

/**
 * STORY-316 AC11-AC15: Public status page.
 *
 * Server Component shell: renders the static page header.
 * Dynamic status data (sources, components, uptime, incidents) is
 * fetched and rendered client-side via StatusContent ("use client").
 */
export const metadata: Metadata = {
  title: { absolute: "Status do Sistema | SmartLic" },
  description: "Acompanhe o status em tempo real dos sistemas e fontes de dados do SmartLic.",
};

export default function StatusPage() {
  return (
    <div className="min-h-screen bg-surface-0">
      {/* Static header — rendered on server */}
      <header className="border-b border-border bg-surface-1">
        <div className="max-w-3xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <a href="/" className="text-brand-blue font-bold text-lg hover:opacity-80 transition-opacity">
                SmartLic
              </a>
              <h1 className="text-2xl font-bold text-ink mt-1">Status do Sistema</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Dynamic status content — fetches live data, auto-refreshes */}
      <main className="max-w-3xl mx-auto px-4 py-8">
        <StatusContent />
      </main>
    </div>
  );
}
