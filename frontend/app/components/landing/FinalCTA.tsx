interface FinalCTAProps {
  className?: string;
}

export default function FinalCTA({ className = '' }: FinalCTAProps) {
  return (
    <section
      className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-12 text-center text-white">
        <h2 className="text-3xl sm:text-4xl font-bold mb-4">
          Pronto para economizar tempo e encontrar mais oportunidades?
        </h2>

        <p className="text-lg sm:text-xl mb-8 text-blue-50">
          Comece agora com 3 buscas gratuitas
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <a
            href="/signup"
            className="w-full sm:w-auto bg-white text-blue-600 hover:bg-blue-50 font-bold px-8 py-4 rounded-lg transition-colors text-center text-lg"
          >
            Começar agora - 3 buscas gratuitas
          </a>
        </div>

        <p className="mt-6 text-sm text-blue-100">
          Sem necessidade de cartão de crédito
        </p>
      </div>
    </section>
  );
}
