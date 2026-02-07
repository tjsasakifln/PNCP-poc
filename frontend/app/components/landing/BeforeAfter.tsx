interface BeforeAfterProps {
  className?: string;
}

export default function BeforeAfter({ className = '' }: BeforeAfterProps) {
  return (
    <section
      className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      <h2 className="text-3xl sm:text-4xl font-bold text-center text-gray-900 dark:text-white mb-12">
        Transforme sua busca por licitações
      </h2>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Sem SmartLic */}
        <div className="bg-gray-100 dark:bg-gray-800 p-8 rounded-lg">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
              <svg
                className="w-6 h-6 text-red-600 dark:text-red-400"
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">Sem SmartLic</h3>
          </div>

          <ul className="space-y-4 text-gray-700 dark:text-gray-300">
            <li className="flex items-start gap-3">
              <span className="text-red-600 dark:text-red-400 text-xl">❌</span>
              <span>
                <strong>8 horas/dia</strong> buscando manualmente em 27 portais diferentes
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-red-600 dark:text-red-400 text-xl">❌</span>
              <span>
                Editais importantes <strong>perdidos</strong> por sobrecarga de informação
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-red-600 dark:text-red-400 text-xl">❌</span>
              <span>
                Busca <strong>fragmentada</strong>, sem histórico unificado
              </span>
            </li>
          </ul>
        </div>

        {/* Com SmartLic */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 p-8 rounded-lg border-2 border-blue-200 dark:border-blue-700">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center">
              <svg
                className="w-6 h-6 text-blue-600 dark:text-blue-400"
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
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">Com SmartLic</h3>
          </div>

          <ul className="space-y-4 text-gray-700 dark:text-gray-300">
            <li className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400 text-xl">✓</span>
              <span>
                <strong>15 minutos/dia</strong> com buscas automáticas e filtros inteligentes
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400 text-xl">✓</span>
              <span>
                <strong>Alertas em tempo real</strong> para oportunidades relevantes
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400 text-xl">✓</span>
              <span>
                Busca <strong>unificada</strong> em múltiplas fontes com histórico completo
              </span>
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
