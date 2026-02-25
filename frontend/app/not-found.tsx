import Link from "next/link";

/**
 * SLA-001: Custom 404 page prevents Railway's "train has not arrived at the station"
 * from showing for app-level 404s (invalid routes within the frontend).
 *
 * Railway's 404 only appears when the entire service is unreachable.
 * This page handles the case where the service is up but the route doesn't exist.
 */
export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--surface-0)] px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-6">
          <span className="text-6xl font-bold text-[var(--brand-navy)]">404</span>
        </div>

        <h1 className="text-2xl font-bold text-[var(--ink)] mb-2">
          Página não encontrada
        </h1>

        <p className="text-[var(--ink-secondary)] mb-8">
          A página que você procura não existe ou foi movida.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="inline-flex items-center justify-center bg-[var(--brand-navy)] hover:bg-[var(--brand-blue)] text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200"
          >
            Voltar ao início
          </Link>
          <Link
            href="/buscar"
            className="inline-flex items-center justify-center border border-[var(--border)] text-[var(--ink)] font-medium py-3 px-6 rounded-lg transition-colors duration-200 hover:bg-[var(--surface-1)]"
          >
            Ir para busca
          </Link>
        </div>
      </div>
    </div>
  );
}
