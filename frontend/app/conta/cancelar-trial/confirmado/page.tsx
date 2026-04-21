/**
 * /conta/cancelar-trial/confirmado — success page shown after a one-click
 * trial cancellation succeeds (STORY-CONV-003c AC7).
 */
import Link from "next/link";

export const metadata = {
  title: "Trial cancelada — SmartLic",
  // Prevent indexing — this page is only valid via redirect.
  robots: { index: false, follow: false },
};

export default function CancelTrialConfirmadoPage() {
  return (
    <main className="p-6 max-w-md mx-auto" data-testid="cancel-trial-confirmado">
      <h1 className="text-2xl font-semibold text-ink mb-3">Trial cancelada ✓</h1>
      <p className="text-sm text-ink-secondary mb-4">
        Nenhuma cobrança será feita. Você mantém acesso até o fim do período
        de trial. Nenhum dado da sua conta foi apagado.
      </p>
      <p className="text-sm text-ink-secondary mb-4">
        Se mudou de ideia, basta reativar a assinatura a partir da sua conta
        — mantemos seus dados por 30 dias.
      </p>
      <div className="flex flex-col gap-2">
        <Link
          href="/buscar"
          className="py-2 px-4 text-center bg-brand-blue text-white rounded-input"
        >
          Continuar usando SmartLic
        </Link>
        <Link
          href="/conta"
          className="py-2 px-4 text-center border border-ink-secondary rounded-input text-ink"
        >
          Minha conta
        </Link>
        <Link
          href="/ajuda"
          className="py-2 px-4 text-center text-ink-secondary text-sm"
        >
          Precisa de ajuda?
        </Link>
      </div>
    </main>
  );
}
