interface OpportunityCostProps {
  className?: string;
}

export default function OpportunityCost({ className = '' }: OpportunityCostProps) {
  return (
    <section
      className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      <div className="bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 p-8 rounded-lg">
        {/* Headline Provocativa */}
        <div className="flex items-start gap-4">
          <svg
            className="w-8 h-8 text-amber-500 flex-shrink-0 mt-1"
            fill="currentColor"
            viewBox="0 0 20 20"
            role="img"
            aria-label="Alerta"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>

          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
              Qual o custo de uma licitação não disputada por não ter sido encontrada?
            </h2>

            {/* 3 Pontos-Chave */}
            <ul className="mt-6 space-y-4 text-lg text-gray-700 dark:text-gray-300">
              <li className="flex items-start gap-3">
                <svg
                  className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>
                  <strong>500 mil oportunidades</strong> publicadas mensalmente no Brasil
                </span>
              </li>
              <li className="flex items-start gap-3">
                <svg
                  className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>
                  A maioria passa <strong>despercebida</strong> por fornecedores qualificados
                </span>
              </li>
              <li className="flex items-start gap-3">
                <svg
                  className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>
                  Cada edital perdido = <strong>concorrente que venceu no seu lugar</strong>
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
