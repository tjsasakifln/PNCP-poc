import Link from "next/link";

interface SignupSuccessProps {
  email: string;
  isConfirmed: boolean;
  countdown: number;
  isResending: boolean;
  onResend: () => void;
  onChangeEmail: () => void;
}

export function SignupSuccess({
  email,
  isConfirmed,
  countdown,
  isResending,
  onResend,
  onChangeEmail,
}: SignupSuccessProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas">
      <div className="w-full max-w-md p-8 bg-surface-0 rounded-card shadow-lg text-center">
        {/* AC10: Confirmed transition */}
        {isConfirmed ? (
          <>
            <div className="text-4xl mb-4" data-testid="confirmed-icon">&#10003;</div>
            <h2 className="text-xl font-semibold text-green-600 mb-2">
              Email confirmado!
            </h2>
            <p className="text-ink-secondary">Redirecionando...</p>
          </>
        ) : (
          <>
            {/* AC1: Mail icon */}
            <div className="text-4xl mb-4" data-testid="mail-icon">&#9993;</div>

            <h2 className="text-xl font-semibold text-ink mb-2">
              Confirme seu email
            </h2>

            <p className="text-ink-secondary mb-4">
              Enviamos um link de confirmação para:
              <br />
              <strong>{email}</strong>
            </p>

            {/* AC7: Polling indicator */}
            <p className="text-sm text-brand-blue mb-4" data-testid="polling-indicator">
              Aguardando confirmação...
            </p>

            {/* AC1/AC2: Resend button with countdown */}
            <button
              onClick={onResend}
              disabled={countdown > 0 || isResending}
              data-testid="resend-button"
              className="w-full py-3 bg-brand-blue text-white rounded-button
                         font-semibold disabled:bg-gray-300 disabled:text-gray-500
                         disabled:cursor-not-allowed hover:opacity-90 transition-colors"
            >
              {isResending
                ? "Reenviando..."
                : countdown > 0
                  ? `Reenviar em ${countdown}s`
                  : "Reenviar email"}
            </button>

            {/* AC11: Spam helper section */}
            <div className="mt-6 p-4 bg-surface-1 rounded-input text-left">
              <h3 className="font-semibold text-sm mb-2 text-ink">
                Não recebeu o email?
              </h3>
              <ul className="text-sm space-y-1 text-ink-secondary">
                <li>• Verifique sua caixa de spam/lixo eletrônico</li>
                <li>• Aguarde até 5 minutos</li>
                <li>• Confirme se o email está correto</li>
              </ul>
              {/* AC12: Change email link */}
              <button
                onClick={onChangeEmail}
                data-testid="change-email-link"
                className="text-brand-blue text-sm mt-2 underline hover:opacity-80"
              >
                Alterar email
              </button>
            </div>

            <Link
              href="/login"
              className="mt-4 inline-block text-sm text-ink-muted hover:underline"
            >
              Ir para login
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
