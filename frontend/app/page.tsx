// Landing Page Institucional - STORY-168 + STORY-173
// Route: / (root)
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
import ProofOfValue from './components/landing/ProofOfValue';
import ValuePropSection from './components/ValuePropSection';
import ComparisonTable from './components/ComparisonTable';
import AnalysisExamplesCarousel from './components/landing/AnalysisExamplesCarousel';
import TrustCriteria from './components/landing/TrustCriteria';
import Footer from './components/Footer';

export default function LandingPage() {
  return (
    <>
      <LandingNavbar />

      <main id="main-content">
        <HeroSection />
        <ProofOfValue />
        <ValuePropSection />
        <OpportunityCost />
        <BeforeAfter />
        <ComparisonTable />
        <DifferentialsGrid />
        <HowItWorks />
        <StatsSection />
        <section id="sobre">
          <DataSourcesSection />
        </section>
        <SectorsGrid />
        <AnalysisExamplesCarousel />
        <TrustCriteria />

        {/* GTM-COPY-005 AC6: Credibility badge */}
        <div className="text-center py-6 bg-surface-1 border-y border-[var(--border)]">
          <p className="text-sm text-ink-secondary">
            Desenvolvido pela <strong className="text-ink">CONFENGE Avaliações e Inteligência Artificial</strong>{' '}
            <span className="mx-1">·</span>{' '}
            <a href="/sobre" className="text-brand-blue hover:underline">Conheça nossa metodologia</a>
          </p>
        </div>

        <section id="suporte">
          <FinalCTA />
        </section>
      </main>

      <Footer />
    </>
  );
}
