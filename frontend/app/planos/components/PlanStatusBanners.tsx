import Link from "next/link";

type UserStatus = "subscriber" | "privileged" | "trial" | "trial_expired" | "anonymous";

interface PlanStatusBannersProps {
  userStatus: UserStatus;
  trialDaysRemaining: number | null;
  partnerName: string | null;
  statusMsg: string | null;
  portalLoading: boolean;
  onManageSubscription: () => void;
}

export function PlanStatusBanners({
  userStatus,
  trialDaysRemaining,
  partnerName,
  statusMsg,
  portalLoading,
  onManageSubscription,
}: PlanStatusBannersProps) {
  return (
    <>
      {statusMsg && (
        <div className="mb-8 p-4 bg-[var(--success-subtle)] backdrop-blur-sm text-[var(--success)] rounded-card text-center">
          {statusMsg}
        </div>
      )}

      {userStatus === "subscriber" && (
        <div data-testid="status-banner-subscriber" className="mb-8 p-4 bg-emerald-50 dark:bg-emerald-950/50 backdrop-blur-sm border border-emerald-200 dark:border-emerald-800 rounded-card text-center">
          <p className="font-semibold text-emerald-800 dark:text-emerald-200">
            Você possui acesso completo ao SmartLic
          </p>
          <button
            onClick={onManageSubscription}
            disabled={portalLoading}
            className="mt-1 text-sm text-emerald-600 dark:text-emerald-400 hover:underline disabled:opacity-50"
          >
            {portalLoading ? "Abrindo..." : "Gerenciar assinatura"}
          </button>
        </div>
      )}

      {userStatus === "privileged" && (
        <div data-testid="status-banner-privileged" className="mb-8 p-4 bg-emerald-50 dark:bg-emerald-950/50 backdrop-blur-sm border border-emerald-200 dark:border-emerald-800 rounded-card text-center">
          <p className="font-semibold text-emerald-800 dark:text-emerald-200">
            Você possui acesso completo ao SmartLic
          </p>
          <Link href="/buscar" className="mt-1 text-sm text-emerald-600 dark:text-emerald-400 hover:underline">
            Iniciar análise
          </Link>
        </div>
      )}

      {userStatus === "trial" && (
        <div data-testid="status-banner-trial" className="mb-8 p-4 bg-blue-50 dark:bg-blue-950/50 backdrop-blur-sm border border-blue-200 dark:border-blue-800 rounded-card text-center">
          <p className="font-semibold text-blue-800 dark:text-blue-200">
            Você está no período de avaliação{trialDaysRemaining !== null ? ` (${trialDaysRemaining} ${trialDaysRemaining === 1 ? "dia restante" : "dias restantes"})` : ""}
          </p>
          <p className="text-sm text-blue-600 dark:text-blue-400">
            Assine para continuar após o período de avaliação
          </p>
        </div>
      )}

      {userStatus === "trial_expired" && (
        <div data-testid="status-banner-expired" className="mb-8 p-4 bg-amber-50 dark:bg-amber-950/50 backdrop-blur-sm border border-amber-200 dark:border-amber-800 rounded-card text-center">
          <p className="font-semibold text-amber-800 dark:text-amber-200">
            Seu período de avaliação encerrou
          </p>
          <p className="text-sm text-amber-600 dark:text-amber-400">
            Assine para voltar a ter acesso
          </p>
        </div>
      )}

      {partnerName && (
        <div data-testid="partner-discount-banner" className="mb-8 p-4 bg-emerald-50 dark:bg-emerald-950/50 backdrop-blur-sm border border-emerald-200 dark:border-emerald-800 rounded-card text-center">
          <p className="font-semibold text-emerald-800 dark:text-emerald-200">
            Indicado por <strong>{partnerName}</strong> — 25% de desconto aplicado no checkout
          </p>
          <p className="text-sm text-emerald-600 dark:text-emerald-400">
            O cupom exclusivo será aplicado automaticamente ao finalizar
          </p>
        </div>
      )}
    </>
  );
}
