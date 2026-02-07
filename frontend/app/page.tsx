import LandingNavbar from './components/landing/LandingNavbar';
import HeroSection from './components/landing/HeroSection';
import OpportunityCost from './components/landing/OpportunityCost';
import BeforeAfter from './components/landing/BeforeAfter';
import DifferentialsGrid from './components/landing/DifferentialsGrid';
import HowItWorks from './components/landing/HowItWorks';
import StatsSection from './components/landing/StatsSection';
import DataSourcesSection from './components/landing/DataSourcesSection';
import SectorsGrid from './components/landing/SectorsGrid';
import FinalCTA from './components/landing/FinalCTA';

export default function LandingPage() {
  return (
    <>
      <LandingNavbar />

      <main>
        <HeroSection />
        <OpportunityCost />
        <BeforeAfter />
        <DifferentialsGrid />
        <HowItWorks />
        <StatsSection />
        <DataSourcesSection />
        <SectorsGrid />
        <FinalCTA />
      </main>

      <footer className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            {/* Sobre */}
            <div>
              <h3 className="font-bold text-lg mb-4">Sobre</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>
                  <a href="#sobre" className="hover:text-blue-400 transition-colors">
                    Quem somos
                  </a>
                </li>
                <li>
                  <a href="#como-funciona" className="hover:text-blue-400 transition-colors">
                    Como funciona
                  </a>
                </li>
              </ul>
            </div>

            {/* Planos */}
            <div>
              <h3 className="font-bold text-lg mb-4">Planos</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>
                  <a href="#planos" className="hover:text-blue-400 transition-colors">
                    Planos e Preços
                  </a>
                </li>
                <li>
                  <a href="/signup" className="hover:text-blue-400 transition-colors">
                    Teste Gratuito
                  </a>
                </li>
              </ul>
            </div>

            {/* Suporte */}
            <div>
              <h3 className="font-bold text-lg mb-4">Suporte</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>
                  <a href="#suporte" className="hover:text-blue-400 transition-colors">
                    Central de Ajuda
                  </a>
                </li>
                <li>
                  <a href="#contato" className="hover:text-blue-400 transition-colors">
                    Contato
                  </a>
                </li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h3 className="font-bold text-lg mb-4">Legal</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>
                  <a href="#privacidade" className="hover:text-blue-400 transition-colors">
                    Política de Privacidade
                  </a>
                </li>
                <li>
                  <a href="#termos" className="hover:text-blue-400 transition-colors">
                    Termos de Uso
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-gray-800 pt-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              {/* Copyright */}
              <p className="text-sm text-gray-400">
                © 2026 SmartLic. Todos os direitos reservados.
              </p>

              {/* LGPD Badge */}
              <div className="flex items-center gap-2">
                <svg
                  className="w-5 h-5 text-green-400"
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
                <span className="text-sm text-gray-400">LGPD Compliant</span>
              </div>

              {/* Desenvolvido por servidores públicos */}
              <p className="text-sm text-gray-400">
                Desenvolvido por servidores públicos
              </p>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
