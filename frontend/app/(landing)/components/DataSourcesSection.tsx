interface DataSourcesSectionProps {
  className?: string;
}

export default function DataSourcesSection({ className = '' }: DataSourcesSectionProps) {
  return (
    <section
      className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      <div className="text-center max-w-3xl mx-auto">
        <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-6">
          Desenvolvido por quem conhece a máquina pública por dentro
        </h2>

        <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">
          Sistema criado por servidores públicos com anos de experiência em processos
          licitatórios. Sabemos quais dados importam e onde encontrá-los.
        </p>

        {/* Fonte Primária: PNCP */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-8 rounded-lg mb-6">
          <div className="flex items-center justify-center gap-3 mb-3">
            <svg
              className="w-8 h-8"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <h3 className="text-2xl font-bold">Fonte Primária Oficial</h3>
          </div>
          <p className="text-xl font-semibold mb-2">PNCP</p>
          <p className="text-blue-100 mb-4">Portal Nacional de Contratações Públicas</p>
          <a
            href="https://pncp.gov.br"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-white text-blue-600 px-6 py-2 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
            aria-label="Acessar PNCP - abre em nova aba"
          >
            Acessar PNCP
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
          </a>
        </div>

        {/* Fontes Complementares */}
        <div className="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg">
          <h4 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
            Fontes Complementares Integradas
          </h4>
          <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-gray-600 dark:text-gray-300">
            <span className="bg-white dark:bg-gray-700 px-4 py-2 rounded-full">BLL</span>
            <span className="bg-white dark:bg-gray-700 px-4 py-2 rounded-full">
              Portal Compras Públicas
            </span>
            <span className="bg-white dark:bg-gray-700 px-4 py-2 rounded-full">BNC</span>
            <span className="bg-white dark:bg-gray-700 px-4 py-2 rounded-full">
              Licitar Digital
            </span>
            <span className="bg-white dark:bg-gray-700 px-4 py-2 rounded-full">
              Fontes estaduais/municipais
            </span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
            Em constante expansão
          </p>
        </div>
      </div>
    </section>
  );
}
